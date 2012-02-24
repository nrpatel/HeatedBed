#!/usr/bin/env python

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

class HilbertCurveGenerator(object):
    def __init__(self):
        pass
        
    def length(self, order):
        sq = 2**order
        return sq-(1.0/sq)
    
class PCBGenerator(object):
    # size is in inches, currently treats all boards as squares
    def __init__(self, volts, watts, size):
        self.trace = HeatedTraceCalculator(volts, watts)
        self.hilbert = HilbertCurveGenerator()
        self.size = size
        self.pcb_width = min(size[0], size[1])
        self.spacing = 10 # mils the traces need to be apart (limited by the manufacturing process)
        
    def electrical_description(self):
        return "%.2fV %.2fW %.2fA %.2fohms" % (self.trace.volts, self.trace.watts, self.trace.amps, self.trace.ohms)
        
    def length(self):
        min_width = self.trace.min_width()
        min_order = 0
        min_length = 0
        max_order = 0
        max_length = 0
        order = 1
        while 1:
            trace_len = 1000.0*self.pcb_width*self.hilbert.length(order)
            temp_width = self.trace.width_for_length(trace_len)
                
            # save the first width that is above the minimum required
            if temp_width > min_width and min_order == 0:
                min_length = trace_len
                min_order = order
                
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
