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
        # KiCad uses 0.0001 inch unit measurements internally
        self.width = width*10000.0
        
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

   
class PCBWriter(object):
    def __init__(self, filename, size, width, segments):
        """
        Units for size are inches and width are mils.
        """
        self.filename = filename
        self.segments = segments
        self.size = [int(size[0]*10000.0), int(size[1]*10000.0)]
        self.width = width
        self.offset = 10000
        print self.header()
        print self.edge([self.offset, self.offset], [self.offset+self.size[0], self.offset])
        print self.edge([self.offset, self.offset], [self.offset, self.offset+self.size[1]])
        print self.edge([self.offset+self.size[0], self.offset], [self.offset+self.size[0], self.offset+self.size[1]])
        print self.edge([self.offset, self.offset+self.size[1]], [self.offset+self.size[0], self.offset+self.size[1]])
        print "$TRACK"
        for seg in self.segments:
            print self.trace([seg[0][0]+self.offset, seg[0][1]+self.offset],\
                       [seg[1][0]+self.offset, seg[1][1]+self.offset],\
                       self.width)
        print "$EndTRACK"
        print self.footer()
        
    def header(self):
        return """PCBNEW-BOARD Version 1 date

# Hacked together using nrp's Hilbert curve PCB generator

$GENERAL
encoding utf-8
LayerCount 2
Ly 1FFF8001
EnabledLayers 1FFF8001
Links 0
NoConn 0
Di %(xi)s %(yi)s %(xr)s %(yb)s
Ndraw 4
Ntrack %(track)s
Nzone 0
BoardThickness 630
Nmodule 0
Nnets 1
$EndGENERAL

$SHEETDESCR
Sheet A3 16535 11700
Title ""
Date "24 feb 2012"
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndSHEETDESCR

$SETUP
InternalUnit 0.000100 INCH
Layers 2
Layer[0] Back signal
Layer[15] Front signal
TrackWidth 100
TrackClearence 100
ZoneClearence 200
TrackMinWidth 100
DrawSegmWidth 150
EdgeSegmWidth 150
ViaSize 350
ViaDrill 250
ViaMinSize 350
ViaMinDrill 200
MicroViaSize 200
MicroViaDrill 50
MicroViasAllowed 0
MicroViaMinSize 200
MicroViaMinDrill 50
TextPcbWidth 120
TextPcbSize 600 800
EdgeModWidth 150
TextModSize 600 600
TextModWidth 120
PadSize 600 600
PadDrill 320
Pad2MaskClearance 100
AuxiliaryAxisOrg 0 0
PcbPlotParams (pcbplotparams (layerselection 3178497) (usegerberextensions true) (excludeedgelayer true) (linewidth 60) (plotframeref false) (viasonmask false) (mode 1) (useauxorigin false) (hpglpennumber 1) (hpglpenspeed 20) (hpglpendiameter 15) (hpglpenoverlay 2) (pscolor true) (psnegative false) (psa4output false) (plotreference true) (plotvalue true) (plotothertext true) (plotinvisibletext false) (padsonsilk false) (subtractmaskfromsilk false) (outputformat 1) (mirror false) (drillshape 1) (scaleselection 1) (outputdirectory ""))
$EndSETUP

$EQUIPOT
Na 0 ""
St ~
$EndEQUIPOT
$NCLASS
Name "Default"
Desc "This is the default net class."
Clearance 100
TrackWidth 100
ViaDia 350
ViaDrill 250
uViaDia 200
uViaDrill 50
AddNet ""
$EndNCLASS""" % {"xi" : self.offset-101, "yi" : self.offset-101,\
                 "xr" : self.offset+self.size[0]+101, "yb" : self.offset+self.size[1]+101,\
                 "track" : len(self.segments)}
            
    def footer(self):
        return """$ZONE
$EndZONE
$EndBOARD"""

    def edge(self, start, end):
        return """$EndDRAWSEGMENT
$DRAWSEGMENT
Po 0 %(xi)s %(yi)s %(xr)s %(yb)s 100
De 28 0 900 0 0
$EndDRAWSEGMENT""" % {"xi" : start[0], "yi" : start[1], "xr" : end[0], "yb" : end[1]}

    def trace(self, start, end, width):
        return """Po 0 %(xi)s %(yi)s %(xr)s %(yb)s %(w)s -1
De 15 0 0 0 0""" % {"xi" : start[0], "yi" : start[1], "xr" : end[0], "yb" : end[1], "w" : width}


class PCBGenerator(object):
    # size is in inches, currently treats all boards as squares
    def __init__(self, volts, watts, size):
        self.trace = HeatedTraceCalculator(volts, watts)
        self.size = size
        self.pcb_width = min(size[0], size[1])
        self.spacing = 10 # mils the traces need to be apart (limited by the manufacturing process)
        self.min_order = ()
        self.max_order = ()
        self.generate_orders()
        
    def electrical_description(self):
        return "%.2fV %.2fW %.2fA %.2fohms" % (self.trace.volts, self.trace.watts, self.trace.amps, self.trace.ohms)
        
    def generate_trace(self, order):
        h = HilbertTrace(self.pcb_width, order)
        count = len(h)
        ret = []
        for i in range(0, count-1):
            ret.append(h.segment(i))
        return ret
        
    def generate_min_trace(self):
        """
        Generates the minimum length trace meeting the wattage criteria.
        """
        return self.generate_trace(self.min_order[0]+1)
        
    def generate_max_trace(self):
        """
        Generates the maximum length trace that will fit on the board.
        """
        return self.generate_trace(self.max_order[0]+1)
        
    def generate_orders(self):
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
                
            #print "%d %f %f %f %f"  % (order, temp_width, trace_len, order*2*temp_width/1000.0, (order*2*temp_width+(order*2+1)*self.spacing)/1000.0)
                
            # stop if there is no longer space on the board for the traces
            if (2**(order-1)*temp_width+(2**(order-1)+1)*self.spacing)/1000.0 > self.pcb_width:
                max_length = trace_len
                max_order = order
                break
                
            max_length = trace_len
            max_order = order
            order += 1

        self.min_order = (min_order, min_length, self.trace.width_for_length(min_length))
        self.max_order = (max_order, max_length, self.trace.width_for_length(max_length))


if __name__ == '__main__':
    size = [5.0, 5.0]
    generator = PCBGenerator(12, 100, size)
    PCBWriter("blah", size, int(generator.max_order[2]), generator.generate_max_trace())
