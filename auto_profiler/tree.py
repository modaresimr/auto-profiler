# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from operator import itemgetter

import six
from tree_format import format_tree
import os
workingdir = os.getcwd()


@six.python_2_unicode_compatible
class Tree(object):
    """The class that represents the given timer and its children
    timers as a tree.
    """

    def __init__(self, timer, span_unit='auto', span_fmt='%.3f', threshold=0.5):
        self._timer = timer
        self._span_unit = span_unit
        self._span_fmt = span_fmt
        self._threshold = threshold

    def format_span(self, tim):
        """Return the elapsed time as a fraction.

        unit:
            's'  -- in seconds (the default value)
            'ms' -- in milliseconds
            'us' -- in microseconds
        """
        multipliers = dict(m=1/60, s=1, ms=1000, us=1000000)
        unit = self._span_unit
        if unit == 'auto':
            for m in multipliers:
                if 1/multipliers[m] < tim:
                    unit = m
                    break
        assert unit in multipliers, '`unit` must be one of %s' % multipliers.keys()
        timstr = (self._span_fmt % (tim*multipliers[unit])).rstrip('0').rstrip('.')
        return f'{timstr}{unit}'

    @property
    def nodes(self):
        tim = self._timer.span()
        span = self.format_span(tim)
        per_call = self.format_span(tim/self._timer._num_start_call)
        node = '%s [%d * %s]  %s' % (span, self._timer._num_start_call, per_call, self._timer.display_name)
        # node = '%s%s [%d]  %s\n%s\nparents=%s' % (span, self._span_unit, self._timer._num_start_call, self._timer.display_name,self._timer._name,self._timer._parent_name)
        children = []
        for child in self._timer.children:
            if (child.span() < self._threshold):
                # print('ignore short functions:',child.display_name)
                continue
            children.append(Tree(child, self._span_unit, self._span_fmt).nodes)
        # children = [Tree(child, self._span_unit, self._span_fmt).nodes
        #             for child in self._timer.children]
        return node, children

    def __str__(self):
        return format_tree(
            self.nodes, format_node=itemgetter(0), get_children=itemgetter(1)
        )
