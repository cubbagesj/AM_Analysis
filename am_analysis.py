#!/usr/bin/env python
# Run_Browser.py
#
# Copyright (C) 2007 - Samuel J. Cubbage
#
# This program is part of the Autonomous Model Software Tools Package
#
# a wxPython program to browse the run files and display info about each run

# 3/23/2007s
# Updated 8/13/2010 by C.Michael Pietras

# Updated 3/10/2016 to add .tdms data file support by Woody Pfitsch
# sjc - 1/2018 - Updates to convert to using pandas for the data struture

#Imports - Standard Libraries
import wx
import wx.grid, wx.html
import os
import fnmatch

# Imports - Local Packages
from plotcanvas import CanvasFrame
import plottools as plottools
import images
import mergewiz
import overplot
import analysis
import extrema
from BoS_run_comparison import CorrelateFrame
import TDMStoOBCwiz

class BrowserFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Run File Browser", size=(1000,650))
        
        # Some of the functions differ between windows and linux
        # So check here for the system and set a flag
        self.osname = os.name
        
        self.readFilePaths()
 
        # Set up the status bar
        self.statusbar = self.CreateStatusBar()

        # Set up the split window
        self.sp = wx.SplitterWindow(self)

        #Left Pane
        self.p1 = wx.Panel(self.sp, style= wx.SUNKEN_BORDER)
        self.createFileTree(self.p1)

        # Right Pane
        self.p2 = wx.Panel(self.sp, style= wx.SUNKEN_BORDER)
        self.createInfoView(self.p2)
        self.createMenuBar()

        self.sp.SplitVertically(self.p1, self.p2, 300)

    def createInfoView(self, panel):
        # The display components
        topLbl = wx.StaticText(panel, -1, "File Information")
        topLbl.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))

        fnameLbl = wx.StaticText(panel, -1, "Filename:")
        self.fname = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)

        titleLbl = wx.StaticText(panel, -1, "Title:")
        self.title = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)

        timestmpLbl = wx.StaticText(panel, -1, "Time Stamp:")
        self.timestmp = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)

        nchansLbl = wx.StaticText(panel, -1, "Number of Channels:")
        self.nchans = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)

        dtLbl = wx.StaticText(panel, -1, "Timestep:")
        self.dt = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)

        stdbyLbl = wx.StaticText(panel, -1, "Standby At:")
        self.stdbytime = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)

        execLbl = wx.StaticText(panel, -1, "Execute At:")
        self.exectime = wx.TextCtrl(panel, -1, "", style=wx.TE_READONLY)

        #Listbox for y axis channels
        chanList = wx.StaticText(panel, -1, "Channel List:")
        self.chanList = wx.ListBox(panel, -1, size=(200,200),
                                   style=wx.LB_EXTENDED, name="Channel List")

        #Listbox for x axis channels
        xchanList = wx.StaticText(panel, -1, "X Axis Channel List:")
        self.xchanList = wx.ListBox(panel, -1, size=(150,180),
                                    style=wx.LB_SINGLE, name="X Axis Channel List")

        # The buttons
        self.calBtn = wx.Button(panel, -1, "View CAL File")
        self.calBtn.Enable(False)
        self.dataBtn = wx.Button(panel, -1, "View RAW Data")
        self.dataBtn.Enable(False)
        self.dataBtnEU = wx.Button(panel, -1, "View EU Data")
        self.dataBtnEU.Enable(False)
        self.graphBtnRaw = wx.Button(panel, -1, "Quick RAW Graph")
        self.graphBtnRaw.Enable(False)
        self.graphBtn = wx.Button(panel, -1, "Quick EU Graph")
        self.graphBtn.Enable(False)


        #Button Events
        self.Bind(wx.EVT_BUTTON, self.OnCalClick, self.calBtn)
        self.Bind(wx.EVT_BUTTON, self.OnDataClick, self.dataBtn)
        self.Bind(wx.EVT_BUTTON, self.OnDataEUClick, self.dataBtnEU)
        self.Bind(wx.EVT_BUTTON, self.OnGraphClick, self.graphBtn)
        self.Bind(wx.EVT_BUTTON, self.OnGraphRawClick, self.graphBtnRaw)

        # Set up the layout with sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(topLbl, 0, wx.ALL, 5)
        mainSizer.Add(wx.StaticLine(panel), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)

        infoSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        infoSizer.AddGrowableCol(1)
        infoSizer.Add(fnameLbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        infoSizer.Add(self.fname, 0, wx.EXPAND)
        infoSizer.Add(titleLbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        infoSizer.Add(self.title, 0, wx.EXPAND)
        infoSizer.Add(timestmpLbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        infoSizer.Add(self.timestmp, 0, wx.EXPAND)
        infoSizer.Add(nchansLbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

        ndtSizer = wx.BoxSizer(wx.HORIZONTAL)
        ndtSizer.Add(self.nchans, 0, wx.RIGHT, 20)
        ndtSizer.Add(dtLbl, 0)
        ndtSizer.Add(self.dt, 0, wx.LEFT|wx.RIGHT,5)
        infoSizer.Add(ndtSizer, 0, wx.EXPAND)

        timeSizer = wx.BoxSizer(wx.HORIZONTAL)
        infoSizer.Add(stdbyLbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        timeSizer.Add(self.stdbytime, 0, wx.RIGHT, 10)
        timeSizer.Add(execLbl, 0)
        timeSizer.Add(self.exectime, 0, wx.LEFT|wx.RIGHT, 5)
        infoSizer.Add(timeSizer, 0)

        infoSizer.Add(chanList, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

        chanSizer = wx.BoxSizer(wx.HORIZONTAL)
        chanSizer.Add(self.chanList, 0, wx.LEFT|wx.RIGHT)
        chanSizer.Add(xchanList, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        chanSizer.Add(self.xchanList, 0, wx.LEFT|wx.RIGHT)
        infoSizer.Add(chanSizer)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20), 1)
        btnSizer.Add(self.calBtn)
        btnSizer.Add((20,20), 1)
        btnSizer.Add(self.dataBtn)
        btnSizer.Add((20,20), 1)
        btnSizer.Add(self.dataBtnEU)
        btnSizer.Add((20,20), 1)
        btnSizer.Add(self.graphBtnRaw)
        btnSizer.Add((20,20), 1)
        btnSizer.Add(self.graphBtn)
        btnSizer.Add((20,20), 1)
        

        mainSizer.Add(infoSizer, 0, wx.EXPAND|wx.ALL, 10)
        mainSizer.Add((20,20),1)
        mainSizer.Add(btnSizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        panel.SetSizer(mainSizer)
        mainSizer.Fit(panel)
        mainSizer.SetSizeHints(panel)


    def createFileTree(self, parent):
        self.tree = wx.TreeCtrl(parent, -1,
                                style=wx.TR_HAS_BUTTONS)

        sizer=wx.GridSizer(1,0,0)
        sizer.Add(self.tree, flag = wx.GROW)
        parent.SetSizer(sizer)
        parent.Fit()

        # Create an Image list for the pictures in the tree
        il = wx.ImageList(16,16)
        self.fldridx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16,16)))
        self.fldropenidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16,16)))
        self.fileidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16,16)))

        self.tree.AssignImageList(il)

        root = self.tree.AddRoot("Data Files")
        self.tree.SetItemImage(root, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(root, self.fldropenidx, wx.TreeItemIcon_Expanded)


        # Add a root node for OBC File
        self.obcroot = self.tree.AppendItem(root, "OBC Files")
        self.tree.SetItemImage(self.obcroot, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.obcroot, self.fldropenidx, wx.TreeItemIcon_Expanded)

        # Add a root node for TDMS File
        self.tdmsroot = self.tree.AppendItem(root, "TDMS Files")
        self.tree.SetItemImage(self.tdmsroot, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.tdmsroot, self.fldropenidx, wx.TreeItemIcon_Expanded)

        # Add a root node for STD File
        self.stdroot = self.tree.AppendItem(root, "STD Files")
        self.tree.SetItemImage(self.stdroot, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.stdroot, self.fldropenidx, wx.TreeItemIcon_Expanded)

        # Add a root node for FST Files
        self.fstroot = self.tree.AppendItem(root, "FST Files")
        self.tree.SetItemImage(self.fstroot, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.fstroot, self.fldropenidx, wx.TreeItemIcon_Expanded)

        # Bind some interesting events
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed, self.tree)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated, self.tree)

        #Expand the first level        
        self.tree.Expand(root)

        self.buildFileTree()
        
    def readFilePaths(self):
        """
            Reads in the default paths from the 'defaultPaths.txt' file
            and sets the class properties to the paths defined
        """
        
        f = open('defaultPaths.txt', 'r')
        path_lines = f.read().splitlines()
        
        default_Paths = {}
        # Loop through the file to get the paths
        for line in path_lines:
            if line == '':
                continue
            elif line[0] == '#':
                continue
            else:
                entry = line.split()
                default_Paths[entry[0]] = entry[1]
        
        self.defaultPaths = default_Paths
             

    def buildFileTree(self):
        """
            Creates the nodes for STD, OBC, and FST files.  Also used to rebuild
            the file tree after it's been cleared
        """

        # Pull the paths from the default path dictionary
        obcDir = self.defaultPaths['obcDir']
        tdmsDir = self.defaultPaths['tdmsDir']
        stdDir = self.defaultPaths['stdDir']
        fstDir = self.defaultPaths['fstDir']
            
        if os.path.exists(obcDir):
            self.TreeBuilder(obcDir, self.obcroot)
        if os.path.exists(tdmsDir):
            self.TreeBuilder(tdmsDir, self.tdmsroot)
        if os.path.exists(stdDir):
            self.TreeBuilder(stdDir, self.stdroot)
        if os.path.exists(fstDir):
            try:
                self.TreeBuilder(fstDir, self.fstroot)
            except:
                pass

    def TreeBuilder(self, currdir, branch):
        """ 
            Populates the tree with files of the known data types
            Types are: .std, .obc, .tdms
        """
        
        for file in os.listdir(currdir):
            path = os.path.join(currdir, file)
            if not os.path.isdir(path):
                head, tail = os.path.split(path)
                if fnmatch.fnmatch(tail, '*.obc') or fnmatch.fnmatch(tail, '*.std') or fnmatch.fnmatch(tail, '*.tdms'):
                    fileItem = self.tree.AppendItem(branch, tail)
                    self.tree.SetItemImage(fileItem, self.fileidx, wx.TreeItemIcon_Normal)
                    self.tree.SetItemData(fileItem, path)
                self.tree.SortChildren(branch)
            else:
                head, tail = os.path.split(path)
                newbranch = self.tree.AppendItem(branch, tail)
                self.tree.SetItemImage(newbranch, self.fldridx, wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(newbranch, self.fldropenidx, wx.TreeItemIcon_Expanded)

                self.tree.SetItemData(newbranch, path)
                self.tree.SortChildren(branch)

    def menuData(self):
        return (("&File",
                 ("&Update Tree", "Update Tree",self.OnTreeUpdate),
                 ("Update Paths", "Update Paths",self.OnPathUpdate),
                 ("&Quit", "Quit", self.OnCloseWindow)),
                ("&Merge",
                 ("Merge Wizard...", "Merge Files", self.OnMerge),
                 ("Convert TDMS to OBC for Merge...", "Convert TDMS Files", self.OnTDMStoOBC)),
                ("&Plot",
                 ("Overplot Tool...", "Overplot Files", self.OnPlot),
                 ("Overplot Tool (More plots)", "Overplot Files", self.OnPlotMore)),
                ("&Analysis",
                 ("Analyze Run...", "Analyze Run", self.OnAnalyze),
                 ("Beginning of Shift Runs", "Compare Beginning of Shift Runs", self.OnCompareBoS),
                 ("Extrema", "Extrema", self.OnExtrema)),
                ("&Data",
                 ("Extract Data...", "Extract Data", self.OnData)),
                ("&Help",
                 ("&About", "About Program", self.OnAbout)))

    def createMenuBar(self):
        menuBar = wx.MenuBar()
        for eachMenuData in self.menuData():
            menuLabel = eachMenuData[0]
            menuItems = eachMenuData[1:]
            menuBar.Append(self.createMenu(menuItems), menuLabel)
        self.SetMenuBar(menuBar)

    def createMenu(self, menuData):
        menu = wx.Menu()
        for eachLabel, eachStatus, eachHandler in menuData:
            if not eachLabel:
                menu.AppendSeperator()
                continue
            menuItem = menu.Append(-1, eachLabel, eachStatus)
            self.Bind(wx.EVT_MENU, eachHandler, menuItem)
        return menu

    def GetItemText(self, item):
        if item:
            return self.tree.GetItemText(item)
        else:
            return ""

    def OnItemExpanded(self, evt):
        pass

    def OnItemCollapsed(self, evt):
        pass

    def OnSelChanged(self, evt):
        try:
            self.statusbar.SetStatusText(self.tree.GetItemData(evt.GetItem()))
        except:
            pass
        wx.SetCursor(wx.Cursor(wx.CURSOR_ARROWWAIT))

        if not self.tree.ItemHasChildren(evt.GetItem()):
            if os.path.isdir(self.tree.GetItemData(evt.GetItem())):
                self.TreeBuilder(self.tree.GetItemData(evt.GetItem()), evt.GetItem())

        wx.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def OnActivated(self, evt):
        wx.SetCursor(wx.Cursor(wx.CURSOR_ARROWWAIT))

        try:
            runName = self.tree.GetItemData(evt.GetItem())
        except:
            runName = ""
        if os.path.isfile(runName):
            self.fname.SetValue(runName)
            
            # Here we open and process the run file
            runObj = plottools.get_run(runName)

            self.runObj = runObj

            self.title.SetValue(runObj.title)
            self.timestmp.SetValue(runObj.timestamp)
            self.nchans.SetValue(str(runObj.nchans))
            self.dt.SetValue(str(runObj.dt))
            self.stdbytime.SetValue(str(runObj.stdbytime))
            self.exectime.SetValue(str(runObj.exectime))

            self.chanList.Set([])
            self.chanList.InsertItems(runObj.chan_names, 0)
            self.chanList.SetSelection(0)

            self.xchanList.Set([])
            self.xchanList.InsertItems(runObj.chan_names,0)
            self.xchanList.InsertItems(['nTime'],0)
            self.xchanList.SetSelection(0)

            # Turn on the buttons as appropriate
            if runObj.filetype == 'AM-obc':
                self.calBtn.Enable(True)
            else:
                self.calBtn.Enable(False)
            self.dataBtn.Enable(True)
            self.dataBtnEU.Enable(True)
            self.graphBtn.Enable(True)
            self.graphBtnRaw.Enable(True)

        wx.SetCursor(wx.Cursor(wx.CURSOR_ARROW))

    def OnCalClick(self, evt):
        if self.runObj.nchans != 0:
            frame = CalFrame(self.runObj)
            frame.Show()

    def OnTreeUpdate(self, evt):
        """
            Rebuilds the file tree so it can take into account any changes to 
            the file structure that have occured
        """
        self.statusbar.SetStatusText('Working...')
        self.tree.DeleteChildren(self.obcroot)
        self.tree.DeleteChildren(self.tdmsroot)
        self.tree.DeleteChildren(self.stdroot)
        if self.fstroot:
            self.tree.DeleteChildren(self.fstroot)
        self.buildFileTree()
        self.statusbar.SetStatusText('Tree rebuilt')

    def OnDataClick(self, evt):
        frame = DataFrame(self.runObj)
        frame.Show()
        
    def OnDataEUClick(self, evt):
        frame = DataFrame(self.runObj, EU=True)
        frame.Show()

    def OnGraphClick(self, evt):
        chans = self.chanList.GetSelections()
        xchan = self.xchanList.GetSelection() - 1
        frame = CanvasFrame(self.runObj, chans, xchan, EU=True)
        frame.Show()
        
    def OnGraphRawClick(self, evt):
        chans = self.chanList.GetSelections()
        xchan = self.xchanList.GetSelection() - 1
        frame = CanvasFrame(self.runObj, chans, xchan, EU=False)
        frame.Show()

    def OnCloseWindow(self, event):
        self.Destroy()

    def OnMerge(self, event):
#        wizard = wx.wizard.Wizard(self, -1, "Merge Wizard", images.getWizTest1Bitmap())
        wizard = wx.wizard.Wizard(self, -1, "Merge Wizard")
        page1 = mergewiz.StartPage(wizard)
        page2 = mergewiz.SelectFilesPage(wizard)
        page3 = mergewiz.MrgDirPage(wizard)
        page4 = mergewiz.RunMrgPage(wizard)

        wx.wizard.WizardPageSimple_Chain(page1, page2)
        wx.wizard.WizardPageSimple_Chain(page2, page3)
        wx.wizard.WizardPageSimple_Chain(page3, page4)

        wizard.FitToPage(page1)

        wizard.RunWizard(page1)
        wx.MessageBox("Merge completed successfully", "That's all folks!")
        
    def OnTDMStoOBC(self, event):
        wizard = wx.wizard.Wizard(self, -1, "TDMS to OBC conversion", images.getWizTest1Bitmap())
        page1 = TDMStoOBCwiz.StartPage(wizard)
        page2 = TDMStoOBCwiz.SelectFilesPage(wizard)
        page3 = TDMStoOBCwiz.RunConvPage(wizard)
        
        wx.wizard.WizardPageSimple_Chain(page1, page2)
        wx.wizard.WizardPageSimple_Chain(page2, page3)

        wizard.FitToPage(page1)

        wizard.RunWizard(page1)
        wx.MessageBox("Conversion completed successfully", "That's all folks!")

    def OnPlot(self, event):
        frame = overplot.OverPlotFrame()
        frame.Show()

    def OnPlotMore(self, event):
        frame = overplot.OverPlotFrame(15)
        frame.Show()


    def OnAnalyze(self, event):
        frame = analysis.AnalysisFrame()
        frame.Show()

    def OnData(self, event): 
        pass 

    def OnPathUpdate(self,event):         
        frame = PathFrame()
        frame.Show()

    def OnCompareBoS(self, event):
        frame = CorrelateFrame()
        frame.Show()

    def OnAbout(self, event):
        dlg = ToolsAbout(self)
        dlg.ShowModal()
        dlg.Destroy()

    def OnExtrema(self, event):
        frame = extrema.ExtremaFrame()
        frame.Show()

class PathFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None,
                          title="Update Search Paths",
                          size=(600, 500))
        self.pathCtrl = wx.TextCtrl(self, -1, "",style=wx.TE_MULTILINE )  

        self.pathlist = open("defaultPaths.txt").read()
        self.pathCtrl.ChangeValue(self.pathlist)
        updateBtn = wx.Button(self, -1, "Update Paths")

        self.Bind(wx.EVT_BUTTON, self.OnPathWrite, updateBtn)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.pathCtrl, 4, wx.EXPAND, 0)
        mainSizer.Add(updateBtn, 0, wx.TOP|wx.ALIGN_CENTER_HORIZONTAL, 10)
        self.SetSizer(mainSizer)
        self.Layout()

    def OnPathWrite(self,event):
        self.pathlist = self.pathCtrl.GetValue()
        outfile = open("defaultPaths.txt", "w")
        outfile.write(self.pathlist)
        outfile.close()
        self.Destroy()


