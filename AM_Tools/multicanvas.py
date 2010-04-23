#!/usr/bin/env python
"""
An example of how to use wx or wxagg in an application with the new
toolbar - comment out the setA_toolbar line for no toolbar
"""
import wx
import matplotlib

#matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from matplotlib.figure import Figure


from tools.plottools import *

class MultiCanvasFrame(wx.Frame):
    
    def __init__(self, plotData, titles, pgpntr):
        wx.Frame.__init__(self,None,-1,
                         'Over Plot  ')

        self.SetBackgroundColour(wx.NamedColor("WHITE"))

        self.figure = Figure(figsize=(8.7,10))
	self.figure.subplots_adjust(bottom=.15)
        self.plotData = plotData
        self.Build_Menus()
        self.titles = titles
        self.makePlot()
        
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.cid = self.canvas.mpl_connect('draw_event', self.onDraw)
        self.canvas.mpl_connect('key_press_event', self.kpress)
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(4)
        self.add_toolbar()  # comment this out for no toolbar

 
    def Build_Menus(self):
        """ build menus """
        MENU_EXIT  = wx.NewId()        
        MENU_SAVE  = wx.NewId()
        MENU_PRINT = wx.NewId()
        MENU_PSETUP= wx.NewId()
        MENU_PREVIEW=wx.NewId()
        MENU_CLIPB  =wx.NewId()
 
        menuBar = wx.MenuBar()
        
        f0 = wx.Menu()
        f0.Append(MENU_SAVE,   "&Export",   "Save Image of Plot")
        f0.AppendSeparator()
        f0.Append(MENU_PSETUP, "Page Setup...",    "Printer Setup")
        f0.Append(MENU_PREVIEW,"Print Preview...", "Print Preview")
        f0.Append(MENU_PRINT,  "&Print",           "Print Plot")
        f0.AppendSeparator()
        f0.Append(MENU_EXIT,   "E&xit", "Exit")
        menuBar.Append(f0,     "&File");

        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.onPrint,        id=MENU_PRINT)        
        self.Bind(wx.EVT_MENU, self.onPrinterSetup, id=MENU_PSETUP)
        self.Bind(wx.EVT_MENU, self.onPrinterPreview, id=MENU_PREVIEW)
        self.Bind(wx.EVT_MENU, self.onClipboard,    id=MENU_CLIPB)
        self.Bind(wx.EVT_MENU, self.onExport,       id=MENU_SAVE)
        self.Bind(wx.EVT_MENU, self.onExit ,        id=MENU_EXIT)
        
    # the printer / clipboard methods are implemented
    # in backend_wx, and so are very simple to use.
    def onPrinterSetup(self,event=None):
        self.canvas.Printer_Setup(event=event)

    def onPrinterPreview(self,event=None):
        self.canvas.Printer_Preview(event=event)

    def onPrint(self,event=None):
        self.canvas.Printer_Print(event=event)

    def onClipboard(self,event=None):
        self.canvas.Copy_to_Clipboard(event=event)

    def onHelp(self, event=None):
        dlg = wx.MessageDialog(self, self.help_msg,
                               "Quick Reference",
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def onExport(self,event=None):
        """ save figure image to file"""
        file_choices = "PNG (*.png)|*.png|" \
                       "PS (*.ps)|*.ps|" \
                       "EPS (*.eps)|*.eps|" \
                       "BMP (*.bmp)|*.bmp"                        
                       
        #thisdir  = os.getcwd()
	thisdir = 'c:/plots'

        dlg = wx.FileDialog(self, message='Save Plot Figure as...',
			defaultDir = thisdir, defaultFile=self.plotData.run_list[0].filename[:-4]+'-'+str(self.plotData.pgpntr),
                            wildcard=file_choices, style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path,dpi=300)
            if (path.find(thisdir) ==  0):
                path = path[len(thisdir)+1:]
            print 'Saved plot to %s' % path

    def onExit(self,event=None):
        self.Destroy()
 
    def makePlot(self):
        """
            Draw the plots using the number of plots per page defined
            in the plot configuration
        """
        for i in range(self.plotData.perpage):
            if i == 0:
                self.ax = self.figure.add_subplot(self.plotData.perpage, 1, i+1)
                ax0 = self.ax
            else:
                self.ax = self.figure.add_subplot(self.plotData.perpage, 1, i+1, sharex=ax0)
            ychan = self.plotData.ychans[self.plotData.pgpntr + i]
            scale = self.plotData.yscales[self.plotData.pgpntr + i]
            xform = self.plotData.yxforms[self.plotData.pgpntr + i]
            offset = self.plotData.yoffsets[self.plotData.pgpntr + i]
            lines = []
	    lcnt = 0
            for runobj in self.plotData.run_list:
                xdata, ydata = get_xy(runobj, ychan, -1)
                if scale or offset or xform:
                    if xform == 3:
                        offset = runobj.init_values[ychan] - self.plotData.run_list[0].init_values[ychan]
                        offset = float(offset)
			ydata = xfrm(ydata, runobj.dt, scale, offset, xform)
		    elif xform == 33:
			if ychan < len(runobj.appr_values):
			    try:
			        offset = runobj.appr_values[ychan] - self.plotData.run_list[0].appr_values[ychan]
 			    except:
			    	offset = runobj.appr_values[ychan] - 0.0
			else:
			    offset = 0
			offset = float(offset)
			ydata = xfrm(ydata, runobj.dt, scale, offset, 11)
		    else:
			ydata = xfrm(ydata, runobj.dt, scale, offset, xform)
		line = self.ax.plot(xdata, ydata)
                lines.append(line)
                self.ax.grid(True)
                if i == self.plotData.perpage - 1:
                    self.ax.set_xlabel('nTime (s)')
                try:
                    self.ax.set_ylabel(runobj.chan_names[ychan])
                except:
                    pass
            yrange = (self.plotData.ymins[self.plotData.pgpntr + i],
                      self.plotData.ymaxs[self.plotData.pgpntr + i])
            if self.plotData.xmin or self.plotData.xmax:
                self.ax.set_xlim(self.plotData.xmin, self.plotData.xmax)
            if yrange[0] or yrange[1]:
                self.ax.set_ylim(yrange)
            
            
            # Set up the legend
            if i == 0:
#                leg = ax0.legend(lines, self.titles, (.5, .5))
                leg = self.figure.legend(lines, self.titles, (.3, .901))
                ltext = leg.get_texts()
                setp(ltext, fontsize='small')
                
    def kpress(self, event):
        if event.key == 'n':
            self.figure.clear()
            self.plotData.pgpntr += self.plotData.perpage
            if (self.plotData.pgpntr + self.plotData.perpage) > self.plotData.numchans:
                self.plotData.pgpntr = 0
            self.makePlot()
            self.canvas.draw()
        if event.key == 'p':
            self.figure.clear()
            self.plotData.pgpntr -= self.plotData.perpage
            if self.plotData.pgpntr < 0:
                self.plotData.pgpntr = 0
            self.makePlot()
            self.canvas.draw()
            
        if event.key == 'q':
            self.Destroy()

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
        pass
    
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

