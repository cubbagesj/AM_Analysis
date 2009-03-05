#!/usr/bin/env python
# analysis.py
#
# Copyright (C) 2006-2007 - Samuel J. Cubbage
# 		          - Anthony Constable
# 
#  This program is part of the Autonomous Model Software Tools Package
# 
"""
This class defines an Analysis frame that allows user to analyze
model data.  The frame can be standalone or is normally
called from the AM_tools utility

"""

import wx
import os
import math

from tools.plottools import *
from multicanvas import MultiCanvasFrame


class AnalysisFrame(wx.Frame):
    
    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'AM Analysis',size=(600,700))
        self.SetBackgroundColour(wx.NamedColor("LIGHTGREY"))

        self.dataList = [['U pw', 6],
                    ['U adcp', 0],
                    ['ZCG', 22],
                    ['ZNose', -1],
                    ['ZSail', -2],
                    ['Pitch', 8],
                    ['Roll', 7],
                    ['Yaw', 9],
                    ['Stern 1', 13],
                    ['Stern 2', 16],
                    ['Rudder', 15],
                    ['Fwd. Pln.', 14]]
        
        boats = ['688/751', 'S21', 'S23', 'VA', 'SSGN', 'TB']
        
        maneuvers = ['None','Cont Turn','FP Turn','Vert OS','Horz OS','Dive Jam','Rise Jam',
                     'Rud Jam','Accel','Decel','Rev Spiral','Speed Cal']
        
        # Set up the user interface
        #Button section
        runLbl = wx.StaticText(self, -1, "AM/RCM Data Analysis")
        runLbl.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
        paramLbl = wx.StaticText(self, -1, "Analysis Parameters")
        paramLbl.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))

        self.runBtn = wx.Button(self, -1, "Load Run")
        self.Bind(wx.EVT_BUTTON, self.OnFileClick, self.runBtn)
        self.writeBtn = wx.Button(self, -1, "Write Stats")
        self.Bind(wx.EVT_BUTTON, self.OnWriteClick, self.writeBtn)

        # Run Info    
        self.runnumText = wx.StaticText(self, -1, "")
        self.runtitleText = wx.StaticText(self, -1, "")
        self.notebox = wx.TextCtrl(self, -1, value="", size = (450, -1))
        
        # Anlysis Parm Section
        self.boatBtn = wx.RadioBox(self, -1, "Boat Type", choices=boats,
                                   majorDimension=2, style = wx.RA_SPECIFY_COLS)
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, self.boatBtn)
        self.startTime = wx.TextCtrl(self, -1, value="", size=(100, -1))
        self.endTime = wx.TextCtrl(self, -1, value="", size=(100,-1))
        self.Bind(wx.EVT_TEXT_ENTER, self.EvtTimeChg, self.startTime)
        self.Bind(wx.EVT_TEXT_ENTER, self.EvtTimeChg, self.endTime)
                
        # Maneuvering Data section
        dataLabel = wx.StaticText(self, -1, "Maneuvering Data (Full-Scale, Times from Execute)")
        dataLabel.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
        # Each data channel needs 8 text labels for the data and times
        for data in self.dataList:
            for i in range(5):
                textLabel = wx.StaticText(self, -1, " ", style=wx.ALIGN_RIGHT)
                data.append(textLabel)
        
        # Extra Data Section
        self.maneuverBtn = wx.RadioBox(self, -1, "Maneuver Type", choices = maneuvers,
                                       majorDimension=7, style = wx.RA_SPECIFY_COLS)
        self.Bind(wx.EVT_RADIOBOX, self.EvtDoExtra, self.maneuverBtn)
                                       
        extraLabel = wx.StaticText(self, -1, "Maneuver Analysis")
        extraLabel.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
                
        self.extrastartTime = wx.TextCtrl(self, -1, value="", size=(100, -1))
        self.extraendTime = wx.TextCtrl(self, -1, value="", size=(100,-1))
        self.Bind(wx.EVT_TEXT_ENTER, self.EvtExtraTimeChg, self.extrastartTime)
        self.Bind(wx.EVT_TEXT_ENTER, self.EvtExtraTimeChg, self.extraendTime)
        self.parameter = wx.TextCtrl(self, -1, value="", size=(100,-1))
        self.Bind(wx.EVT_TEXT_ENTER, self.EvtExtraTimeChg, self.parameter)

        # Extra data fields
        self.extraData = []
        for i in range(12):
            self.extraData.append(wx.StaticText(self, -1, " ", style=wx.CENTER))
        self.extraList = []
                  
        # Layout Screen - Set up the layout with sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(runLbl, 0, wx.ALL, 5)
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP, 5)

        # Button/Info Section
        btninfoSizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=10)
        btninfoSizer.Add((20,20), 0)
        btninfoSizer.Add(wx.StaticText(self, -1, "Run Information"), 0, wx.ALIGN_CENTER_VERTICAL)
        btninfoSizer.Add(self.runBtn, 0, wx.ALIGN_CENTER_VERTICAL)
        btninfoSizer.Add(self.runnumText, 0, wx.ALIGN_CENTER_VERTICAL)
        btninfoSizer.Add(self.writeBtn, 0, wx.ALIGN_CENTER_VERTICAL)
        btninfoSizer.Add(self.runtitleText, 0, wx.ALIGN_CENTER_VERTICAL)
        btninfoSizer.Add(wx.StaticText(self, -1, "Notes:"), 0, wx.ALIGN_LEFT)
        btninfoSizer.Add(self.notebox, 0, wx.ALIGN_LEFT)
        mainSizer.Add(btninfoSizer, wx.ALL, 10)
 
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        mainSizer.Add(paramLbl, 0, wx.ALL, 5)
       
        paramSizer = wx.BoxSizer(wx.HORIZONTAL)
        paramSizer.Add(self.boatBtn,0, wx.ALL, 5)
        timeSizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=2)
        timeSizer.Add((20,20), 0)
        timeSizer.Add(wx.StaticText(self, -1, "Analysis Range"), 0, wx.ALIGN_CENTER)
        timeSizer.Add(wx.StaticText(self, -1, "Start"), 0, wx.ALIGN_RIGHT)
        timeSizer.Add(self.startTime, 0, wx.ALIGN_CENTER)
        timeSizer.Add(wx.StaticText(self, -1, "Stop"), 0, wx.ALIGN_RIGHT)
        timeSizer.Add(self.endTime, 0, wx.ALIGN_CENTER)
        paramSizer.Add(timeSizer, 0, wx.ALL, 5)
        mainSizer.Add(paramSizer, 0, wx.EXPAND|wx.ALL, 10)

        # Data  section
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        mainSizer.Add(dataLabel, 0, wx.ALL, 5)
        dataSizer = wx.FlexGridSizer(cols=6, hgap=20, vgap=2)
        dataLabels = ('     ','     ','Abs.','Abs.','Rel.','Rel.',
                      'Channel','Appr','Max/Time','Min/Time','Max/Time','Min/Time')
                    
        for label in dataLabels:
            tempLbl = wx.StaticText(self, -1, label)
            tempLbl.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))               
            dataSizer.Add(tempLbl, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
        for data in self.dataList:
            dataSizer.Add(wx.StaticText(self, -1, data[0]), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
            txtFields = data[2:]
            for field in txtFields:
                dataSizer.Add(field, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)        
        mainSizer.Add(dataSizer, 0, wx.EXPAND|wx.ALL, 5)
        
        # Extra analysis section
        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)
        mainSizer.Add(extraLabel, 0, wx.ALL, 5)
        mainSizer.Add(self.maneuverBtn,0, wx.ALL, 5)

        extratimeSizer = wx.FlexGridSizer(cols=4, hgap=20, vgap=2)
        extratimeSizer.Add(wx.StaticText(self, -1, "Start Time"), 0, wx.ALIGN_CENTER)
        extratimeSizer.Add(wx.StaticText(self, -1, "Stop Time"), 0, wx.ALIGN_CENTER)
        extratimeSizer.Add((20,20), 0)
        tempLbl = wx.StaticText(self, -1, " ")
        self.extraList.append(tempLbl)
        extratimeSizer.Add(tempLbl, 0, wx.ALIGN_CENTER)
        extratimeSizer.Add(self.extrastartTime, 0, wx.ALIGN_CENTER)
        extratimeSizer.Add(self.extraendTime, 0, wx.ALIGN_CENTER)
        extratimeSizer.Add((20,20),0)
        extratimeSizer.Add(self.parameter, 0, wx.ALIGN_CENTER)

        mainSizer.Add(extratimeSizer, 0, wx.ALL, 5)

        mainSizer.Add(wx.StaticLine(self), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)

        extradataSizer = wx.FlexGridSizer(cols=6, hgap=25, vgap=6)
        
        tempLbl = wx.StaticText(self, -1, ' ')
        tempLbl.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.extraList.append(tempLbl)
        mainSizer.Add(tempLbl, 0, wx.ALL, 5)
        
        for i in range(6):
            tempLbl = wx.StaticText(self, -1, " ")
            tempLbl.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))               
            extradataSizer.Add(tempLbl, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
            self.extraList.append(tempLbl)
        for i in range(6):
            extradataSizer.Add(self.extraData[i], 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
        for i in range(6):
            tempLbl = wx.StaticText(self, -1, " ")
            tempLbl.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))               
            extradataSizer.Add(tempLbl, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)
            self.extraList.append(tempLbl)
        for i in range(6):
            extradataSizer.Add(self.extraData[i+6], 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)

        mainSizer.Add(extradataSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(mainSizer)
        self.Fit()
        
    def OnWriteClick(self, evt):
        """
            This method writes the computed stats to a stat file in the
            same directory as the run file.  The stst file is a comma/space
            delimited text file that can easily be imported into Excel, or
            the data can be selectively extracted using an excel macro
        """
        # define the delimeter - comma, space, etc
        dlm = ','
        
        # Shortcut for runObj
        r = self.runObj
        
        #Make up the stat file name from the run file name and path
        root, ext = os.path.splitext(self.runObj.filename)
        statfile = root + '.STT'
        statfile = os.path.join(self.runObj.dirname, statfile)
        
        # now open file
        f = open(statfile, 'w')
        
        # Write out the header portion
        header = [('Title1', r.title),
                ('Title2', r.timestamp),
                ('Numchans', r.nchans),
                ('DT', r.dt),
                ('Length', r.length),
                ('Boat_Type' , r.boat),
                ('', ''),
                ('Stdby_Time', r.stdbytime),
                ('Exec_Time', r.exectime),
                ('Note:', self.notebox.GetValue())]
        
        for name,value in header:
            f.write(name)
            f.write(dlm)
            f.write(str(value))
            f.write('\n')
        
        # Write Out Extra Maneuvering Data
        if self.maneuverBtn.GetStringSelection() == 'None':
            f.write('\n')
            f.write('\n')
        else:
            i = 0
            for label in self.ManeuverDict[self.maneuverBtn.GetStringSelection()]:
                if i == 1:
                    f.write(label+'\n')
                if i > 1 and self.ManeuverTitles[label] <> ' ':
                    f.write(self.ManeuverTitles[label]+',')
                i = i + 1
            i = 0
            f.write('\n')
            for label in self.ManeuverDict[self.maneuverBtn.GetStringSelection()]:
                if i > 1 and self.ManeuverTitles[label] <> ' ':
                    f.write(self.extracalc[label]+',')
                i = i + 1
            i = 0
        for i in range(6):
            f.write('\n')
        
        # Write Out Normal Data
        labels = ('Chan','Appr.','Abs_Max','Abs_Max_Time','Abs_Min','Abs_Min_Time',
                  'Rel_Max','Rel_Min')
        for label in labels:
            f.write(label+dlm)
        f.write('\n')
        
        # Put computed depths first
        ZNoffset = STDFile.GeoTable[self.runObj.boat][0]
        ZSoffset = 2 * STDFile.GeoTable[self.runObj.boat][0] + STDFile.GeoTable[self.runObj.boat][3]

        cdata = [('Znose', (r.Znoseappr, r.maxZnose, r.maxZnosetime, r.minZnose,
                            r.minZnosetime, r.maxZnose-r.Znoseappr-ZNoffset,
                            r.minZnose-r.Znoseappr-ZNoffset)),
                ('Zsail', (r.Zsailappr, r.maxZsail, r.maxZsailtime, r.minZsail,
                           r.minZsailtime, r.maxZsail-r.Zsailappr-ZSoffset,
                           r.minZsail-r.Zsailappr-ZSoffset))]
        
        for name, values in cdata:
            f.write(name)
            for value in values:
                f.write(dlm)
                f.write('%.2f' % value)
            f.write('\n')
       
        for i in range(r.nchans):
            f.write(r.chan_names[i].replace("'",""))
            f.write(dlm)
            f.write('%.2f' % r.appr_values[i])
            f.write(dlm)
            f.write('%.2f' % r.maxValues[i])
            f.write(dlm)
            f.write('%.2f' % r.maxTimes[i])
            f.write(dlm)
            f.write('%.2f' % r.minValues[i])
            f.write(dlm)
            f.write('%.2f' % r.minTimes[i])
            f.write(dlm)
            f.write('%.2f' % (r.maxValues[i]-r.appr_values[i]))
            f.write(dlm)
            f.write('%.2f' % (r.minValues[i]-r.appr_values[i]))
            f.write('\n')
        f.close()
        
    def OnFileClick(self, evt):
        """ 
            Pops up a dialog to choose the run and then opens and 
            loads the run into memory
        """
        try:
            runPath = self.runFile
        except:
            runPath = '//alpha1/DISK31'
            
        dlg = wx.FileDialog(self, "Choose Run File",
                                defaultDir=runPath, wildcard="*.std",
                                style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.runFile = dlg.GetPath()
            self.runObj = get_run(self.runFile)
            self.runnumText.SetLabel(self.runObj.filename)
            self.runtitleText.SetLabel(self.runObj.title)
            self.runObj.compStats()
            self.startTime.ChangeValue(str(0.0))
            self.endTime.ChangeValue(str(self.runObj.ntime[-1]))
            # Compute and Display data
            self.setData()
            self.boatBtn.SetStringSelection(self.runObj.boat)
            self.maneuverBtn.SetStringSelection('None')
            self.EvtDoExtra(evt)
            # Make plot
            self.makePlot()
        dlg.Destroy()
        
    def EvtTimeChg(self,evt):
        """
            Get new start and stop time and recompute the stats
        """
        starttime = self.runObj.exectime + float(self.startTime.GetValue())
        startrec = int(starttime/self.runObj.dt)
        if startrec < 0:
            startrec = 0
        
        endtime = self.runObj.exectime + float(self.endTime.GetValue())
        endrec = int(endtime/self.runObj.dt)
        # Check the bounds
        if endrec >= len(self.runObj.ntime)-1:
            endrec = len(self.runObj.ntime)-1
            
        self.runObj.compStats(startrec, endrec)
        self.setData()
        self.Fit()
        
    def EvtExtraTimeChg(self, evt):
        """
            Get new start and stop time and recompute the Turn stats
        """
        starttime = self.runObj.exectime + float(self.extrastartTime.GetValue())
        startrec = int(starttime/self.runObj.dt)
        if startrec < 0:
            startrec = 0
        
        endtime = self.runObj.exectime + float(self.extraendTime.GetValue())
        endrec = int(endtime/self.runObj.dt)
        # Check the bounds
        if endrec >= len(self.runObj.ntime)-1:
            endrec = len(self.runObj.ntime)-1
            
        # Now To compute the stats and display.  These are done individually for now
        # Slice out the data of interest
        rundata = self.runObj.data[startrec:endrec, :]
        npts = len(rundata[:,6])
                
        self.ManeuverTitles = ['ApprUpw','ApprRoll','ApprPitch','ApprYaw','ApprStr1','ApprBow',
                            'ApprRud','ApprStr2','AvgUpw','AvgRoll','AvgPitch','AvgYaw','AvgStr1',
                            'AvgBow','AvgRud','AvgStr2','RollStbd','RollPort','PitchUp','PitchDn',
                            'YawStbd','YawPort','ZCGMax','ZCGMin','ZNose','ZSail','MaxRise','YawRate',
                            'StdRud','TDiam','EPA','EPATime','EPADepth','OSPitch','OSDepth','EYA',
                            'EYATime','OSYaw','TimeTo0','Uat30','Uat60','Uat90','Uat120',' ']

        self.ManeuverDict ={'Cont Turn':[' ','CT Steady Data', 8, 14, 12, 15, 13, 10, 9, 16, 17, 27, 29, 43],
            'FP Turn':[' ','UT Steady Data', 8, 14, 12, 15, 13, 10, 9, 16, 17, 27, 29, 43],
            'Vert OS':['EPA','Vertical Overshoot', 2, 30, 31, 32, 33, 34, 43, 43, 43, 43, 43, 43],
            'Horz OS':['EYA','Horizontal Overshoot', 3, 35, 36, 37, 43, 43, 43, 43, 43, 43, 43, 43],
            'Dive Jam':[' ','Dive Jam', 22, 19, 16, 17, 43, 43, 43, 43, 43, 43, 43, 43],
            'Rise Jam':[' ','Rise Jam', 23, 24, 25, 26, 18, 16, 17, 43, 43, 43, 43, 43],
            'Rud Jam':[' ','Rudder Jam', 22, 23, 24, 25, 26, 19, 18, 16, 17, 43, 43, 43],
            'Accel':[' ','Acceleration', 39, 40, 41, 42, 43, 43, 43, 43, 43, 43, 43, 43],
            'Decel':[' ','Deceleration', 22, 23, 24, 25, 26, 19, 18, 16, 17, 20, 21, 38],
            'Rev Spiral':[' ','Reverse Spiral', 27, 28, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43],
            'Speed Cal':[' ','Speed Calibration', 0, 6, 4, 7, 5, 2, 1, 43, 43, 43, 43, 43]}
        
        self.extracalc = []
        #Approach Values (Upw [0], Roll [1], Pitch [2], Yaw [3], Str1 [4], Bow [5], Rud [6], Str2 [7])
        datachans = [6,7,8,9,13,14,15,16]
        for i in range(8):
            self.extracalc.append('%.2f' % self.runObj.appr_values[datachans[i]])
        
        #Average Run Values (Upw [8], Roll [9], Pitch [10], Yaw [11], Str1 [12], Bow [13], Rud [14], Str2 [15])
        for i in range(8):
            if i == 0:
                self.extracalc.append('%.2f' % ((sum(rundata[:, datachans[i]])/npts)))
            else:
                self.extracalc.append('%.2f' % ((sum(rundata[:, datachans[i]])/npts) - self.runObj.appr_values[datachans[i]]))
        
        #Extremes (RollStbd [16], RollPort [17], PitchUp [18], PitchDn [19], YawStbd [20], YawPort [21], ZCGMax [22], ZCGMin [23]) 
        datachans = [7,8,9,22]
        for i in range(4):
            self.extracalc.append('%.2f' % (self.runObj.maxValues[datachans[i]] - self.runObj.appr_values[datachans[i]]))
            self.extracalc.append('%.2f' % (self.runObj.minValues[datachans[i]] - self.runObj.appr_values[datachans[i]]))
        
        #Nose and Sail Calcs (ZNose [24], ZSail [25], MaxRise [26])
        ZNoffset = STDFile.GeoTable[self.runObj.boat][0]
        ZSoffset = 2 * STDFile.GeoTable[self.runObj.boat][0] + STDFile.GeoTable[self.runObj.boat][3]
        self.extracalc.append('%.2f' % (self.runObj.minZnose - self.runObj.Znoseappr - ZNoffset))
        self.extracalc.append('%.2f' % (self.runObj.minZsail - self.runObj.Zsailappr - ZSoffset))
        MaxRise = min(self.runObj.minValues[22] - self.runObj.appr_values[22],
                      self.runObj.minZnose - self.runObj.Znoseappr - ZNoffset,
                      self.runObj.minZsail - self.runObj.Zsailappr - ZSoffset)
        self.extracalc.append('%.2f' % MaxRise)
        
        #Turning (YawRate [27], StdRud [28], TDiam [29])
        yawrate = 0
        yawdata = rundata[:,9].tolist()
        for i in range(npts):
            if i != 0:
                yawrate = yawrate + (abs(abs(yawdata[i]) - abs(yawdata[i-1]))/self.runObj.dt)
        yawrate = yawrate/(npts-1)
        self.extracalc.append('%.3f' % yawrate)
        self.extracalc.append('%.2f' % ((sum(rundata[:,15])/npts)))
        vel = (sum(rundata[:,6])/npts) * 1.6878
        tdiam = vel * 2 / (math.radians(yawrate)*self.runObj.length)
        self.extracalc.append('%.3f' % tdiam)
        
        #Vertical Overshoots (EPA [30], EPATime [31], EPADepth [32], OSPitch [33], OSDepth [34])
        epa = self.runObj.appr_values[8] + float(self.parameter.GetValue())
        epaRec = 0
        if float(self.parameter.GetValue()) > 0:
            while epa >= rundata[epaRec + 1,8] and (endrec - startrec - 2) > epaRec:
                epaRec = epaRec + 1
            osPitch = self.runObj.maxValues[8] - epa
            osDepth = self.runObj.minValues[22] - rundata[epaRec,22]
        if float(self.parameter.GetValue()) < 0:
            while epa <= rundata[epaRec + 1,8] and (endrec - startrec - 2) > epaRec:
                epaRec = epaRec + 1
            osPitch = self.runObj.minValues[8] - epa
            osDepth = self.runObj.maxValues[22] - rundata[epaRec,22]
        epaTime = (epaRec)*self.runObj.dt + float(self.extrastartTime.GetValue())
        epaDepth = rundata[epaRec,22] - self.runObj.appr_values[22]
        if epaRec == 0 or epaRec >= (endrec - startrec - 2):
            for i in range(5):
                self.extracalc.append('--')
        else:
            self.extracalc.append('%.2f' % epa)
            self.extracalc.append('%.2f' % epaTime)
            self.extracalc.append('%.2f' % epaDepth)
            self.extracalc.append('%.2f' % osPitch)
            self.extracalc.append('%.2f' % osDepth)
        
        #Horizontal Overshoots (EYA [35], EYATime [36], OSYaw [37]
        #Tricky Becasue yaw goes from +/- 180 degrees
        eya = self.runObj.appr_values[9] + float(self.parameter.GetValue())
        eyaRec = 0
        if abs(eya) >= 180:
            eya = -(eya/abs(eya))*(360 - abs(eya))
        if float(self.parameter.GetValue()) > 0 and (rundata[eyaRec+40,9] - rundata[eyaRec,9]) > 0:
            while (eya <= rundata[eyaRec,9] or eya >= rundata[eyaRec + 1,9]) and (endrec - startrec - 2) > eyaRec:
                eyaRec = eyaRec + 1
            osYaw = self.runObj.maxValues[9] - eya
        if float(self.parameter.GetValue()) < 0 and (rundata[eyaRec+40,9] - rundata[eyaRec,9]) < 0:
            while (eya >= rundata[eyaRec,9] or eya <= rundata[eyaRec + 1,9]) and (endrec - startrec - 2) > eyaRec:
                eyaRec = eyaRec + 1
            osYaw = self.runObj.minValues[9] - eya
        eyaTime = (eyaRec)*self.runObj.dt + float(self.extrastartTime.GetValue())
        if eyaRec == 0 or eyaRec >= (endrec - startrec - 2):
            for i in range(3):
                self.extracalc.append('--')
        else:
            self.extracalc.append('%.2f' % eya)
            self.extracalc.append('%.2f' % eyaTime)
            self.extracalc.append('%.2f' % osYaw)
        
        #Speed vs Time(x) (TimeTo0 [38], Uat30 [39], Uat60 [40], Uat90 [41], Uat120 [42])
        if self.runObj.minValues[6] < 0.5:
            self.extracalc.append('%.2f' % self.runObj.minTimes[6])
        else:
            self.extracalc.append('--')
        acctime = (30,60,90,120)
        for i in range(4):
            AccRec = startrec + int(acctime[i]/self.runObj.dt)
            if AccRec < (endrec - startrec - 2):
                self.extracalc.append('%.2f' % rundata[AccRec, 6])
            else:
                self.extracalc.append('--')
        
        #Blank (' ' [43])
        self.extracalc.append('')
        
        #Updates extracalc list and extraList list
        i = 0
        for label in self.ManeuverDict[self.maneuverBtn.GetStringSelection()]:
            if i < 2:
                self.extraList[i].SetLabel(label)
            else:
                self.extraList[i].SetLabel(self.ManeuverTitles[label])
                self.extraData[i-2].SetLabel(self.extracalc[label])
            i = i+1
        i = 0
                    
        self.Layout()
    
    def EvtDoExtra(self, evt):
        if self.maneuverBtn.GetStringSelection() == 'None':
            self.extrastartTime.ChangeValue('')
            self.extraendTime.ChangeValue('')
            self.parameter.ChangeValue('')
            for i in range (12):
                self.extraData[i].SetLabel(' ')
            for i in range (13):
                self.extraList[i].SetLabel(' ')
        else:
            self.extrastartTime.ChangeValue(self.startTime.GetValue())
            self.extraendTime.ChangeValue(self.endTime.GetValue())
            self.parameter.ChangeValue('0')
            self.EvtExtraTimeChg(evt)
        self.Fit()
    
    def makePlot(self):
        """
            Create an overplot to allow user to change the analysis
            range and to preview the data
        """
        cfgfile = './analysis.ini'
                               
        params = (0.0, self.runObj.ntime[-1]+5, 4)
                
        plotData = PlotPage([self.runObj], params, cfgfile)
        frame = MultiCanvasFrame(plotData, [self.runObj.filename], 0)
        frame.Show()

    def setData(self):
        """
            Displays the maximum and minimum values for the data
        """
        
        for data in self.dataList:
            if data[1] >= 0:
                apprValue = self.runObj.appr_values[data[1]]
                data[2].SetLabel("%.2f" % apprValue)
                data[3].SetLabel("%.2f/%.2f" % (self.runObj.maxValues[data[1]],self.runObj.maxTimes[data[1]]))
                data[4].SetLabel("%.2f/%.2f" % (self.runObj.minValues[data[1]],self.runObj.minTimes[data[1]]))
                data[5].SetLabel("%.2f/%.2f" % ((self.runObj.maxValues[data[1]] - apprValue),self.runObj.maxTimes[data[1]]))
                data[6].SetLabel("%.2f/%.2f" % ((self.runObj.minValues[data[1]] - apprValue),self.runObj.minTimes[data[1]]))
            elif data[1] == -1:
                apprValue = self.runObj.Znoseappr
                ZNoffset = STDFile.GeoTable[self.runObj.boat][0]
                data[2].SetLabel("%.2f" % apprValue)
                data[3].SetLabel("%.2f/%.2f" % (self.runObj.maxZnose,self.runObj.maxZnosetime))
                data[4].SetLabel("%.2f/%.2f" % (self.runObj.minZnose,self.runObj.minZnosetime))
                data[5].SetLabel("%.2f/%.2f" % ((self.runObj.maxZnose - apprValue - ZNoffset),self.runObj.maxZnosetime))
                data[6].SetLabel("%.2f/%.2f" % ((self.runObj.minZnose - apprValue - ZNoffset),self.runObj.minZnosetime))
            elif data[1] == -2:
                apprValue = self.runObj.Zsailappr
                ZSoffset = 2 * STDFile.GeoTable[self.runObj.boat][0] + STDFile.GeoTable[self.runObj.boat][3]
                data[2].SetLabel("%.2f" % apprValue)
                data[3].SetLabel("%.2f/%.2f" % (self.runObj.maxZsail,self.runObj.maxZsailtime))
                data[4].SetLabel("%.2f/%.2f" % (self.runObj.minZsail,self.runObj.minZsailtime))
                data[5].SetLabel("%.2f/%.2f" % ((self.runObj.maxZsail - apprValue - ZSoffset),self.runObj.maxZsailtime))
                data[6].SetLabel("%.2f/%.2f" % ((self.runObj.minZsail - apprValue - ZSoffset),self.runObj.minZsailtime))
                
        self.Layout()
        
    def EvtRadioBox(self,event):
        self.runObj.boat = self.boatBtn.GetStringSelection()
        self.runObj.compStats()
        # Compute and Display data
        self.setData()
        
            
if __name__ == "__main__":
    app = wx.PySimpleApp(redirect=False)
    frame = AnalysisFrame()
    frame.Show()
    app.MainLoop()
