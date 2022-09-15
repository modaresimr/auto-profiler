
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections
import functools
import re
import sys
from . import utils
import six

from .timer import Timer
from .tree import Tree
import os
workingdir = os.getcwd()


def default_show(p):
    print('Time   [Hits * PerHit] Function name [Called from] [Function Location]\n' +
          '-----------------------------------------------------------------------')
    print(Tree(p.root, threshold=0.5))


class OrderedDefaultDictInt(collections.OrderedDict):
    def __missing__(self, key):
        self[key] = value = 0
        return value


class _FrameNameCounter(object):
    """The counter class that counts a given function name in a given frame,
    and returns an unique name for each function, in case that it has the
    same name as other functions in the same frame.
    """

    _ctx_counts_name = '_NameCounter_counts'

    def __init__(self, context):
        self._counts = getattr(context, self._ctx_counts_name, None)
        if self._counts is None:
            self._counts = OrderedDefaultDictInt()
            setattr(context, self._ctx_counts_name, self._counts)

    @staticmethod
    def raw_name(frame, name):
        return '%s%s' % (frame, name)

    def incr(self, frame, name):
        self._counts[(frame, name)] += 1

    def unique_name(self, ctx, frame, name):
        """Return an unique name for function `name` in frame `frame`."""

        count = self._counts[(frame, name)]
        unique_name = self.raw_name(frame, name)
        if count > 1:
            unique_name += str(count - 1)
        return unique_name+str(ctx)

    def unique_name2(self, ctx, frame, name, depth):
        """Return an unique name for function `name` in frame `frame`."""
        fcode = frame.f_code
        unique_name = ('%s [%s:%s]\n') % (fcode.co_filename, fcode.co_firstlineno, fcode.co_name)
        # count = self._counts[(frame, name)]
        if depth >= 0 and frame.f_back:
            fcode = frame.f_back.f_code
            # parent_name =('%s [%s:%s]\n')% (fcode.co_filename, fcode.co_firstlineno, fcode.co_name)
            unique_name += self.unique_name2(ctx, frame.f_back, None, depth-1)

        return unique_name+str(ctx)

    @property
    def first_frame(self):
        """Return the first frame attached to the context."""
        default = (None, None)
        return next(iter(six.iterkeys(self._counts)), default)[0]


