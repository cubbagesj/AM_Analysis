#!/usr/bin/env python
# Run_Browser.py
#
# Copyright (C) 2007 - Samuel J. Cubbage
#
# This program is part of the Autonomous Model Software Tools Package
#
# a wxPython program to browse the run files and display info about each run

# 3/23/2007

import wx
import wx.grid, wx.html
import os
import fnmatch
from plotcanvas import CanvasFrame
from multicanvas import MultiCanvasFrame
import tools.plottools as plottools
import images
import mergewiz
import overplot
import analysis

class BrowserFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Run File Browser", size=(800,550))
        
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
                
        chanList = wx.StaticText(panel, -1, "Channel List:")
        self.chanList = wx.ListBox(panel, -1, size=(150,180),
                                   style=wx.LB_EXTENDED, name="Channel List")
        
        # The buttons
        self.calBtn = wx.Button(panel, -1, "View CAL File")
        self.calBtn.Enable(False)
        self.dataBtn = wx.Button(panel, -1, "View Data")
        self.dataBtn.Enable(False)
        self.graphBtn = wx.Button(panel, -1, "Quick Graph")
        self.graphBtn.Enable(False)
        
        #Button Events
        self.Bind(wx.EVT_BUTTON, self.OnCalClick, self.calBtn)
        self.Bind(wx.EVT_BUTTON, self.OnDataClick, self.dataBtn)
        self.Bind(wx.EVT_BUTTON, self.OnGraphClick, self.graphBtn)
        
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
        infoSizer.Add(self.chanList, 0, wx.LEFT|wx.RIGHT)
              
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20), 1)
        btnSizer.Add(self.calBtn)
        btnSizer.Add((20,20), 1)
        btnSizer.Add(self.dataBtn)
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
              
        sizer=wx.GridSizer()
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
        obcroot = self.tree.AppendItem(root, "OBC Files")
        self.tree.SetItemImage(obcroot, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(obcroot, self.fldropenidx, wx.TreeItemIcon_Expanded)


        # Add nodes from our data set
        rootDir = r'\\skipjack\FRMG\Autonomous_Model\test_data'
        self.TreeBuilder(rootDir, obcroot)

        # Add a root node for STD File
        stdroot = self.tree.AppendItem(root, "STD Files")
        self.tree.SetItemImage(stdroot, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(stdroot, self.fldropenidx, wx.TreeItemIcon_Expanded)

        # Add nodes from our data set
        rootDir = r'\\alpha1\DISK31'
        if os.path.exists(rootDir):
            self.TreeBuilder(rootDir, stdroot)
        rootDir = r'\\alpha1\DISK72\RCMMRG-S23'
        if os.path.exists(rootDir):
            self.TreeBuilder(rootDir, stdroot)

        # Add a root node for FST Files
        fstroot = self.tree.AppendItem(root, "FST Files")
        self.tree.SetItemImage(fstroot, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(fstroot, self.fldropenidx, wx.TreeItemIcon_Expanded)

        # Add nodes from our data set
        rootDir = r'\\alpha1\FSTDATA'
        if os.path.exists(rootDir):
            self.TreeBuilder(rootDir, fstroot)

        # Bind some interesting events
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed, self.tree)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated, self.tree)

        # Expand the first level
        self.tree.Expand(root)
        
    def TreeBuilder(self, currdir, branch):
        for file in os.listdir(currdir):
            path = os.path.join(currdir, file)
            if not os.path.isdir(path):
                head, tail = os.path.split(path)
                if fnmatch.fnmatch(tail, '*.obc') or fnmatch.fnmatch(tail, '*.std'):
                    fileItem = self.tree.AppendItem(branch, tail)
                    self.tree.SetItemImage(fileItem, self.fileidx, wx.TreeItemIcon_Normal)
                    self.tree.SetItemPyData(fileItem, path)
                self.tree.Expand(branch)
                self.tree.SortChildren(branch)
            else:
                head, tail = os.path.split(path)
                newbranch = self.tree.AppendItem(branch, tail)
                self.tree.SetItemImage(newbranch, self.fldridx, wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(newbranch, self.fldropenidx, wx.TreeItemIcon_Expanded)
                
                self.tree.SetItemPyData(newbranch, path)
                self.tree.SortChildren(branch)
                self.tree.Expand(branch)
                
    def menuData(self):
        return (("&File",
                 ("&Quit", "Quit", self.OnCloseWindow)),
                ("&Merge",
                 ("Merge Wizard...", "Merge Files", self.OnMerge)),
                ("&Plot",
                 ("Overplot Tool...", "Overplot Files", self.OnPlot)),
                ("&Analysis",
                 ("Analyze Run...", "Analyze Run", self.OnAnalyze)),
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
            self.statusbar.SetStatusText(self.tree.GetItemPyData(evt.GetItem()))
        except:
            pass
        wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROWWAIT))

        if not self.tree.ItemHasChildren(evt.GetItem()):
            if os.path.isdir(self.tree.GetItemPyData(evt.GetItem())):
                self.TreeBuilder(self.tree.GetItemPyData(evt.GetItem()), evt.GetItem())

        wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

    def OnActivated(self, evt):
        wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROWWAIT))
        
        try:
            runName = self.tree.GetItemPyData(evt.GetItem())
        except:
            runName = ""
        if os.path.isfile(runName):
            self.fname.SetValue(runName)
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
            
            # Turn on the buttons as appropriate
            if runObj.filetype == 'AM-obc':
                self.calBtn.Enable(True)
            else:
                self.calBtn.Enable(False)
            self.dataBtn.Enable(True)
            self.graphBtn.Enable(True)

        wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
    
    def OnCalClick(self, evt):
        if self.runObj.nchans != 0:
            frame = CalFrame(self.runObj)
            frame.Show()

    def OnDataClick(self, evt):
        frame = DataFrame(self.runObj)
        frame.Show()

    def OnGraphClick(self, evt):
        chans = self.chanList.GetSelections()
        frame = CanvasFrame(self.runObj, chans)
        frame.Show()
    
    def OnCloseWindow(self, event):
        self.Destroy()
    
    def OnMerge(self, event):
        wizard = wx.wizard.Wizard(self, -1, "Merge Wizard", images.getWizTest1Bitmap())
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
        
        
    def OnPlot(self, event):
        frame = overplot.OverPlotFrame()
        frame.Show()
        
    def OnAnalyze(self, event):
        frame = analysis.AnalysisFrame()
        frame.Show()
               
    def OnData(self, event): pass
    
    def OnAbout(self, event):
        dlg = ToolsAbout(self)
        dlg.ShowModal()
        dlg.Destroy()
        
