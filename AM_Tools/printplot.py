#!/usr/bin/env python
"""
Uses gnuplot to generate hard copy plots
"""

import matplotlib
import time
import Gnuplot

from matplotlib.figure import Figure

from tools.plottools import *

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
            in the plot configuration
        """
        for p in range(self.plotData.numchans/self.plotData.perpage):
            for i in range(self.plotData.perpage):
                if i == 0:
                    self.g('set multiplot title "VIRGINIA Scaling Study" layout 3,1')
                    self.g('set grid')
                    self.g('set bmargin at screen .05')
                    self.g('set tmargin at screen .9')
                    self.g('set key tmargin')
                    self.g('set format x ""')
                    self.g('set format y "%6.1f"')
                    self.g.xlabel('')
                else:
                    self.g('set key off')
                ychan = self.plotData.ychans[self.plotData.pgpntr + i]
                scale = self.plotData.yscales[self.plotData.pgpntr + i]
                xform = self.plotData.yxforms[self.plotData.pgpntr + i]
                offset = self.plotData.yoffsets[self.plotData.pgpntr + i]
                lines = []
                plots = []
                curve = 0
                for runobj in self.plotData.run_list:
                    xdata, ydata = get_xy(runobj, ychan, -1)
                    if scale or offset or xform:
                        if xform == 3:
                            offset = runobj.init_values[ychan] - self.plotData.run_list[0].init_values[ychan]
                            ofst = float(offset)
                            ydata = xfrm(ydata, runobj.dt, scale, offset, xform)                        
                        else:
                            ydata = xfrm(ydata, runobj.dt, scale, offset, xform)
                    if i == self.plotData.perpage - 1:
                        self.g.xlabel('nTime (s)')
                        self.g('set format x "%g"')
                        pass
                    try:
                        self.g.ylabel(runobj.chan_names[ychan])
                    except:
                        pass
                    d = Gnuplot.Data(xdata, ydata, with_='lines', title=str(self.titles[curve]))
                    plots.append(d)
                    curve +=1               
                self.g.plot(plots[0], plots[1])
                time.sleep(1)
            self.plotData.pgpntr += self.plotData.perpage
            time.sleep(10)
##            yrange = (self.plotData.ymins[self.plotData.pgpntr + i],
##                      self.plotData.ymaxs[self.plotData.pgpntr + i])
##            if self.plotData.xmin or self.plotData.xmax:
##                self.ax.set_xlim(self.plotData.xmin, self.plotData.xmax)
##            if yrange[0] or yrange[1]:
##                self.ax.set_ylim(yrange)
##            
            
##            # Set up the legend
##            if i == 0:
###                leg = ax0.legend(lines, self.titles, (.5, .5))
##                leg = self.figure.legend(lines, self.titles, (.3, .901))
##                ltext = leg.get_texts()
##                setp(ltext, fontsize='small')
##                
if __name__ == "__main__":
    pass

