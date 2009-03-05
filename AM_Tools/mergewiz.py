#!/usr/bin/env python

import wx
import os
import wx.wizard
import glob

from am_merge import MergeRun

runsToMerge = []
mrgDir = ''
obcDir = '//alpha1/DISK51/CB09/OBC'


class StartPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent):
        wx.wizard.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        titleText = wx.StaticText(self, -1, 'Merge Wizard')
        titleText.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        self.sizer.Add(titleText, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(wx.StaticText(self, -1,"""
            This wizard guides you through the steps to convert the AM
            OBC data into standard format STD files.  The merge converts
            the data to full-scale units, places it in the correct columns
            and handles all of the computed channels like the prop dyno."""))
        
            
class SelectFilesPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent):
        self.dataDir = '//alpha1/DISK51/CB09/OBC'
        
        wx.wizard.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        titleText = wx.StaticText(self, -1, 'Select OBC Files')
        titleText.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        self.radio1 = wx.RadioBox(self, -1, "Centerbody", choices=['CB 8', 'CB 9', 'CB A'],
                    majorDimension=1, style=wx.RA_SPECIFY_COLS)
        
        self.radio1.SetSelection(1) 
        self.fileList = wx.CheckListBox(self, -1, style=wx.LB_MULTIPLE)

        self.Bind(wx.EVT_RADIOBOX, self.OnRadio)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck, self.fileList)
        
        fileSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        fileSizer.AddGrowableCol(1)
        fileSizer.Add(self.radio1, 0, wx.ALIGN_CENTER_VERTICAL)
        fileSizer.Add(self.fileList, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
       
        self.sizer.Add(titleText, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(fileSizer, 0, wx.EXPAND|wx.ALL, 5)
        
        self.fileList.Set(self.getFiles())
        
        
    def getFiles(self):
        obcfiles = []
        
        for file in glob.glob(os.path.join(self.dataDir,'*.obc')):
            head, tail = os.path.split(file)
            name, ext = os.path.splitext(tail)
            obcfiles.append(name)
        return obcfiles
        
        
    def OnRadio(self, evt):
        global obcDir
        if self.radio1.GetSelection() == 0:
            self.dataDir = '//alpha1/DISK51/CB08/OBC'
        elif self.radio1.GetSelection() == 1:
            self.dataDir = '//alpha1/DISK51/CB09/OBC'
        elif self.radio1.GetSelection() == 2:
            self.dataDir = '//alpha1/DISK51/CB0A/OBC'
        obcDir = self.dataDir
        runsToMerge = []
        self.fileList.Set(self.getFiles())
        
    def OnCheck(self, evt):
        global runsToMerge
        runsToMerge = []
        for item in range(self.fileList.GetCount()):
            if self.fileList.IsChecked(item):
                try:
                    runsToMerge.index(self.fileList.GetString(item))
                except:
                    runsToMerge.append(self.fileList.GetString(item))


class MrgDirPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent):
        wx.wizard.WizardPageSimple.__init__(self, parent)
        
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        
        titleText = wx.StaticText(self, -1, 'Enter Merge Directory')
        titleText.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        self.dirBox = wx.TextCtrl(self, -1, "")
        
        self.Bind(wx.EVT_TEXT, self.OnText, self.dirBox)

        self.sizer.Add(titleText, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(self.dirBox, 0, wx.EXPAND|wx.ALL, 5)
        
    def OnText(self, evt):
        global mrgDir
        mrgDir = self.dirBox.GetValue()

class RunMrgPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent):
        wx.wizard.WizardPageSimple.__init__(self, parent)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        
        titleText = wx.StaticText(self, -1, 'Run The Merge')
        titleText.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))

        text1 = wx.StaticText(self, -1,
                              ' All Set!  Press the Button to run the Merge.')

        mrgBtn = wx.Button(self, -1, 'Run Merge')
        
        self.Bind(wx.EVT_BUTTON, self.OnMerge, mrgBtn)
        
        self.sizer.Add(titleText, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(text1, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.sizer.Add(mrgBtn, 0, wx.ALIGN_CENTER | wx.ALL, 5)  
        
    def OnMerge(self, evt):
        # Here is where we run the actual merge.
        # The obc directory is in the global obcdir.  Run the merge from here
        currdir = os.getcwd()
        os.chdir(obcDir)
        
        keepGoing = True
        count = 0
        
        for run in runsToMerge:
            if keepGoing:
                runnum = run[4:]
                MergeRun(int(runnum), mrgDir)
            count += 1
        os.chdir(currdir)
        