class Profiler(object):
    GlobalDisable = False
    """The profiler class that automatically injects a timer for each
    function to measure its execution time.
    """

    CALL_EVENTS = ('call', 'c_call')
    RETURN_EVENTS = ('return', 'exception', 'c_return', 'c_exception')

    def enable(self):
        if (len(Profiler._stack) > 0):
            print(RuntimeError('profiler is already running '))
            return False

        if (len(self._parents) > 0):
            print(RuntimeError('profiler enabling but not disabled called '))
            return False
        Timer._timer_map.get_map(Timer._default_ctx).clear()
        self._parents=[Timer('program',ui=self.ui)]

        self._parents[-1].start()
        Profiler._stack.append('i')

        # It's necessary to delay calling `timer_class.get_context()` here
        # if this profiler is used as a decorator.
        ctx = self._timer_class.get_context()
        ctxstr = str(self._timer_class.get_context())

        # Attach the context local variables.
        self._ctx_local_vars['call_stack_depths'][ctxstr] = -1
        self._ctx_local_vars['frame_depths'][ctxstr] = []
        self._ctx_local_vars['counters'][ctxstr] = _FrameNameCounter(ctx)

        sys.setprofile(self._profile)
        return self

    def disable(self):
        Profiler._stack.pop()
        if (len(self._stack) > 0):
            print('Error')

        sys.setprofile(None)

        # It's necessary to delay calling `timer_class.get_context()` here
        # if this profiler is used as a decorator.
        ctx = str(self._timer_class.get_context())

        # Detach the context local variables.
        self._ctx_local_vars['call_stack_depths'].pop(ctx)
        self._ctx_local_vars['frame_depths'].pop(ctx)
        self._ctx_local_vars['counters'].pop(ctx)

        
        for p in self._parents:
            if not ('__exit__' in p.name or 'disable' in p.name or 'program' in p.name):
                print('error exited not successfully',p.name)
            p.stop()
        self._parents.clear()
        
        # If a callback function is given, call it after this profiler is disabled.
        if self._on_disable_callback is not None:
            self._on_disable_callback(self)

        return self

    def __init__(self, timer_class=Timer, depth=4, on_disable=default_show, filterExternalLibraries=True, eliminateWorkspacePath=True, eliminateExternalLibrariesPath=True,ui=utils.in_notebook()):
        self._timer_class = timer_class
        self._depth = depth
        self._parents=[]
        if ui and on_disable==default_show:
            on_disable=None
        self.ui=ui
        self._on_disable_callback = on_disable
        self._filterExternalLibraries = filterExternalLibraries
        self._eliminateWorkspacePath = eliminateWorkspacePath
        self._eliminateExternalLibrariesPath = eliminateExternalLibrariesPath
        self._ctx_local_vars = dict(
            # Mapping: context -> call_stack_depth [PER CONTEXT]
            #                     (The depth of the call stack).
            call_stack_depths={},
            # Mapping: context -> frame_depth [PER CONTEXT]
            #                     (Mapping: frame -> depth [PER FRAME],
            #                                        relative to the first frame).
            frame_depths={},

            # Mapping: context -> counter [PER CONTEXT]
            #                     (The helper to make unique function name).
            counters={},
        )

        # The excluded function is mainly due to the side effect of
        # enabling or disabling the profiler.
        current_filename = re.sub('(\.pyc)$', '.py', __file__)
        self._excluded_func_names = (
            '<sys.setprofile>',
            'enable auto_profiler',
            'disable auto_profiler',
            '__exit__',
            '__enter__ auto_profiler',
            
            # the following line number need to be updated if the
            # actual line number of the method `enable()` is changed.
            # self._format_func_name(current_filename, 89, 'enable'),
            # the following line number need to be updated if the
            # actual line number of the method `disable()` is changed.
            # self._format_func_name(current_filename, 109, 'disable'),
        )

    def _format_func_name(self, filename, firstlineno, name):
        return '{2}  [{0}:{1}]'.format(self._filterPath(filename), firstlineno, name)

    def _filterPath(self, path):
        if ('auto_profiler\\profiler' in path or 'auto_profiler/profiler' in path):
            return ' '
        if (self._eliminateWorkspacePath and path.startswith(workingdir)):
            return path[len(workingdir)+1:]
        if (self._eliminateWorkspacePath and 'site-packages/' in path):
            return path.split('site-packages/')[1]
        if (self._eliminateWorkspacePath and 'python/' in path):
            return path.split('python/')[1]
        return ' '

    def _get_func_name(self, frame):
        fcode = frame.f_code
        fback = frame.f_back
        if (fback):
            fn = (fback.f_code.co_filename, fback.f_lineno, fcode.co_name)
            fn2 = (fcode.co_filename, frame.f_lineno, '')
            return self._format_func_name(*fn)+self._format_func_name(*fn2)
        else:
            fn = (fcode.co_filename, frame.f_lineno, fcode.co_name)
            return self._format_func_name(*fn)

    _stack = []

    @property
    def root(self):
        """Return the root timer of the implicit entire timer tree."""
        return self._timer_class.root

    def _profile(self, frame, event, arg):
        """The core handler used as the system’s profile function."""
        # help(frame)
        # print('xxxxxxx', frame.__repr__())
        ctx = str(self._timer_class.get_context())

        # Judge if the given event happened on a C function.
        # i.e. ('c_call', 'c_return', 'c_exception')
        is_c = event.startswith('c_')

        if is_c:  # C function
            if arg.__module__:
                func_name = '`%s.%s`' % (arg.__module__, arg.__name__)
            else:
                func_name = '`%s`' % (arg.__name__)
            parent_frame = frame
        else:  # Python function
            func_name = self._get_func_name(frame)
            parent_frame = frame.f_back

        # Ignore the excluded functions.
        for f in self._excluded_func_names:
            # print('aaaa ', f in func_name, ' aaaa', f, 'b', func_name)
            if all([ff in func_name for ff in f.split(' ')]):
                return
        # if func_name in self._excluded_func_names:
        #     return
        # if 'site-packages' in self._get_func_name(parent_frame):
        #     return
        # if 'python' in func_name and 'python' in self._get_func_name(parent_frame):
        #     return

        # if 'builtins'in func_name and 'python' in self._get_func_name(parent_frame):
        #     return
        # print('not ignoreing',func_name,self._get_func_name(parent_frame))

        if self._filterExternalLibraries and not frame.f_code.co_filename.startswith(workingdir):
            if not (parent_frame):
                return
            coname=parent_frame.f_code.co_filename
            if not coname.startswith(workingdir) and not coname.startswith('<ipython-input') :
                return

        current_depth = 0

        frame_name = ('c_' if is_c else '') + frame.__repr__()
        # print('frame', frame_name, 'event', event, 'args', arg)
        if event in Profiler.CALL_EVENTS:
            # Increment the depth of the call stack.
            self._ctx_local_vars['call_stack_depths'][ctx] += 1

            d = self._ctx_local_vars['call_stack_depths'][ctx]
            # print('call ctx', frame_name)
            # print('call fram_depth', self._ctx_local_vars['frame_depths'])
            # current_depth = self._ctx_local_vars['frame_depths'][ctx][frame_name] = d
            self._ctx_local_vars['frame_depths'][ctx].append(d)
            current_depth = d
        elif event in Profiler.RETURN_EVENTS:
            # print('return ctx', frame_name)
            # Decrement the depth of the call stack.
            # if frame_name in self._ctx_local_vars['frame_depths'][ctx]:
            if len(self._ctx_local_vars['frame_depths'][ctx]) == 0:
                return
            self._ctx_local_vars['call_stack_depths'][ctx] -= 1
            current_depth = self._ctx_local_vars['frame_depths'][ctx].pop()
            # current_depth = self._ctx_local_vars['frame_depths'][ctx].pop(frame_name)

        # Ignore the frame if its depth exceeds the specified depth.
        if self._depth is not None and current_depth > self._depth:
            return

        ctx_local_counter = self._ctx_local_vars['counters'][ctx]
        if event in Profiler.CALL_EVENTS:
            ctx_local_counter.incr(frame, func_name)

            unique_func_name = ctx_local_counter.unique_name(ctx, frame, func_name)
            unique_func_name = ctx_local_counter.unique_name2(ctx, frame, func_name, current_depth)
            # print('call u', unique_func_name)
            if frame is ctx_local_counter.first_frame:
                unique_parent_name = None
            else:
                parent_name = self._get_func_name(parent_frame)
                unique_parent_name = ctx_local_counter.unique_name2(ctx,
                                                                    parent_frame, parent_name, current_depth-1)
            # print('call parent', unique_parent_name)
            # Create and start a timer for the entering function
            # timer = self._timer_class.timers.get(unique_func_name)
            # if timer is None:
            #     timer = self._timer_class(
            #         unique_func_name,
            #         parent_name=unique_parent_name,
            #         display_name=func_name,
            #         on_stop=None,
            #         ui=self.ui
            #     )
            parent_name=self._parents[-1].name
            current_name=unique_func_name+parent_name 
            
            timer = self._timer_class.timers.get(current_name)
            
            if timer is None:
                timer = self._timer_class(
                    current_name,
                    parent_name=parent_name, 
                    display_name=func_name,
                    on_stop=None,
                    ui=self.ui
                )
            
            # timer = Timer.instance(unique_func_name,ui=self.ui,display_name=func_name,on_stop=None)
            self._parents.append(timer)
            timer.start()
        elif event in Profiler.RETURN_EVENTS:
            unique_func_name = ctx_local_counter.unique_name2(ctx, frame, func_name, current_depth)
            # timer = self._timer_class.timers.get(unique_func_name)
            timer = self._parents.pop()
            timer.stop()
            # print('return ', unique_func_name)
            # if timer is not None:
            #     # Stop the timer for the exiting function
            #     timer.stop()

    def __call__(self, func):
        """Make the profiler object to be a decorator."""
        @functools.wraps(func)
        def decorator(*args, **kwargs):
            if (Profiler.GlobalDisable):
                return func(*args, **kwargs)

            with self:
                return func(*args, **kwargs)
            
        return decorator

    def __enter__(self):
        self.enable()

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        self.disable()