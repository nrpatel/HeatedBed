#!/usr/bin/env python

# from http://github.com/cortesi/scurve
from scurve.hilbert import Hilbert

def mm(mils):
    return mils*0.0254

def mils(mm):
    return mm*39.3700787

class HeatedTraceCalculator(object):
    # for simplicity, sizes are in mils, temperature is in C, current is Amps
    def __init__(self, volts, watts):
        self.volts = float(volts)
        self.watts = float(watts)
        self.amps = self.watts/self.volts
        self.ohms = self.volts/self.amps
        self.rise = 100
        self.thickness = 1.378 # 1 oz Cu in mils
        self.resistivity = 1.7*(10**-6)*393.700787 # of Cu in ohm mils

    def min_width(self):
        # from IPC 2221
        return ((self.amps/(0.048*(self.rise**0.44)))**(1.0/0.725))/self.thickness
    
    def width_for_length(self, length):
        # note that these formulas are not quite correct as they ignore temperature
        return self.resistivity*length/(self.ohms*self.thickness)
        
    def length_for_width(self, width):
        return self.ohms*self.thickness*width/self.resistivity
    
class HilbertTrace(Hilbert, object):
    def __init__(self, width, order):
        Hilbert.__init__(self, 2, order)
        self.width = width*1000.0
        
    def euclidean(self):
        """
        Euclidean length of the curve in mils
        """
        sq = 2**self.order
        return (sq-(1.0/sq))*self.width
        
    def __getitem__(self, idx):
        if idx >= len(self):
            raise IndexError
        return self.point(idx)
        
    def point(self, idx):
        """
        Location of the point on the curve in mils
        """
        point = super(HilbertTrace, self).point(idx)
        dim = self.dimensions()
        offset = 1.0/(2.0*float(dim[0]))
        x = int((float(point[0])/float(dim[0])+offset)*self.width)
        y = int((float(point[1])/float(dim[1])+offset)*self.width)
        return [x, y]
        
    def segment(self, idx):
        if idx >= len(self)-1:
            raise IndexError
        return [self.point(idx), self.point(idx+1)]
    
class PCBGenerator(object):
    # size is in inches, currently treats all boards as squares
    def __init__(self, volts, watts, size):
        self.trace = HeatedTraceCalculator(volts, watts)
        self.size = size
        self.pcb_width = min(size[0], size[1])
        self.spacing = 10 # mils the traces need to be apart (limited by the manufacturing process)
        
    def electrical_description(self):
        return "%.2fV %.2fW %.2fA %.2fohms" % (self.trace.volts, self.trace.watts, self.trace.amps, self.trace.ohms)
        
    def blah(self, order):
        h = HilbertTrace(self.pcb_width, order)
        count = len(h)
        for i in range(0, count-1):
            print h.segment(i)
        
    def length(self):
        min_width = self.trace.min_width()
        min_order = 0
        min_length = 0
        max_order = 0
        max_length = 0
        order = 1
        while 1:
            h = HilbertTrace(self.pcb_width, order)
            trace_len = h.euclidean()
            temp_width = self.trace.width_for_length(trace_len)
                
            # save the first width that is above the minimum required
            if temp_width > min_width and min_order == 0:
                min_length = trace_len
                min_order = order
                
            # stop if there is no longer space on the board for the traces
            if (order*2*temp_width+(order*2+1)*self.spacing)/1000.0 > self.pcb_width:
                break
                
            max_length = trace_len
            max_order = order
            order += 1

        return ((min_order, min_length, self.trace.width_for_length(min_length)),
                (max_order, max_length, self.trace.width_for_length(max_length)))

if __name__ == '__main__':
    generator = PCBGenerator(12, 100, (5, 5))
    print generator.electrical_description()
    print generator.length()
