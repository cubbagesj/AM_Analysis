#!/usr/bin/env python
"""
Uses gnuplot to generate hard copy plots
"""

import matplotlib
import time
from matplotlib.backends.backend_pdf import PdfPages
from math import ceil

from plottools import *
from function_parse import doFunction, makeLabel

class PrintPlot:
    
    def __init__(self, plotData, titles, pgpntr):

        self.plotData = plotData
        self.titles = titles
        self.g = Gnuplot.Gnuplot(debug=1)
        #self.g('set term postscript color portrait')
        #elf.g('set output "test.ps"')

        self.makePlot()
        
 
    def makePlot(self):
        """
            Draw the plots using the number of plots per page defined
            in the plot configuration and save as a pdf
        """
        pp = PdfPages(r'output\PrintPlot'+str(time.time())+'.pdf')
        fig = figure()
        for p in range(int(ceil(float(self.plotData.numchans)/float(self.plotData.perpage)))):
            fig.clear()
            for i in range(self.plotData.perpage):
                try:
                    ychan = self.plotData.ychans[self.plotData.pgpntr + i]
                    scale = self.plotData.yscales[self.plotData.pgpntr + i]
                    xform = self.plotData.yxforms[self.plotData.pgpntr + i]
                    offset = self.plotData.yoffsets[self.plotData.pgpntr + i]
                    ychans = self.plotData.ychanlists[self.plotData.pgpntr + i]
                    function = self.plotData.funcs[self.plotData.pgpntr + i]
                    
                    d = fig.add_subplot(self.plotData.perpage, 1, i+1)
                    if i == self.plotData.perpage - 1:
                        d.set(xlabel = 'nTime (s)')
                    curve = 0
                    for runobj in self.plotData.run_list:
                        ydata = {}
                        for chan in ychans:
                            xdata, ydata[chan] = get_xy(runobj, chan, -1)
                        ydata = doFunction(function, ychans, ydata)
                        d.set(ylabel = makeLabel(function, ychans, runobj.chan_names))
                        if scale or offset or xform:
                            if xform == 3:
                                offset = runobj.init_values[ychan] - self.plotData.run_list[0].init_values[ychan]
                                ofst = float(offset)
                                ydata = xfrm(ydata, runobj.dt, scale, offset, xform)                        
                            else:
                                ydata = xfrm(ydata, runobj.dt, scale, offset, xform)
                        d.plot(xdata, ydata, label = str(self.titles[curve]))
                        curve+=1
                    if i == 0:
                        d.legend()
                except:
                    pass
            pp.savefig(fig)
            self.plotData.pgpntr += self.plotData.perpage
        pp.close()
if __name__ == "__main__":
    pass