class DataFrame(wx.Frame):
    def __init__(self, runData):
        wx.Frame.__init__(self, None,
                          title="Run Data  "+runData.filename,
                          size=(640,480))
        
        grid = wx.grid.Grid(self)
        table = DataTable(runData)
        grid.SetTable(table, True)
        grid.SetDefaultColSize(80)
        
class CalFrame(wx.Frame):
    def __init__(self, runData):
        wx.Frame.__init__(self, None,
                          title="Cal File Viewer   "+runData.filename,
                          size=(600, 500))
                
        columns = ['Ch. #', 'Name', 'Alt Name', 'Gain', 'Zero', 'Eng. Units']
        self.list = wx.ListCtrl(self, -1, style=wx.LC_REPORT|wx.LC_HRULES)
        for col, text in enumerate(columns):
            self.list.InsertColumn(col, text)
        
        for item in range(runData.nchans):
            index = self.list.InsertStringItem(item, str(item))
            self.list.SetStringItem(index, 1, runData.chan_names[index])
            self.list.SetStringItem(index, 2, runData.alt_names[index])
            self.list.SetStringItem(index, 3, str(runData.gains[index]))
            self.list.SetStringItem(index, 4, str(runData.zeros[index]))
            self.list.SetStringItem(index, 5, str(runData.eng_units[index]))
            
        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE_USEHEADER)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(3, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(4, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(5, wx.LIST_AUTOSIZE)
        
class DataTable(wx.grid.PyGridTableBase):
    def __init__(self, runData):
        wx.grid.PyGridTableBase.__init__(self)
        self.runData = runData
        
    def GetNumberRows(self):
        return len(self.runData.data)
    
    def GetNumberCols(self):
        return self.runData.nchans
    
    def GetValue(self, row, col):
        value = self.runData.data[row][col]
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
            bmp = wx.Image("./lib/tool_img.png").ConvertToBitmap()
            wx.SplashScreen(bmp, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                    500, None, -1)
            wx.Yield()
        except:
            pass

        # Start the main app window
        frame = BrowserFrame()
        frame.Show()
        return True
    
if __name__ == "__main__":
    app = App(redirect = False)
    app.MainLoop()
