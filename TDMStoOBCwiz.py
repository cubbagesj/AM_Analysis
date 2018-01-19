#!/usr/bin/env python

import wx
import wx.lib.filebrowsebutton as filebrowse
import os
import wx.adv
import glob
from tdms_to_obc import tdmsToOBC

runsToConvert = []
if os.name == 'posix':
    tdmsDir = '/frmg/Autonomous_Model/Test_Data/'
    obcDir = '/frmg/Autonomous_Model/Test_Data/'
else:
    tdmsDir = 'C:/TDMS_Data'
    obcDir = 'C:/OBC_Data'


class StartPage(wx.adv.WizardPageSimple):
    def __init__(self, parent):
        wx.adv.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        titleText = wx.StaticText(self, -1, 'TDMS to OBC Wizard')
        titleText.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        self.sizer.Add(titleText, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(wx.StaticText(self, -1,"""
            This wizard guides you through the steps to convert the AM
            TDMS data into OBC files.  The merge puts the TDMS data into
            the appropriate OBC columns and creates the complimentary files
            needed to run the Merge process.
            
            You will need to have the appropriate configuration files in the same
            directory as the TDMS files you are converting.
            The configuration files are:
                tdms_to_obc.txt             - CSV file mapping TDMS channel names to OBC column numbers
                tdms_to_obc.gps             - .gps file needed to run merge (currently empty)
                tdms_to_obc.run             - .run file needed to run merge 
                tdms_to_obc_calfooter.txt   - footer text to add to cal file
                tdms_to_obc_calheader.txt   - header text to add to cal file
                tdms_to_obc_MERGE.INP       - .INP file needed to run merge
            
            The OBC data files and complimentary files (.cal, .gps, .run and .INP) will be put in
            C:\OBC_Data on windows systems and in /frmg/Autonomous_Model/Test_Data/ on linux systems
                """))
        
            
class SelectFilesPage(wx.adv.WizardPageSimple):
    def __init__(self, parent):
        if os.name == 'posix':
            self.dataDir = '/frmg/Autonomous_Model/Test_Data/'
        else:
            self.dataDir = 'C:/TDMS_Data'
            
        wx.adv.WizardPageSimple.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        titleText = wx.StaticText(self, -1, 'Select TDMS Files')
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
        tdmsfiles = []
        
        for file in glob.glob(os.path.join(self.dataDir,'*.tdms')):
            #head, tail = os.path.split(file)
            #name, ext = os.path.splitext(tail)
            tdmsfiles.append(file)
        return tdmsfiles
        
        
    def OnDirPick(self, evt):
        global tdmsDir
        self.dataDir = self.dirpick.GetPath()
        tdmsDir = self.dataDir
        runsToConvert = []
        self.fileList.Set(self.getFiles())
        
    def OnCheck(self, evt):
        global runsToConvert
        runsToConvert = []
        for item in range(self.fileList.GetCount()):
            if self.fileList.IsChecked(item):
                try:
                    runsToConvert.index(self.fileList.GetString(item))
                except:
                    runsToConvert.append(self.fileList.GetString(item))
                    
class RunConvPage(wx.adv.WizardPageSimple):
    def __init__(self, parent):
        wx.adv.WizardPageSimple.__init__(self, parent)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        
        titleText = wx.StaticText(self, -1, 'Run The Conversion')
        titleText.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))

        text1 = wx.StaticText(self, -1,
                              ' All Set!  Press the Button to run the Conversion.')

        convBtn = wx.Button(self, -1, 'Run Conversion')
        
        self.Bind(wx.EVT_BUTTON, self.OnConv, convBtn)
        
        self.sizer.Add(titleText, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.sizer.Add(wx.StaticLine(self, -1), 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(text1, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.sizer.Add(convBtn, 0, wx.ALIGN_CENTER | wx.ALL, 5)  
        
    def OnConv(self, evt):
        # Here is where we run the actual conversion.
        # The tdms directory is in the global tdmsDir.
        # The OBC directory is in the global obcDir. OBC files will be put here
        
        keepGoing = True
        count = 0
        
        for run in runsToConvert:
            if keepGoing:
                #runnum = run[4:]
                tdmsToOBC(run, obcDir)
            count += 1