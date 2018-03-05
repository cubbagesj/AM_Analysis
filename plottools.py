# plottools.py
#
# Copyright (C) 2006-2007 - Samuel J. Cubbage
#
# This program is part of the Autonomous Model Software Tools Package
#
# Updated 8/13/2010 by C.Michael Pietras
"""
    This is a collection of helper functions for the plotting
    AM and RCM data.  It uses the Matplotlib library to create
    graphs of the data.
    
    Functions Provided:
    
    get_runs() - Takes a list of run numbers and returns a list of
                FileType objects that hold the run data.  This is the primary
                tool for reading in the data
    get_xy() -  Returns a tuple of x,y data from a specific run.  The data
                can either be raw counts or converted to EU
    get_runs_overplot() - Takes a list of run numbers and returns a list of
                FileType objects that hold the run data.  This is the primary
                tool for reading in the data.  It is modified from get_runs to 
                make overplot work.  
    xy_plt() -  Creates a single xy plot for a list of runs
    
    y_plt() -   Creates a single y vs time plot for a list of runs
    
    my_plt() -  Similar to y_plt() but customized for use by mplt routine
    
    xfrm() -    Performs transforms on a set of data, like a filter
    
    mplt() -    Sets up a multi page plot and creates a PlotPage instance
    
    
"""
import matplotlib.pyplot as plt
#matplotlib.use('WXAgg')
from filetypes import OBCFile, STDFile, TDMSFile
import os, re
import numpy as np



def get_runs( run_list, obc_path='', std_path=''):
    """  Return a list of FileType objects for each run found
    
        Attempt to find each run in the run_list on either the
        specified paths, or the default.  If found, create a FileType object
        and return a list of objects found.  If no runs are found, return None
    """
    
    # Now parse the run_list
    runs = []
    
    std_path = os.path.expanduser('~')
    obc_path = r'\\ATIS21\MODEL\RCM\Autonomous_Model\test_data'

    # search pattern for std filenames - Assumes that a file with a '-' in the
    # name is an STD file.  If the file ends in 'obc' it is an OBC file, all
    # others are considered TDMS files.   
    stdm = re.compile(r'^\w+-\w+$')
    
    for runnum in run_list:
        if stdm.match(runnum.strip()):
            runobj = STDFile(runnum, search_path=std_path)
        elif runnum[-3:] == 'obc':
            runobj = OBCFile(runnum, search_path=obc_path)
        else:
            runobj = TDMSFile(runnum, search_path=obc_path)
    
        # If we found a run, add it to the list of run objects
        if runobj.filename:
            runs.append(runobj)

    return runs

def get_run(run_list):
    """  Return a FileType object for the run if found
    
        Special version of get_runs that retrives a run based
        on an absolute path
    """
    
    head, tail = os.path.split(run_list)
    root, ext = os.path.splitext(tail)
    
    if ext.lower() == '.std':
        runobj = STDFile(run_list, search_path='known')
    elif ext.lower() == '.obc':
        runobj = OBCFile(root[4:], search_path=head)
    elif ext.lower() == '.tdms':
        runobj = TDMSFile(root[4:], search_path=head)
    else:
        runobj = None
    
    return runobj

def get_runs_overplot( run_list, title_list, obc_path='', std_path=''): #made a new 
    """  Return a list of FileType objects for each run found
    
        Attempt to find each run in the run_list on either the
        specified paths, or the default.  If found, create a FileType object
        and return a list of objects found and a list of the index of each 
        object.  If no runs are found, return None
    """
      
    # Now parse the run_list
    runs,titles,i = [], [],0
    
    # in case the paths are undefined
    if std_path == '':
        std_path = os.path.expanduser('~')

    # search pattern for std filenames - Assumes that a file with a '-' in the
    # name is an STD file.  All others are considered OBC files
    
    stdm = re.compile(r'^\w+-\w+$')
    
    
    for runnum in run_list:
        if stdm.match(runnum.strip()):
            runobj = STDFile(runnum, search_path=std_path)
        else:
            runobj = OBCFile(runnum, search_path=obc_path)
    
        # If we found a run, add it to the list of run objects
        if runobj.filename:
            runs.append(runobj)
            titles.append(title_list[i])
        i+=1

    return runs, titles


