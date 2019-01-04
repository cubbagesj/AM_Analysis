#!/usr/bin/env python
# clean_datafile.py
#
# Copyright (C) 2006-2018 - Samuel J. Cubbage
# 
#  This program is part of the Autonomous Model Software Tools Package
# 
"""
This class defines a tool frame that allows the user to blank out
selected columns in an STD datafile.  

This tool would be used to remove classified data from a standard
STD datafile so that the resulting file could be downgraded to unclassified
to put on the model.  

The primary use is for creating time history files
for correlation maneuvers but it could be used to create unclassified data files
to provide to others.

The tool keeps the structure of the data file and the original number of rows
and columns but zeros out the unwanted data.  It also allows for cleaning
the name of the file if required.

The tool creates an entirely new file instead of modifying and existing one to 
be sure that no data is hidden in the slack space.
"""
import os
import wx

import plottools as plottools

class CleanDataFrame(wx.Frame):
    
    def __init__(self, paths ):
        '''Initializes the frame and all the widgets.  
        '''
        wx.Frame.__init__(self, None, -1, 'Datafile Cleaning Tool', 
                          style=wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(wx.Colour("LIGHTGREY"))
        
        # Setup status bar
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText('Ready to Clean')
        
        # Map default paths
        self.defaultPaths = paths
        self.runsToMerge = []

        # decorate the frame with the widgets
        topLbl = wx.StaticText(self, -1, "Select File To Clean")
        topLbl.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        # Input file section
        self.fileText = wx.TextCtrl(self, -1, value="", 
                                    size=(400, -1))
        self.fileBtn = wx.Button(self, -1, "Pick File")
        self.Bind(wx.EVT_BUTTON, self.OnFileClick, self.fileBtn)

        # File display section
        displayLabel = wx.StaticText(self, -1, "File Information")
        displayLabel.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))

        self.headerText = wx.TextCtrl(self, -1, "", size=(200,100),
                                      style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        
 
        # Run Merge Button
        cleanBtn = wx.Button(self, -1, "Clean File")
        cleanBtn.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.Bind(wx.EVT_BUTTON, self.OnCleanClick, cleanBtn)

        # Set up the layout with sizers
        
        # Main Title
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(topLbl, 0, wx.ALL, 5)
        
        # File selection section
        fileSizer = wx.BoxSizer(wx.HORIZONTAL)
        fileSizer.Add(self.fileBtn, 0, wx.ALL, 5)
        fileSizer.Add(self.fileText, 0, wx.ALL, 5)
        mainSizer.Add(fileSizer, 0, wx.EXPAND|wx.ALL, 10)

        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)

        mainSizer.Add(displayLabel, 0, wx.EXPAND|wx.ALL, 10)
        mainSizer.Add(self.headerText, 0, wx.EXPAND|wx.ALL,10)
        
        #Setup for channel entry
        chanLbl = wx.StaticText(self, -1, "Channel")
        self.chanList = wx.ListBox(self, -1, 
                                   style=wx.LB_SINGLE, name="Channel")
        nameLbl = wx.StaticText(self, -1, "New Name")
        self.newName = wx.TextCtrl(self, -1, "")
        
        scaleLbl = wx.StaticText(self, -1, "Scale")
        self.newScale = wx.TextCtrl(self, -1, "1.0")

        self.mapBtn = wx.Button(self, -1, "Add Channel")
        self.Bind(wx.EVT_BUTTON, self.OnAddClick, self.mapBtn)

        #Setup for Mapping info
        self.mapInfo = wx.TextCtrl(self, -1, "", size=(300, 300),
                                   style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER )
        
        # Sizer for channel Input
        chanSizer = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
        chanSizer.Add(chanLbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        chanSizer.Add(self.chanList, 0)
        chanSizer.Add(nameLbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        chanSizer.Add(self.newName, 0, wx.EXPAND)
        chanSizer.Add(scaleLbl, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        chanSizer.Add(self.newScale, 0, wx.EXPAND)
        
        # Sizer for Channel Mapping
        mapSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label='Output Map')
        mapSizer.Add(self.mapInfo, 0, wx.EXPAND)
        
        
        # Create sizer for channel information
        configSizer = wx.StaticBoxSizer(wx.VERTICAL,self, label='Channel Input')
        configSizer.Add(chanSizer, 0, wx.LEFT)
        configSizer.Add(self.mapBtn, 0, wx.EXPAND)
        
        groupSizer = wx.BoxSizer(wx.HORIZONTAL)
        groupSizer.Add(configSizer, 0, wx.LEFT, 5)
        groupSizer.Add(mapSizer, 0, wx.RIGHT, 5)
              
        mainSizer.Add(groupSizer, 0, wx.LEFT, 5)

        mainSizer.Add((20,20), 0)
       
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        mainSizer.Add(cleanBtn, 0, wx.EXPAND|wx.ALL, 5)
        
        self.SetSizer(mainSizer)
        self.Fit()
        

    def OnFileClick(self, evt):
        dlg = wx.FileDialog(self, "Choose file to clean...",
                                defaultDir=".", wildcard="*.*",
                                style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.inputFile = dlg.GetPath()
            self.fileText.SetValue(dlg.GetFilename())
        dlg.Destroy()
        
        # Clear the current header info
        self.headerText.ChangeValue("")
        # Open the file and read in the header info
        f = open(self.inputFile, 'r')
        for x in range(4):
            self.headerText.write(f.readline())
        f.close()
        
        # Now pull in the whole file
        self.runObj = plottools.get_run(self.inputFile)
        
        self.chanList.Set([])
        self.chanList.InsertItems(self.runObj.chan_names, 0)
        self.chanList.SetSelection(0)
        
    def OnCleanClick(self, evt):
        """
            Get the values from the dialog box and create the plot
            with a call to mplt in the plottools module
        """
        # Start by getting the mapping info
        
        oldNames = []
        newNames = []
        newScales = []
        
        for i in range(self.mapInfo.GetNumberOfLines()):
            try:
                oldName, newName, newScale = self.mapInfo.GetLineText(i).split(',')
            except:
                pass
            oldNames.append(oldName)
            newNames.append(newName)
            newScales.append(newScale)
            
        # Now open an output file - append 'clean' to original
        cleanFile = open(self.inputFile + 'clean', 'w')
        
        # Write the header info
        cleanFile.write(self.headerText.GetValue() + '\n')
        
        # Now apply the mapping
        for channel in self.runObj.chan_names:
            try:
                idx = oldNames.index(channel)
                # Channel in map list so process
                self.runObj.dataEU[channel] *= float(newScales[idx])
                cleanFile.write("%s " % newNames[idx])
            except:
                self.runObj.dataEU[channel] *= 0.0
                cleanFile.write("%s " % channel)

        self.runObj.dataEU.to_csv(cleanFile, index=False, header=False, sep=' ', float_format='%12.7e')
        
        
        cleanFile.close()
        
        
               
    def OnAddClick(self, evt):
        """
            Add a channel to the output mapping list
        """
        
        # Get the information from the channel boxes
        orgName = self.chanList.GetString(self.chanList.GetSelection())
        newName = self.newName.GetLineText(0)
        newScale = self.newScale.GetLineText(0)
        
        self.mapInfo.write("%s, %s, %s \n" % (orgName, newName, newScale))
        
        
        