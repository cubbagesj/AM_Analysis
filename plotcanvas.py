#!/usr/bin/env python
# Modified 7/20/2010 - Christopher M. Pietras
"""
An example of how to use wx or wxagg in an application with the new
toolbar - comment out the setA_toolbar line for no toolbar
"""

import matplotlib

matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from matplotlib.figure import Figure

import wx
from plottools import *

class CanvasFrame(wx.Frame):

    #added xchan variable to control which channel is used as the x axis.  Defaults
    #to -1 so nothing should change for other uses.
    def __init__(self, runData, chans, xchan = -1, EU=True):
        wx.Frame.__init__(self,None,-1,
                          'Plot  '+runData.filename)

        self.SetBackgroundColour(wx.NamedColor("WHITE"))

        self.figure = Figure(figsize=(12,6))
        self.axes = self.figure.add_subplot(111)
        self.figure.subplots_adjust(bottom=.2)
        lines = []
        names = []
        for chan in chans:
            xdata, ydata = get_xy(runData, chan, xchan, EU=EU)

            #Get some values from the data for the max/min/mean
            self.ydata = ydata
            #changed code for max and min since they won't always be the first and
            #last index now.
            self.xmin = float(min(xdata))
            self.xmax = float(max(xdata))
            self.dt = runData.dt

            line = self.axes.plot(xdata, ydata)
            self.axes.grid(True)
            #x channel needs to be properly named
            if xchan == -2:
                self.axes.set_xlabel('Time (s)')
            if xchan == -1:
                self.axes.set_xlabel('nTime (s)')
            else:
                self.axes.set_xlabel(runData.chan_names[xchan])
            name = runData.chan_names[chan]
            lines.append(line)
            names.append(name)
        
        if len(chans) > 1:
            handles = []
            for i in range(len(chans)):
                handles.append(matplotlib.lines.Line2D([], [], color=lines[i][0].get_color(), marker=None))
            leg = self.axes.legend(handles, names, loc='lower left')
            ltext = leg.get_texts()
            setp(ltext, fontsize='small')
        else:
            self.axes.set_ylabel(names[0])

        self.canvas = FigureCanvas(self, -1, self.figure)
        self.cid = self.canvas.mpl_connect('draw_event', self.onDraw)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(4)
        self.add_toolbar()  # comment this out for no toolbar

    def add_toolbar(self):
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()
        tw, th = self.toolbar.GetSizeTuple()
        fw, fh = self.canvas.GetSizeTuple()
        # By adding toolbar in sizer, we are able to put it at the bottom
        # of the frame - so appearance is closer to GTK version.
        # As noted above, doesn't work for Mac.
        self.toolbar.SetSize(wx.Size(fw, th))
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()  

    def onDraw(self, event):
        xstart, xstop = self.axes.get_xlim()
        if xstart < self.xmin:
            xstart = self.xmin
        if xstop > self.xmax:
            xstop = self.xmax

        yminindex = int((xstart - self.xmin) / self.dt)
        ymaxindex = int((xstop - self.xmin) / self.dt)

        if yminindex < 0:
            yminindex = 0
        if ymaxindex > len(self.ydata)-1:
            ymaxindex = -1

        yrange = self.ydata[yminindex:ymaxindex]
        ymax = float(max(yrange))
        ymin = float(min(yrange))
        ymean = float(average(yrange))

        self.statusbar.SetStatusText('Max = %.3f' %ymax, 1)
        self.statusbar.SetStatusText('Min = %.3f' %ymin, 2)
        self.statusbar.SetStatusText('Mean = %.3f' %ymean, 3)

    def OnPaint(self, event):
        self.canvas.draw()

    def OnClose(self, event):
        self.canvas.mpl_disconnect(self.cid)
        self.Destroy()



if __name__ == "__main__":
    app = wx.PySimpleApp(redirect=False)
    frame = CanvasFrame()
    frame.Show()
    app.MainLoop()
