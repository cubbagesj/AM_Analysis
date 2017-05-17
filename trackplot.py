#!/usr/bin/env python
"""
  Creates an XY Track plot and labels the execute 90 and 180 points
"""

import matplotlib.pyplot as plt
import numpy as np
from plottools import get_xy

   
 
def TrackPlot(plotData, titles):
    """
        Draw the plots using the number of plots per page defined
        in the plot configuration and save as a pdf
    """
    
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)

    lines=[]

    for runobj in plotData.run_list:
        runobj.turnstats()
        xdata, ydata = get_xy(runobj, 21, 20)
        line = ax.plot(xdata, ydata)
        lines.append(line)
        ax.plot(xdata[runobj.index90], ydata[runobj.index90],'b*')
        ax.plot(xdata[runobj.index180], ydata[runobj.index180],'b+')

    ax.plot(0,0,'r*')
    ax.set_xlabel('X position (ft)')
    ax.set_ylabel('Y position (ft)')
    ax.set_title('XY Track')
    ax.grid(True)


    # Legend
    try:
        leg = fig.legend(lines, titles)
    except ValueError:
        pass

    fig.show()
