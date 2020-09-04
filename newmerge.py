#!/usr/bin/env python
# newmerge.py
#
# Copyright (C) 2006-2018 - Samuel J. Cubbage
# 
#  This program is part of the Autonomous Model Software Tools Package
# 
"""
This class defines an merge frame that allows user set up a file merge

Provides input fields to select directories and filenames
"""
import os, glob
import wx
import wx.grid, wx.html
from tdms_to_obc import tdmsToOBC 

from am_merge_array import MergeRun

class MergeFrame(wx.Frame):
    
    def __init__(self, paths ):
        '''Initializes the frame and all the widgets.  
        '''
        wx.Frame.__init__(self, None, -1, 'Merge', style=wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(wx.Colour("LIGHTGREY"))
        
        # Setup status bar
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText('Ready to Merge')
        
        # Map default paths
        self.defaultPaths = paths
        self.runsToMerge = []

        # decorate the frame with the widgets
        topLbl = wx.StaticText(self, -1, "Merge Runs")
        topLbl.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        # Merge input file section
        fileLabel = wx.StaticText(self, -1, "Merge Input File:")
        self.fileText = wx.TextCtrl(self, -1, value="", 
                                    size=(200, -1))
        self.fileBtn = wx.Button(self, -1, "Pick File")
        self.Bind(wx.EVT_BUTTON, self.OnFileClick, self.fileBtn)

        runLabel = wx.StaticText(self, -1, "Select Files to Merge")
        runLabel.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))

        stdLabel = wx.StaticText(self, -1, "Select STD Location")
        stdLabel.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        # File selector
        self.dirpick = wx.DirPickerCtrl(self, -1, 
                                        path=self.defaultPaths['obcDir'], 
                                        message="Choose Directory")
        self.fileList = wx.CheckListBox(self, -1, 
                                        size=(200,150), 
                                        style=wx.LB_MULTIPLE)

        self.Bind(wx.EVT_DIRPICKER_CHANGED,  self.OnDirPick, self.dirpick)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck, self.fileList) #AFP Updated onCheck function


        self.mrgdirpick = wx.DirPickerCtrl(self, -1, 
                                           path=self.defaultPaths['stdDir'], 
                                           message="Choose Directory",
                                           style=wx.DIRP_USE_TEXTCTRL)
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnMrgDirPick, self.mrgdirpick)
 
        # Run Merge Button
        mergeBtn = wx.Button(self, -1, "Run Merge")
        mergeBtn.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.Bind(wx.EVT_BUTTON, self.OnMergeClick, mergeBtn)

        # Set up the layout with sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(topLbl, 0, wx.ALL, 5)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        
        fileSizer = wx.BoxSizer(wx.HORIZONTAL)
        fileSizer.Add(fileLabel, 0, wx.ALL, 5)
        fileSizer.Add(self.fileText, 0, wx.ALL, 5)
        fileSizer.Add(self.fileBtn, 0, wx.ALL, 5)
        mainSizer.Add(fileSizer, 0, wx.EXPAND|wx.ALL, 10)

        mainSizer.Add(runLabel, 0, wx.EXPAND|wx.ALL, 10)

        fileSizer2 = wx.FlexGridSizer(cols=1, hgap=5, vgap=5)
        fileSizer2.AddGrowableCol(0)
        fileSizer2.Add(self.dirpick, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        fileSizer2.Add(self.fileList, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        fileSizer2.Add(stdLabel, 0, wx.EXPAND|wx.ALL, 10)
        fileSizer2.Add(self.mrgdirpick, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        mainSizer.Add(fileSizer2, 0, wx.EXPAND|wx.ALL, 10)

        mainSizer.Add((20,20), 0)
       
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        mainSizer.Add(mergeBtn, 0, wx.EXPAND|wx.ALL, 5)
        
        self.SetSizer(mainSizer)
        self.Fit()
        

    def OnFileClick(self, evt):
        dlg = wx.FileDialog(self, "Open merge input file...",
                                defaultDir="/home/pi/Documents/Merge_Files", wildcard="*.*",
                                style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.MergeCfg = dlg.GetPath()
            self.fileText.SetValue(dlg.GetFilename())
        dlg.Destroy()
    
        
    def OnMergeClick(self, evt):
        """
            Get the values from the dialog box and create the plot
            with a call to mplt in the plottools module
        """
        currdir = os.getcwd()
        os.chdir(self.dataDir)
        count = 0
        for run in self.runsToMerge:
            # Split file into name and extenson
            OrigFileName, FileType = run.split(".") 
            # Remove space after underslash in tdms file
            FileName = OrigFileName.replace(" ","") 
            self.runnum = FileName[4:] 
            self.FilePath = os.path.join(self.dataDir,run) 
                
            self.statusbar.SetStatusText('Merging run: %s -----> ' % self.runnum )
            wx.Yield()
            try:
                MergeRun(self.FilePath, int(self.runnum), self.mrgDir, self.MergeCfg)                     
            except:
                raise

            count += 1
        self.statusbar.SetStatusText('Merge Complete!')
        os.chdir(currdir)
         
    def OnDirPick(self, evt):
        self.dataDir = self.dirpick.GetPath()
        self.fileList.Set(self.getFiles())
        
    def OnCheck(self, evt):
        self.runsToMerge = []
        for item in range(self.fileList.GetCount()):  
            if self.fileList.IsChecked(item): 
                try:
                    self.runsToMerge.index(self.fileList.GetString(item))
                except:
                    self.runsToMerge.append(self.fileList.GetString(item))
            else: #AFP Remove the item from fileList if it is unchecked
                try:
                    self.runsToMerge.remove(self.fileList.GetString(item))
                except:
                    continue
                  
    def getFiles(self):
        obctdmsfiles = [] # now also includes TDMS files

        for file in glob.glob(os.path.join(self.dataDir,'*.obc')):
            head, tail = os.path.split(file)
            obctdmsfiles.append(tail)

        for file in glob.glob(os.path.join(self.dataDir,'*.tdms')): #AFP added search for TDMS files
            head, tail = os.path.split(file)
            obctdmsfiles.append(tail) #AFP Display extension since there will now be TDMS files

        return obctdmsfiles


    def OnMrgDirPick(self, evt):
        self.mrgDir = self.mrgdirpick.GetPath()
