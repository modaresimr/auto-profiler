import time
import threading

class TreeUI:

    def __init__(self,timer):
        from ipytree import Tree, Node
        self.tree = Tree(stripes=True)
        self.root_node=Node('root')
        self.tree.add_node(self.root_node)
        import IPython
        IPython.display.display('Time   [Hits * PerHit] Function name [Called from] [Function Location]' )
        IPython.display.display(self.tree)
        self.node_map={}
        self._threshold=.1
        self.root_timer=timer


    def _priodic_update(self):
        while self.do_update:
            self.update()
            time.sleep(1)
    
    def start_priodic_update(self):
        self.do_update=True
        threading.Thread(target=self._priodic_update).start()
    
    def stop_update(self):
        self.do_update=False
        self.update()

    

    
    def update(self):
        self.update_subtree(self.root_timer,self.root_node)
        

    
    def update_subtree(self,ctimer,ctree):
        import numpy as np
        from ipytree import Tree, Node

        ctree.name=self.get_timer_text(ctimer)

        if not (ctimer.children):
            ctree.icon='file'
            return
        ctree.icon='folder'
        
        
        
        childs=list(ctimer.children)
        times=[child.span(realtime=True) for child in childs]
        args=np.argsort(times)

        for i,child in enumerate(childs):
            if (times[i] < self._threshold):
                # print('ignore short functions:',child.display_name)
                continue
            childnode=self.node_map.get(child.name,None)
            if childnode==None:
                self.node_map[child.name]=childnode=Node(child.name)
                ctree.add_node(childnode)
                childnode.lastStateOpen=True
            childnode.close_icon_style=childnode.open_icon_style='default'
            self.update_subtree(child,childnode)
            if args[i]>=(len(times)-1)*2/3:
                childnode.icon_style='danger'
                if not childnode.lastStateOpen:
                    childnode.lastStateOpen=childnode.opened=True
                    
            elif args[i]>=(len(times)-1)/3:
                childnode.icon_style='warning'
                if childnode.lastStateOpen:
                    childnode.lastStateOpen=childnode.opened=False

            else:
                childnode.icon_style='success'
                if childnode.lastStateOpen:
                    childnode.lastStateOpen=childnode.opened=False



            childnode.close_icon_style=childnode.open_icon_style=childnode.icon_style
            
        

    
    def get_timer_text(self,timer):
        tim = timer.span(realtime=True)
        span = self.format_span(tim)
        per_call = self.format_span(tim/timer._num_start_call)
        node = '%s [%d * %s] &nbsp %s' % (span, timer._num_start_call, per_call, timer.display_name)
        return node


    def format_span(self, tim):
        """Return the elapsed time as a fraction.

        unit:
            's'  -- in seconds (the default value)
            'ms' -- in milliseconds
            'us' -- in microseconds
        """
        multipliers = dict(m=1/60, s=1, ms=1000, us=1000000)
        unit = 'auto'
        if unit == 'auto':
            unit='ms'
            for m in multipliers:
                if 1/multipliers[m] < tim:
                    unit = m
                    break
        
        assert unit in multipliers, '`unit` must be one of %s' % multipliers.keys()
        timstr = ('%.3f' % (tim*multipliers[unit])).rstrip('0').rstrip('.')
        return f'{timstr}{unit}'
      
