#!/usr/bin/env python

import wx
import wx.lib.filebrowsebutton as filebrowse
import os
import wx.wizard
import glob

from am_merge import MergeRun

runsToMerge = []
mrgDir = ''
obcDir = '/frmg/Autonomous_Model/Test_Data'


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
            and handles all of the computed channels such as the prop dyno."""))
        
            
class SelectFilesPage(wx.wizard.WizardPageSimple):
    def __init__(self, parent):
        self.dataDir = '/frmg/Autonomous_Model/Test_Data/'
        
        wx.wizard.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        titleText = wx.StaticText(self, -1, 'Select OBC Files')
        titleText.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        self.dirpick = wx.DirPickerCtrl(self, -1, path=self.dataDir, message="Choose Directory")
        self.dirpick.SetTextCtrlGrowable(grow=True)
        self.dirpick.SetTextCtrlProportion(1)
        self.dirpick.SetPickerCtrlProportion(0)
        self.fileList = wx.CheckListBox(self, -1, size=(200,200), style=wx.LB_MULTIPLE)

        self.Bind(wx.EVT_DIRPICKER_CHANGED,  self.OnDirPick, self.dirpick)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck, self.fileList)
        
        fileSizer = wx.FlexGridSizer(cols=1, hgap=5, vgap=5)
        fileSizer.AddGrowableCol(0)
        fileSizer.Add(self.dirpick, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
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
        
        
    def OnDirPick(self, evt):
        global obcDir
        self.dataDir = self.dirpick.GetPath()
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

        self.mrgDir = '/disk2/home/'+os.environ['USER']+'/rcmdata'
        self.mrgInpDir = '/disk2/home/'+os.environ['USER']+'/obcdata/Merge_Files/'
        self.mrgInpDir = '/frmg/Autonomous_Model/Test_Data/Merge_Files/'
        wx.wizard.WizardPageSimple.__init__(self, parent)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        
        titleText = wx.StaticText(self, -1, 'Enter Merge Information')
        titleText.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))

        self.mrgdirpick = wx.DirPickerCtrl(self, -1, path=self.mrgDir, message="Choose Directory",
                        style=wx.DIRP_USE_TEXTCTRL)
        self.mrgdirpick.SetTextCtrlGrowable(grow=True)
        self.mrgdirpick.SetTextCtrlProportion(1)
        self.mrgdirpick.SetPickerCtrlProportion(0)
        
        dirLabel = wx.StaticText(self, -1, 'Merge Directory')
        
        self.mrginpdirpick = wx.FilePickerCtrl(self, -1, path=self.mrgInpDir, message="Choose Merge File",
                        style=wx.DIRP_USE_TEXTCTRL)
        self.mrginpdirpick.SetTextCtrlGrowable(grow=True)
        self.mrginpdirpick.SetTextCtrlProportion(1)
        self.mrginpdirpick.SetPickerCtrlProportion(0)

        inpLabel = wx.StaticText(self, -1, 'Merge Configuration File')
        
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnMrgDirPick, self.mrgdirpick)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnMrgInpDirPick, self.mrginpdirpick)
        

        self.sizer.Add(titleText, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(dirLabel, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.sizer.Add(self.mrgdirpick, 0, wx.EXPAND|wx.ALL, 5)
        self.sizer.Add(inpLabel, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.sizer.Add(self.mrginpdirpick, 0, wx.EXPAND|wx.ALL, 5)
        

    def OnMrgDirPick(self, evt):
        global mrgDir
        mrgDir = self.mrgdirpick.GetPath()
    
    def OnMrgInpDirPick(self, evt):
        global inpDir
        inpDir = self.mrginpdirpick.GetPath()

    def OnInpBtn(self, evt):
        dlg = wx.FileDialog(self, "Open Merge Input File...", obcDir,
                            style=wx.OPEN, wildcard='*.INP')
        if dlg.ShowModal() == wx.ID_OK:
            inpDir = dlg.GetFilename()
        self.inpBox.SetValue(inpDir)

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
        
        password = ''

        currdir = os.getcwd()
        os.chdir(obcDir)
        
        keepGoing = True
        count = 0
        
        for run in runsToMerge:
            if keepGoing:
                runnum = run[4:]
                MergeRun(int(runnum), mrgDir, inpDir, password)
            count += 1
        os.chdir(currdir)
        