def get_xy(runobj, ychan=0, xchan=-1, EU=True):
    """
        Retrieve the x,y data from the runobj
        
        Returns a tuple of the x,y data.  Default x is
        normalized time(-1), default y is channel 0
    """

    # Now we need to get the data. Start with x
    if xchan == -2:
        xdata = runobj.time
    elif xchan == -1:
        xdata = runobj.ntime
    elif xchan >= 0 and xchan < runobj.nchans:
        if EU:
            xdata = runobj.getEUData(xchan).values
        else:
            xdata = runobj.getRAWData(xchan).values
    else:
        xdata = runobj.ntime
        
    if ychan >= 0 and ychan < runobj.nchans:
        if EU:
            ydata = runobj.getEUData(ychan).values
        else:
            ydata = runobj.getRAWData(ychan).values
    else:
        ydata = runobj.getEUData(0).values
          
    return xdata,ydata

def xy_plt(run_list, ychan=0, xchan=-1, **kargs):
    """
        Create a single xy plot from multiple FileType objects
        
        Plots user specified x versus y, If no x given just use
        ntime.  Use **kargs to specify xmin, xmax, ymin, ymax, scale,
        offset, and xform
        -xform is not yet implemented
        
    """
    
    # For each run get the data and plot
    
    for runobj in run_list:
        xdata, ydata = get_xy(runobj, ychan, xchan)
        
        # Now for transforms
        scale = kargs.pop('scale', None)
        offset = kargs.pop('offset', None)
        xform = kargs.pop('xform', None)
        if scale or offset or xform:
            ydata = xfrm(ydata, runobj.dt, scale, offset, xform)
             
        plt.plot(xdata, ydata, label=runobj.filename)
        plt.hold(True)
    
    # Now decorate it with labels
    if xchan == -1:
        plt.xlabel('nTime (s)')
    elif xchan == -2:
        plt.xlabel('Time (s)')
    else:
        plt.xlabel(run_list[0].chan_names[xchan])
    
    plt.ylabel(run_list[0].chan_names[ychan])

    # Turn on the Grid
    plt.grid(True)
    
    # scale the axis if needed
    plt.axis(**kargs)
    
    #resize

    plt.legend()
    plt.show()
    
    return plt.gca()
    
def y_plt(run_list, ychan=0, **kargs):
    """
        Create a single plot from multiple FileType objects.
        Returns an axes object
        
        Plots user specified y versus nTime. Use **kargs to
        specify xmin, xmax, ymin, ymax, scale, offset, and xform

        
    """
    # For each run get the data and plot
    
    for runobj in run_list:
        xdata, ydata = get_xy(runobj, ychan, -1)
        # Now for transforms
        scale = kargs.pop('scale', None)
        offset = kargs.pop('offset', None)
        xform = kargs.pop('xform', None)
        if scale or offset or xform:
            ydata = xfrm(ydata, runobj.dt, scale, offset, xform)
        plot(xdata, ydata, label=runobj.filename)
        hold(True)
        
    
    # Now decorate it with labels
    xlabel('nTime (s)')
    
    ylabel(run_list[0].chan_names[ychan])

    # Turn on the Grid
    grid(True)
    
    # scale the axis if needed
    axis(**kargs)
    legend()
    show()
    
    return gca()