class DataFrame(wx.Frame):
    def __init__(self, runData, EU=False):
        wx.Frame.__init__(self, None,
                          title="Run Data  "+runData.filename,
                          size=(640,480))

        grid = wx.grid.Grid(self)
        table = DataTable(runData, EU)
        grid.SetTable(table, True)
        grid.AutoSizeColumns(True)
        #grid.SetDefaultColSize(80)

class CalFrame(wx.Frame):
    def __init__(self, runData):
        #file = open(r'.\lib\obc_channel_table.txt','w')

        wx.Frame.__init__(self, None,
                          title="Cal File Viewer   "+runData.filename,
                          size=(600, 500))

        columns = ['Ch. #', 'Name', 'Alt Name', 'Gain', 'Zero', 'Eng. Units']
        self.list = wx.ListCtrl(self, -1, style=wx.LC_REPORT|wx.LC_HRULES)
        for col, text in enumerate(columns):
            self.list.InsertColumn(col, text)

        #lines = []
        for item in range(runData.nchans):
            index = self.list.InsertItem(item, str(item))
            self.list.SetItem(index, 1, runData.chan_names[index])
            self.list.SetItem(index, 2, runData.alt_names[index])
            self.list.SetItem(index, 3, str(runData.gains[index]))
            self.list.SetItem(index, 4, str(runData.zeros[index]))
            self.list.SetItem(index, 5, str(runData.eng_units[index]))
            #lines.append(str(index)+' - '+runData.chan_names[index]+'\n')
        #file.writelines(lines)

        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(3, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(4, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(5, wx.LIST_AUTOSIZE)

class DataTable(wx.grid.GridTableBase):
    def __init__(self, runData, EU=False):
        wx.grid.GridTableBase.__init__(self)
        self.runData = runData
        self.EU = EU

    def GetNumberRows(self):
        return len(self.runData.data)

    def GetNumberCols(self):
        return self.runData.nchans

    def GetValue(self, row, col):
        if self.EU:
            value = self.runData.dataEU.iloc[row, col]
        else:
            value = self.runData.data.iloc[row, col]
        return value

    def IsEmptyCell(self, row, col):
        return False

    def SetValue(self, row, col, value):
        pass

    def GetColLabelValue(self, col):
        return self.runData.chan_names[col]

class ToolsAbout(wx.Dialog):
    text = '''
    <html>
    <body bgcolor="ACAA60">
    <center><table bgcolor="#455481" width="100%" cellspacing="0"
    cellpadding="0" border="1">
    <tr>
        <td align="center"><h1>AM Tools</h1></td>
    </tr>
    </table>
    </center>
    <p><b>AM Tools</b> is a package of tools for analyzing and manipulating
    data from the Autonomous Model </p>

    <p><b>Am Tools</b> is brought to you by Sam Cubbage, Copyright &copy; 2007.</p>
    </body>
    </html>
    '''

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About AM Tools', size=(440, 400) )

        html = wx.html.HtmlWindow(self)
        html.SetPage(self.text)
        button = wx.Button(self, wx.ID_OK, "Okay")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(button, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()


class App(wx.App):
    # Main app, derived from wx.App

    def OnInit(self):
        # Start with a splash screen, skip if the file can not be found
        try:
            bmp = wx.Image("./tool_img.png").ConvertToBitmap()
            wx.SplashScreen(bmp, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                            500, None, -1)
            wx.Yield()
        except:
            pass

       
        # Start the main app window
        frame = BrowserFrame()
        frame.Center()
        frame.Show()
        return True

if __name__ == "__main__":
    app = App(redirect = False)
    app.MainLoop()
