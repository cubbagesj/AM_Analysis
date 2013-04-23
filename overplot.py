#!/usr/bin/env python
# overplot.py
#
# Copyright (C) 2006-2007 - Samuel J. Cubbage
# 
#  This program is part of the Autonomous Model Software Tools Package
# 
# Updated 8/13/2010 by C.Michael Pietras
"""
This class defines an Overplot frame that allows user to create
overplots of model data.  The frame can be standalone or is normally
called from the AM_tools utility

The user selects a plot definition file and the desired runs to overplot
along with the x-range and an optional title.
"""

import wx
import wx.grid, wx.html
import os


# The actual plotting routines are found in plottools and the actual plot
# page frame comes from multicanvas

from plottools import *
from multicanvas import MultiCanvasFrame
from printplot import PrintPlot

class OverPlotFrame(wx.Frame):
    
    def __init__(self, numruns = 4):
        '''Initializes the frame and all the widgets.  There are a number of run
        fields in the window equal to the numruns variable.'''
        wx.Frame.__init__(self, None, -1, 'Overplot', style=wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(wx.NamedColor("LIGHTGREY"))
        
        # decorate the frame with the widgets
        topLbl = wx.StaticText(self, -1, "Overplot Runs")
        topLbl.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        # plot input file section
        fileLabel = wx.StaticText(self, -1, "Plot Config File:")
        self.fileText = wx.TextCtrl(self, -1, value="", 
                                    size=(200, -1))
        self.PlotCfg = None
        self.fileBtn = wx.Button(self, -1, "Pick File")
        self.Bind(wx.EVT_BUTTON, self.OnFileClick, self.fileBtn)
        self.editBtn = wx.Button(self, -1, "Edit File")
        self.Bind(wx.EVT_BUTTON, self.OnEditClick, self.editBtn)
        
        # Overall Plot parameters
        paramLabel = wx.StaticText(self, -1, "Overall Plot Parameters:")
        paramLabel.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.xMin = wx.TextCtrl(self, -1, value="0", size=(40, -1))
        self.xMax = wx.TextCtrl(self, -1, value="0", size=(40, -1))
        self.perPage = wx.TextCtrl(self, -1, value="3", size=(40, -1))

        # Run number and title section.  The number of run numbers that can be plotted
        # by overplot is controlled by the runnums variable
        runLabel = wx.StaticText(self, -1, "Run Numbers To Plot:")
        runLabel.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.runNo = []
        self.titleNo = []
        for i in range(numruns):
            self.runNo.append(wx.TextCtrl(self, -1, size=(150, -1)))
            self.titleNo.append(wx.TextCtrl(self, -1, size=(250, -1)))
        
        # Screen Plot Button
        plotBtn = wx.Button(self, -1, "Create Screen Plot")
        plotBtn.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.Bind(wx.EVT_BUTTON, self.OnPlotClick, plotBtn)

        # Print Plot Button
        prnplotBtn = wx.Button(self, -1, "Create Pdf Plot")
        prnplotBtn.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.Bind(wx.EVT_BUTTON, self.OnPrnPlotClick, prnplotBtn)

        # Set up the layout with sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(topLbl, 0, wx.ALL, 5)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        
        fileSizer = wx.BoxSizer(wx.HORIZONTAL)
        fileSizer.Add(fileLabel, 0, wx.ALL, 5)
        fileSizer.Add(self.fileText, 0, wx.ALL, 5)
        fileSizer.Add(self.fileBtn, 0, wx.ALL, 5)
        fileSizer.Add(self.editBtn, 0, wx.ALL, 5)
        mainSizer.Add(fileSizer, 0, wx.EXPAND|wx.ALL, 10)

        mainSizer.Add((20,20), 0)
        mainSizer.Add(paramLabel, 0, wx.ALL, 5)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)

        paramSizer = wx.BoxSizer(wx.HORIZONTAL)
        paramSizer.Add(wx.StaticText(self, -1, "X min"), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        paramSizer.Add(self.xMin, 0, wx.ALL, 10)
        paramSizer.Add(wx.StaticText(self, -1, "X max"), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        paramSizer.Add(self.xMax, 0, wx.ALL, 10)
        paramSizer.Add(wx.StaticText(self, -1, "Plots Per Page"), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        paramSizer.Add(self.perPage, 0, wx.ALL, 10)

        mainSizer.Add(paramSizer, 0, wx.EXPAND|wx.ALL, 10)
        
        mainSizer.Add((20,20), 0)
        mainSizer.Add(runLabel, 0, wx.ALL, 5)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        
        runSizer = wx.FlexGridSizer(cols=4, hgap=5, vgap=5)
        runSizer.AddGrowableCol(3)
        for i in range(numruns):
            runSizer.Add(wx.StaticText(self, -1, "Run "+str(i+1)), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
            runSizer.Add(self.runNo[i], 0, wx.EXPAND)
            runSizer.Add(wx.StaticText(self, -1, "Title"), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
            runSizer.Add(self.titleNo[i], 0, wx.EXPAND)
       
        mainSizer.Add(runSizer, 0, wx.EXPAND|wx.ALL, 5)
        mainSizer.Add((20,20), 0)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        mainSizer.Add(plotBtn, 0, wx.EXPAND|wx.ALL, 5)
        mainSizer.Add(prnplotBtn, 0, wx.EXPAND|wx.ALL, 5)
        
        self.SetSizer(mainSizer)
        self.Fit()
        
        self.numruns = numruns

    def OnFileClick(self, evt):
        dlg = wx.FileDialog(self, "Open plot config file...",
                                defaultDir="./plotfiles", wildcard="*.ini",
                                style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.PlotCfg = dlg.GetPath()
            self.fileText.SetValue(dlg.GetFilename())
        dlg.Destroy()
    
    def OnEditClick(self, evt):
        """ Displays a grid frame that allows the user to edit
            the plot configuration
        """
        # Before we display the data we need to open and read in the file
        # The file name is stored in self.PlotCfg
        frame = EditFrame(self.PlotCfg)
        frame.Show()
        
    def OnPlotClick(self, evt):
        """
            Get the values from the dialog box and create the plot
            with a call to mplt in the plottools module
        """
        plotData, titles = self.GetPlotData()
        if plotData:
            frame = MultiCanvasFrame(plotData, titles, 0)
            frame.Show()

    def OnPrnPlotClick(self, evt):
        """
            Get the values from the dialog box and save a pdf plot in the output
            folder using the PrintPlot function from the printplot module
        """
        plotData, titles = self.GetPlotData()
        if plotData:
            PrintPlot(plotData, titles, 0)
            
    def GetPlotData(self):
        cfgfile = self.PlotCfg
        
        if cfgfile:
            runlist = []
            titles = []
            for i in range(self.numruns):
                run = self.runNo[i].GetValue()
                title = self.titleNo[i].GetValue()
                if run.strip() != "":
                    runlist.append(run)
                    if title.strip() != "":
                        titles.append(run+" - "+title)
                    else:
                        titles.append(run)
                   
            params = (float(self.xMin.GetValue()), float(self.xMax.GetValue()), 
                       int(self.perPage.GetValue()))
                    
            runobjs,new_titles = get_runs_overplot(runlist,titles)
            
            i = 0
            for title in titles:
                if not title in new_titles:
                    dlg = wx.MessageDialog(None,'File '+titles[i]+' not found','Error',wx.OK)
                    result = dlg.ShowModal()
                    dlg.Destroy()
                i+=1
            titles = new_titles
            if runobjs:
                plotData = PlotPage(runobjs, params, cfgfile)
                return plotData, titles
            return False, False
        return False, False
        

class EditFrame(wx.Frame):
    def __init__(self, cfgFile):
        wx.Frame.__init__(self, None,
                          title="Edit plot Configuration",
                          size=(740,480))
        self.cfgFile = cfgFile
        plot_file = open(cfgFile)
        cfgData = []
        for line in plot_file:
            ylbl = ''
            line = line.rstrip()
            try:
                ychan, ymin, ymax, yscale, yoffset, yxform, yfunc, ylbl = line.split()
            except ValueError:
                try:
                    ychan, ymin, ymax, yscale, yoffset, yxform, yfunc = line.split()
                except ValueError:
                    ychan, ymin, ymax, yscale, yoffset, yxform = line.split()
                    channels = ychan.split(',')
                    yfunc = '=$'+channels[0]
            rowdata = [ychan, ymin, ymax, yscale, yoffset, yxform, yfunc, ylbl]
            cfgData.append(rowdata)

        self._grid = editGrid(self, cfgData)
        self.Build_Menu()
    
    def Build_Menu(self):
        """ build menu """
        MENU_EXIT  = wx.NewId()        
        MENU_SAVE  = wx.NewId()
        MENU_SAVEAS = wx.NewId()
        
 
        menuBar = wx.MenuBar()
        
        f0 = wx.Menu()
        f0.Append(MENU_SAVE,   "&Save",   "SaPyve Plot Config")
        f0.Append(MENU_SAVEAS,   "&Save As",   "Save Plot Config")
        f0.AppendSeparator()
        f0.Append(MENU_EXIT,   "E&xit", "Exit")
        f1 = wx.Menu()
        stdchannel_menu = f1.Append(-1, 'STD Channel List', 'View the list of STD file channels')
        obcchannel_menu = f1.Append(-1, 'OBC Channel List', 'View the list of OBC file channels')
        xform_menu = f1.Append(-1, 'Transform List', 'View the list of available transforms')  
        f2 = wx.Menu()
        func_help = f2.Append(-1, 'Function Help', 'View information about plotting functions')
        menuBar.Append(f0,     "&File")
        menuBar.Append(f1, "&View")
        menuBar.Append(f2, "&Help")

        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU, self.onSave,       id=MENU_SAVE)
        self.Bind(wx.EVT_MENU, self.onSaveAs,       id=MENU_SAVEAS)
        self.Bind(wx.EVT_MENU, self.onExit ,        id=MENU_EXIT)
        self.Bind(wx.EVT_MENU, self.onSTDView , stdchannel_menu)
        self.Bind(wx.EVT_MENU, self.onOBCView , obcchannel_menu)
        self.Bind(wx.EVT_MENU, self.onXFormView , xform_menu)
        self.Bind(wx.EVT_MENU, self.onFuncHelp , func_help)
    
    def onSTDView(self, evt):        
        """
            View a list the STD file channels and channel names
        """
        frame = ViewFrame('STD Channels', 'std_channel_table.txt')
        frame.Show()
    
    def onOBCView(self, evt):           
        """
            View a list the OBC file channels and channel names
        """  
        frame = ViewFrame('OBC Channels', 'obc_channel_table.txt')
        frame.Show()
    
    def onXFormView(self, evt):
             
        """
            View a list the available transforms by number what the transform 
            does.
        """
        frame = ViewFrame('Available Transforms', 'xform_table.txt')
        frame.Show()
        
    def onExit(self, evt):
        self.Destroy()
    
    def onSave(self, evt):
        cfgData = self._grid.getData()
        plot_file = open(self.cfgFile, "w")
        for line in cfgData:
            for item in line:
                plot_file.write("%s " % item)
            plot_file.write("\n")

    def onSaveAs(self, evt):
        cfgData = self._grid.getData()
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir="", 
            defaultFile="", wildcard="*.ini", style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            self.cfgFile = dlg.GetPath()

        plot_file = open(self.cfgFile, "w")
        for line in cfgData:
            for item in line:
                plot_file.write("%s " % item)
            plot_file.write("\n")
            
    def onFuncHelp(self,evt):
        """
            View an html help window that explains a little about how the 
            function functionality works
        """
        text = '''
        <html>
        <body bgcolor="ACAA60">
        <center><table bgcolor="#455481" width="100%" cellspacing="0"
        cellpadding="0" border="1">
        <tr>
            <td align="center"><h1>Function Plotting</h1></td>
        </tr>
        </table>
        </center>
        <p>The function plotting functionality allows you to plot functions of one or multiple
        channels.</p>
        
        <p>To plot a function, put a comma deliminated list of the channels you wish to plot 
        in the channel columns, then enter the function (with an = sign before it) in the 
        function column.</p>
        
        <p>Functions can use any of the array operations available in the numpy module, as well as
        mult(x,y) and div(x,y), which implement multiply or divide each element of x by the corresponding
        element of y.</p>
        
        <p>Integration and differentiation of one channel by another are covered by diff(x,y), 
        which differentiates x by y, and integrate(x,y), which integrates x by y.  The time channel,
        which is what will usually be used for y, is $26</p>
        
        <p>To specify channel in a function, place a $ sign before the channel number.  An example of a function: "
        "=abs($47)+abs($50)" 
        </body>
        </html>
        '''
        dlg = helpDialog(self, 'Plotting Functions', text)
        dlg.ShowModal()
        dlg.Destroy()
  
class editGrid(wx.grid.Grid):
    def __init__(self, parent, data):

        # The base class must be initialized *first*
        wx.grid.Grid.__init__(self, parent, -1)
        self._table = DataTable(data)
        self.SetTable(self._table)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.OnLabelRightClicked)
    
    def getData(self):
        return self._table.data

    def Reset(self):
        """reset the view based on the data in the table.  Call
        this when rows are added or destroyed"""
        self._table.ResetView(self)

    def OnLabelRightClicked(self, evt):
        # Did we click on a row or a column?
        # For now only have one type of popup
        row, col = evt.GetRow(), evt.GetCol()
        self.rowPopup(row, evt)

    def rowPopup(self, row, evt):
        """(row, evt) -> display a popup menu when a row label is right clicked"""
        appendID = wx.NewId()
        deleteID = wx.NewId()
        x = self.GetRowSize(row)/2

        if not self.GetSelectedRows():
            self.SelectRow(row)

        menu = wx.Menu()
        xo, yo = evt.GetPosition()
        menu.Append(appendID, "Append Row")
        menu.Append(deleteID, "Delete Row(s)")

        def append(event, self=self, row=row):
            self._table.AppendRow(row)
            self.Reset()

        def delete(event, self=self, row=row):
            rows = self.GetSelectedRows()
            self._table.DeleteRows(rows)
            self.Reset()

        self.Bind(wx.EVT_MENU, append, id=appendID)
        self.Bind(wx.EVT_MENU, delete, id=deleteID)
        self.PopupMenu(menu)
        menu.Destroy()
        return


class DataTable(wx.grid.PyGridTableBase):
    def __init__(self, cfgData):
        wx.grid.PyGridTableBase.__init__(self)
        self.data = cfgData
        self.colLabels = ["Channel", "Ymin", "Ymax", "Scale", "Offset", "Xform", "Function", "YLabel"]
        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()
        
    def GetNumberRows(self):
        return len(self.data)
    
    def GetNumberCols(self):
        return len(self.data[0])
    
    def GetValue(self, row, col):
        value = self.data[row][col]
        return value
    
    def IsEmptyCell(self, row, col):
        return False
    
    def SetValue(self, row, col, value):
        self.data[row][col] = value
        if col == 0:
            try:
                test = int(value)
                self.data[row][6] = "=$"+str(test)
            except: pass
    
    def GetColLabelValue(self, col):
        return self.colLabels[col]

    def GetRowLabelValue(self, row):
        return "Plot %d" % row
    
    def AppendRows(self, numRows=1):
        return (self.GetNumberRows() + numRows) <= 100
    
    def AppendRow(self, row):
        self.data.insert(row, [0,0,0,1,0,0,'=$0'])

    def DeleteRows(self, rows):
        """
        rows -> delete the rows from the dataset
        rows hold the row indices
        """
        deleteCount = 0
        rows = rows[:]
        rows.sort()

        for i in rows:
            self.data.pop(i-deleteCount)
            # we need to advance the delete count
            # to make sure we delete the right rows
            deleteCount += 1

    def UpdateValues(self, grid):
        """Update all displayed values"""
        # This sends an event to the grid table to update all of the values
        msg = wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        grid.ProcessTableMessage(msg)

        
    def ResetView(self, grid):
        """
        (Grid) -> Reset the grid view.   Call this to
        update the grid if rows and columns have been added or deleted
        """
        grid.BeginBatch()

        for current, new, delmsg, addmsg in [
            (self._rows, self.GetNumberRows(), wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED),
            (self._cols, self.GetNumberCols(), wx.grid.GRIDTABLE_NOTIFY_COLS_DELETED, wx.grid.GRIDTABLE_NOTIFY_COLS_APPENDED),
        ]:

            if new < current:
                msg = wx.grid.GridTableMessage(self,delmsg,new,current-new)
                grid.ProcessTableMessage(msg)
            elif new > current:
                msg = wx.grid.GridTableMessage(self,addmsg,new-current)
                grid.ProcessTableMessage(msg)
                self.UpdateValues(grid)

        grid.EndBatch()

        self._rows = self.GetNumberRows()
        self._cols = self.GetNumberCols()

        # update the scrollbars and the displayed part of the grid
        grid.AdjustScrollbars()
        grid.ForceRefresh()
          
class ViewFrame(wx.Frame):
    """
        Text view frame
    """
    def __init__(self, window_title, filename, window_size=(400,700)):
        wx.Frame.__init__(self, None, title=window_title, size=window_size)
        panel=wx.Panel(self)    
        file = open(filename)
        lines = file.readlines()
        
        text = ''
        
        for line in lines:
            text += line
        
        mainSizer = wx.FlexGridSizer(cols = 1, hgap = 5, vgap = 5)
        mainSizer.AddGrowableCol(0); mainSizer.AddGrowableRow(0);
        textbox = wx.TextCtrl(panel, -1, text, style = wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL)
        mainSizer.Add(textbox, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        panel.SetSizer(mainSizer)

class helpDialog(wx.Dialog):
    """
        HTML view frame
    """
    def __init__(self, parent, title, text):
        wx.Dialog.__init__(self, parent, -1, title, size=(440, 400) )
        
        html = wx.html.HtmlWindow(self)
        html.SetPage(text)
        button = wx.Button(self, wx.ID_OK, "Okay")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(button, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        
        self.SetSizer(sizer)
        self.Layout()

if __name__ == "__main__":
    app = wx.PySimpleApp(redirect=False)
    frame = OverPlotFrame()
    frame.Show()
    app.MainLoop()