def my_plt(ax, run_list, ychan=0, **kargs):
    """
        Create a single plot from multiple FileType objects.
        Returns an axes object
        
        Plots user specified y versus nTime. Use **kargs to
        specify xmin, xmax, ymin, ymax, scale, offset, and xform

        
    """
    # For each run get the data and plot
    
    axes(ax)
    cla()
    scale = kargs.pop('scale', None)
    offset = kargs.pop('offset', None)
    xform = kargs.pop('xform', None)
    for runobj in run_list:
        xdata, ydata = get_xy(runobj, ychan, -1)
        # Now for transforms
        if scale or offset or xform:
            ydata = xfrm(ydata, runobj.dt, scale, offset, xform)
            
        plot(xdata, ydata, label=runobj.filename[:-4])
        hold(True)
        
   
    # Now decorate it with labels
    xlabel('nTime (s)')
    
    ylabel(run_list[0].chan_names[ychan])

    # Turn on the Grid
    grid(True)
    
    # scale the axis if needed
    axis(**kargs)
    
    return gca()
    
def xfrm(data, dt = 1.0, scale=None, offset=None, xform=None):
    """ Perform transforms on data """
    
    if scale:
        data = data * scale
    if offset:
        data = data - offset
    if xform >= 10 and xform < 20:
        tau = xform - 10.0
        tfact = (1 - exp(-dt/tau))
        for i in range(len(data)):
            if i > 0:
                data[i] = data[i-1] + (data[i] - data[i-1])*tfact
                
    return data

def mplt(run_list, plotdef=None):
    """ Set up the multi-plot 
       run_list - list of run numbers to plot
       plotdef - plot config file with channels to plot
    """
    
    pg = PlotPage(run_list, plotdef)
    # Display first page
    pg.firstpg()

class PlotPageWrapped:
    """
        PlotPage class is a page of 1 or more plots.  PlotPageWrapped is passed all
        the information needed to make a plot, with all the information that would
        be read from an ini file contained in the dictionary iniData.
        This makes it possible to make a PlotPage without having a specific ini
        file for the channels you want plotted.
    """
    def __init__(self, run_list, params=(0,0,3), iniData=None, plot_title = ''):
        """
            Creates a PlotPage instance using the
            run-list and plotdef file
        """
        self.plot_title = plot_title
        self.run_list = run_list
        self.numchans = iniData['numchans']
        self.funcs = iniData['funcs']
        self.ychans = iniData['ychans']
        self.ymins = iniData['ymins']
        self.ymaxs = iniData['ymaxs']
        self.yscales = iniData['yscales']
        self.yxforms = iniData['yxforms']
        self.yoffsets = iniData['yoffsets']
        self.ychanlists = iniData['ychanlists']
        self.ychanlabels = iniData['ylabels']
        
        
        self.perpage = params[2]
        self.xmin = params[0]
        self.xmax = params[1]
            
        self.pgpntr = 0
        
    def firstpg(self):
        """
            Create the first page and set up the key event
            This must be called before nxtpage or prevpage
        """
        
        figure(figsize=(10,12))
        connect('key_press_event', self.kpress)
        ioff()
        self.pltpage()
        
    def nxtpage(self):
        """
            Increments the plot pointer to display the next set of
            plots.  Going past the end of the list starts back
            at the beginning
        """
        self.pgpntr += self.perpage
        if (self.pgpntr+self.perpage) > self.numchans:
            self.pgpntr = 0
        ioff()
        self.pltpage()

    def prevpage(self):
        """
            Decrements the plot pointer.  Does not roll past
            the start of the list
        """
    
        self.pgpntr -= self.perpage
        if self.pgpntr < 0:
            self.pgpntr = 0
        ioff()
        self.pltpage()
 
    def kpress(self, event):
        """
            Key event to cycle through plots.  Keys are 'n', 'p', and 'q'
        """
        if event.key == 'n':
            self.nxtpage()
        if event.key == 'p':
            self.prevpage()
        if event.key == 'q':
            close('all')
            self.Destroy()
    
    def pltpage(self):
        """
            Draw the actual plots
        """
        for i in range(self.perpage):
            if i == 0:
                ax = subplot(self.perpage, 1, i+1)
                ax0 = ax
            else:
                ax = subplot(self.perpage, 1, i+1, sharex=ax0)
            try:
                # Plot the data
                ychan = self.ychans[self.pgpntr + i]
                my_plt(ax, self.run_list, ychan,
                       scale=self.yscales[self.pgpntr + i],
                       offset=self.yoffsets[self.pgpntr + i],
                       xform=self.yxforms[self.pgpntr + i])
                yrange = (self.ymins[self.pgpntr + i],
                          self.ymaxs[self.pgpntr + i])
                
                # Setup legend
                if i ==0:
                    legend(loc='best')
                    leg = gca().get_legend()
                    ltext = leg.get_texts()
                    setp(ltext, fontsize='small')
                
                # Set the limits
                if self.xmax or self.xmin:
                    xlim(self.xmin, self.xmax)
                if yrange[0] or yrange[1]:
                    ylim(yrange)
                if self.ychanlabels[self.pgpntr + i] != '':
                    ylabel(self.ychanlabels[self.pgpntr + i])
                    
                # Put the plot.ini filename on the graph
                figtext(0.03, 0.03, self.plot_title, rotation=90)
                
                # put run titles
                yloc = 0.0
                for run in self.run_list:
                    figtext(0.15, 0.97-yloc, run.title)
                    yloc += .015
            except:
                close('all')
                raise
        try:
            show()
        except:
            pass    
    
