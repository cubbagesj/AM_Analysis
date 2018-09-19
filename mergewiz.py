#!/usr/bin/env python

import wx
import os
import wx.adv
import glob


from am_merge_array import MergeRun

from tdms_to_obc import tdmsToOBC #AFP - Initially use Woody's file tdms_to_obc converter to handle the TDMS file

runsToMerge = []
if os.name == 'posix':
    obcDir = '/frmg/Autonomous_Model/Test_Data/' #AFP Also TDMS Directory
    mrgDir = ''
else:
    obcDir = 'C:/OBC_Data' #AFP Also TDMS Directory
    mrgDir = 'C:/STD_Data'


class StartPage(wx.adv.WizardPageSimple):
    def __init__(self, parent):
        wx.adv.WizardPageSimple.__init__(self, parent)
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
        
            
class SelectFilesPage(wx.adv.WizardPageSimple):
    def __init__(self, parent):
        if os.name == 'posix':
            self.dataDir = '/frmg/Autonomous_Model/Test_Data/'
        else:
            self.dataDir = 'C:/OBC_Data'
            
            
        wx.adv.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        titleText = wx.StaticText(self, -1, 'Select OBC or TDMS Files')
        titleText.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        self.dirpick = wx.DirPickerCtrl(self, -1, path=self.dataDir, message="Choose Directory")
        self.dirpick.SetTextCtrlGrowable(grow=True)
        self.dirpick.SetTextCtrlProportion(1)
        self.dirpick.SetPickerCtrlProportion(0)
        self.fileList = wx.CheckListBox(self, -1, size=(200,150), style=wx.LB_MULTIPLE)

        self.Bind(wx.EVT_DIRPICKER_CHANGED,  self.OnDirPick, self.dirpick)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck, self.fileList) #AFP Updated onCheck function
        
        fileSizer = wx.FlexGridSizer(cols=1, hgap=5, vgap=5)
        fileSizer.AddGrowableCol(0)
        fileSizer.Add(self.dirpick, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        fileSizer.Add(self.fileList, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
       
        self.sizer.Add(titleText, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(fileSizer, 0, wx.EXPAND|wx.ALL, 5)
        
        self.fileList.Set(self.getFiles())
        
    def getFiles(self):
        obctdmsfiles = [] #AFP now also includes TDMS files
        for file in glob.glob(os.path.join(self.dataDir,'*.obc')):
            head, tail = os.path.split(file)
            obctdmsfiles.append(tail)
        for file in glob.glob(os.path.join(self.dataDir,'*.tdms')): #AFP added search for TDMS files
            head, tail = os.path.split(file)
            obctdmsfiles.append(tail) #AFP Display extension since there will now be TDMS files
        return obctdmsfiles
        
    def OnDirPick(self, evt):
        global obcDir
        self.dataDir = self.dirpick.GetPath()
        obcDir = self.dataDir
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
            else: #AFP Remove the item from fileList if it is unchecked
                try:
                    runsToMerge.remove(self.fileList.GetString(item))
                except:
                    continue
                    
class MrgDirPage(wx.adv.WizardPageSimple):
    def __init__(self, parent):

        if os.name == 'posix':
            self.mrgDir = '/dsk2/home/'+os.environ['USER']+'/rcmdata'
            self.mrgInpDir = '/frmg/Autonomous_Model/Test_Data/Merge_Files/'
        else:
            self.mrgDir = 'C:/STD_Data'
            
            self.mrgInpDir = 'C:/OBC_Data/merge.inp' #AFP Updated to show a file as a default, not just a directory
            
        wx.adv.WizardPageSimple.__init__(self, parent)
        
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

        self.mrgInput = wx.CheckBox(self,-1,'Use Individually Generated TDMS Merge Input Files?',(20,200)) #AFP Defaults to MERGE.INP in directory of OBC file if this is checked and an OBC file is being merged.

        inpLabel = wx.StaticText(self, -1, 'Merge Configuration File')
        
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnMrgDirPick, self.mrgdirpick)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.OnMrgInpDirPick, self.mrginpdirpick)
        self.Bind(wx.EVT_CHECKBOX, self.OnInpCheck, self.mrgInput) #AFP Updated onCheck function

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

    def OnInpCheck(self, evt):
        if self.mrgInput.IsChecked():
            self.mrginpdirpick.Disable()
        else:         
            self.mrginpdirpick.Enable()

class RunMrgPage(wx.adv.WizardPageSimple):
    def __init__(self, parent):
        wx.adv.WizardPageSimple.__init__(self, parent)

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
        count = 0
        for run in runsToMerge:
            OrigFileName, FileType = run.split(".") #AFP Split file into name and extension
            FileName = OrigFileName.replace(" ","") #AFP Remove space after underslash in tdms file, does nothing for OBC file
            self.runnum = FileName[4:] #AFP
            self.FilePath = os.path.join(obcDir,run) #AFP
            if FileType.lower() == 'tdms':
                self.tdmsMerge()
            else:
                MergeRun(self.FilePath, int(self.runnum), mrgDir, inpDir)                     
            count += 1
        os.chdir(currdir)
        
    def tdmsMerge(self):
        tdmsToOBC(self.FilePath, obcDir) #Check to see if the the file we are merging is a TDMS file or an OBC file using the IsTDMSFile input. If it
                                    #is a TDMS file, use Woody's converter to handle it. If it is an OBC file, proceed as normal.
        tdmsinpDir = os.path.join(obcDir,'run-'+self.runnum+'_MERGE.INP')
        MergeRun(int(self.runnum), mrgDir, tdmsinpDir) #AFP Added filepath and filetype inputs to check if TDMS file
        #AFP Now delete files generated from TDMS conversion, since they are not needed.        
        os.remove(os.path.join(obcDir,'run-'+self.runnum+'.cal'))
        os.remove(os.path.join(obcDir,'run-'+self.runnum+'.gps'))
        os.remove(os.path.join(obcDir,'run-'+self.runnum+'.obc'))               
        os.remove(os.path.join(obcDir,'run-'+self.runnum+'.run'))                
        os.remove(os.path.join(obcDir,'run-'+self.runnum+'_MERGE.INP'))