class PlotPage(PlotPageWrapped):
    """
        Wrapper for PlotPageWrapped.  Basically parses the given ini file and
        passes PlotPageWrapped the information in the ini file in dictionary form.
    """
    def __init__(self, run_list, params=(0,0,0), plotdef=None):
        
        # Check to see if plotdef exists and use default if not
        if not os.path.isfile(plotdef):
            if run_list[0].filetype != 'AM-obc':
                plotdef='plot-std.ini'
            else:
                plotdef='plot-obc.ini'
                
        #Read the plot definition file
        numchans = 0

        ychans = []
        ymins = []
        ymaxs = []
        yscales =[]
        yoffsets = []
        yxforms = []
        funcs = []
        ychanlists = []
        ylabels = []
        
        plot_file = open(plotdef)
        for line in plot_file:
            line = line.rstrip()
            func = ''
            ylbl=''
            try:
                ychan, ymin, ymax, yscale, yoffset, yxform, func, ylbl = line.split()
            except ValueError:
                try:
                    ychan, ymin, ymax, yscale, yoffset, yxform, func = line.split()
                except ValueError:
                    ychan, ymin, ymax, yscale, yoffset, yxform = line.split()
            ychan = np.int_(ychan.split(','))
            if not func:
                func = '=$'+str(ychan[0])
            ychanlists.append(ychan)
            ychans.append(max(ychan))
            ymins.append(float(ymin))
            ymaxs.append(float(ymax))
            yscales.append(float(yscale))
            yoffsets.append(float(yoffset))
            yxforms.append(int(yxform))
            funcs.append(func)
            ylabels.append(ylbl.replace('_',' '))
            numchans += 1
            
        iniData = {'numchans':numchans, 'funcs':funcs, 'ychans':ychans, 'ymins':ymins, 'ymaxs':ymaxs,
                'yscales':yscales, 'yoffsets':yoffsets, 'yxforms':yxforms, 'ychanlists':ychanlists, 'ylabels':ylabels}
            
        PlotPageWrapped.__init__(self, run_list, params = params, iniData = iniData, plot_title = plotdef)
   
if __name__ == "__main__":
    runlist = get_run(r's:\autonomous_model\test_data\ssgn\03132007\run-2337.obc')
    print(runlist.nchans)

#    runlist = get_runs(["7-16595", "7-16596"])
#    xy_plt(runlist, 21,  ymin=2000, scale=2)
    
#    mplt(runlist, 'plot-amall.ini')    
    
