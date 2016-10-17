"""
Created on Wed Jul 21 13:35:28 2010

Frame for finding the extrema for a selected list of channels from amongst a 
selected list of runs.

@author: C.Michael Pietras
"""

import wx
import wx.html
import os
import fnmatch
import plottools as plottools
import numpy as np
import time as time_mod
from scipy import signal

class App(wx.App):
    
    def OnInit(self):
        frame = ExtremaFrame()
        frame.Center(direction= wx.BOTH)
        frame.Show()
        self.SetTopWindow(frame)
        return True

class ExtremaFrame(wx.Frame):
    def __init__(self):
        
        #Make some interesting variables
        self.FilesList = []
        self.rootDir = r'\\sim1\samc\rcmdata'
        if not os.path.exists(self.rootDir):
            self.rootDir = r'c:/AM_Merge_Data'
        self.extremaDict = {'Maximum':'max', 'Minimum':'min', 'Maximum Displacement':'maxDis', 'Minimum Displacement':'minDis'}
        self.partDict = {'Entire file':'entire', 'Approach only':'approach', 'Maneuver only':'maneuver'}
        
        wx.Frame.__init__(self,None,-1,"Calculate Extrema",(-1,-1),(380,345))
        self.CreateMenuBar() 
        self.CreateWidgets()              
    
    def CreateWidgets(self):
        #Make all the widgets
        panel = wx.Panel(self)
        FileLabel = wx.StaticText(panel,-1,'Filename(s):')
        self.FileBox = wx.TextCtrl(panel,-1,'',size = (300, 100), style = wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL)
        filesButton = wx.Button(panel,-1,'Choose Files',size = (150, 50))
        directoryButton = wx.Button(panel,-1,'Choose Directory',size = (150, 50))
        
        chanList = wx.StaticText(panel, -1, "Channel List:")
        self.chanList = wx.ListBox(panel, -1, size=(150,180),
                                   style=wx.LB_EXTENDED, name="Channel List")
        self.extremaType = wx.RadioBox(panel, -1, "Extrema Type", choices = self.extremaDict.keys(), majorDimension = 1,size = (150, -1))
        self.filePart = wx.RadioBox(panel, -1, "Part of File(s)", choices = self.partDict.keys(), majorDimension = 1,size = (150, -1))
        
        self.execBtn = wx.Button(panel, -1, "Execute", size = (-1,50))
        
        
        #Make sizer
        mainSizer = wx.FlexGridSizer(cols = 1, hgap = 10, vgap = 10)
        mainSizer.AddGrowableCol(0)
        
        fileSizer = wx.FlexGridSizer(cols = 2, hgap = 10, vgap = 10)
        fileSizer.AddGrowableCol(0)
        fileSizerDisplay = wx.FlexGridSizer(cols = 2, hgap = 10, vgap = 10)
        fileSizerDisplay.AddGrowableCol(1)
        fileSizerDisplay.Add(FileLabel, 0 , wx.ALIGN_CENTER)
        fileSizerDisplay.Add(self.FileBox, 1, wx.EXPAND)
        fileSizerDisplay.Add(chanList, 0 , wx.ALIGN_CENTER)
        fileSizerDisplay.Add(self.chanList, 1, wx.EXPAND)
        fileSizerButtons = wx.BoxSizer(wx.VERTICAL)
        fileSizerButtons.Add(filesButton)
        fileSizerButtons.Add(directoryButton)
        fileSizerButtons.Add(self.extremaType)
        fileSizerButtons.Add(self.filePart)
        fileSizer.Add(fileSizerDisplay, wx.EXPAND)
        fileSizer.Add(fileSizerButtons)
        
        mainSizer.Add(fileSizer, 1, wx.EXPAND)
        mainSizer.Add(self.execBtn, 1, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL)
        
        panel.SetSizer(mainSizer)
        mainSizer.SetSizeHints(self)
        
        #Bind button events
        self.Bind(wx.EVT_BUTTON,self.OnFilesButton,filesButton)
        self.Bind(wx.EVT_BUTTON,self.OnDirectoryButton,directoryButton)
        self.Bind(wx.EVT_BUTTON, self.OnRunButton, self.execBtn)
        
    def menuData(self):
        return (("&File",
                 ("&Quit", "Quit", self.OnCloseWindow)),
                ("&Help",
                 ("&About", "About Program", self.OnAbout)))
                 
    def CreateMenuBar(self):
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
        
    def OnFilesButton(self, evt): 
        """
            Allow the user to select the files directly
        """
        dlg = wx.FileDialog(None, "Choose files", self.rootDir, '', '*.std', wx.OPEN|wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.FilesList = dlg.GetPaths()
            self.PopulateDisplay()
        dlg.Destroy()
        
    def OnDirectoryButton(self,evt):
        """
            Allow the user to select a directory.  All STD files in that directory
            will be used
        """
        self.FilesList = []
        dlg = wx.DirDialog(None, "Choose directory", self.rootDir)
        if dlg.ShowModal() == wx.ID_OK:
            rootDir = dlg.GetPath()
            for file in os.listdir(rootDir):
                path = os.path.join(rootDir, file)
                if not os.path.isdir(path):
                    head, tail = os.path.split(path)
                    if fnmatch.fnmatch(tail, '*.std'):
                        self.FilesList.append(path)
            self.PopulateDisplay()
        dlg.Destroy()
        
    def PopulateDisplay(self):        
        """ 
            Updates the display with the correct information based on the 
            self.FilesList variable
        """
        displayString = ''
        for i in self.FilesList:
            displayString += i+'\n'
        self.FileBox.SetValue(displayString)
        if len(self.FilesList)>0:
            runName = self.FilesList[0]
            if os.path.isfile(runName):
                runObj = plottools.get_run(runName)
                self.chanList.Set([])
                self.chanList.InsertItems(runObj.chan_names, 0)
                self.chanList.SetSelection(0)
                
    def OnRunButton (self, evt):
        """
            Find the extrema and create a frame for output
        """
        chans = self.chanList.GetSelections()
        extrema = self.extremaDict[self.extremaType.GetStringSelection()]
        part = self.partDict[self.filePart.GetStringSelection()]
        if len(self.FilesList) > 0:
            if len(chans) > 0:
                value, time, name = self.findExtrema(chans, extrema, part)
                frame = ViewFrame(self.FilesList, chans, self.chanList.GetStrings(), 
                                  extrema, part, value, time, name) 
                frame.Show()
        
    def OnCloseWindow(self,evt):
        self.Destroy()
        
    def OnAbout(self,evt):
        """
            Create html help window
        """
        dlg = AboutDialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        
    def findExtrema(self, chans,extrema,part):
        value, time, name = {}, {}, {}
        badfiles = []
        index = 0
        while index <= len(self.FilesList):
            try:
                runObj = plottools.get_run(self.FilesList[index])
                break
            except:
                badfiles.append(file[index])
                index+=1
        for chan in chans:
            data = runObj.getEUData(chan)
            if (extrema == 'minDis') | (extrema == 'maxDis'):
                for i in range(len(data)):
                    data[i] = abs(data[i])   
            averageData = signal.lfilter(np.ones(20)/20,1,data).tolist()
            tfix = 0             
            if part == 'approach':
                data = data[:runObj.execrec]
                averageData = averageData[:runObj.execrec]
            elif part == 'maneuver':
                data = data[runObj.execrec:]
                averageData = averageData[runObj.execrec:]
                tfix = runObj.exectime
            data = averageData
            if data:
                value[chan], time[chan], name[chan] = data[0],runObj.ntime[0]+tfix,self.FilesList[0]
            else:
                value[chan], time[chan], name[chan] = 0, 0, self.FilesList[0]
        for filename in self.FilesList:
            try:
                runObj = plottools.get_run(filename)
            except:
                badfiles.append(filename)
                runObj = None
            if runObj:
                for chan in chans:
                    if (len(runObj.chan_names) >= chan):
                        data = runObj.getEUData(chan)                   
                        #averageData = self.runAvg(data, 4)
                        averageData = signal.lfilter(np.ones(20)/20,1,data).tolist()
                        tfix = 0
                        if part == 'approach':
                            data = data[:runObj.execrec]
                            averageData = averageData[:runObj.execrec]
                        elif part == 'maneuver':
                            data = data[runObj.execrec:]
                            averageData = averageData[runObj.execrec:]
                            tfix = runObj.exectime
                        data = averageData
                        if data:
                            if extrema == 'max':
                                val, index = self.max(data)
                                if val > value[chan]:
                                    value[chan] = val
                                    time[chan] = runObj.ntime[index]+tfix
                                    name[chan] = filename
                            elif extrema == 'min':
                                val, index = self.min(data)
                                if val < value[chan]:
                                    value[chan] = val
                                    time[chan] = runObj.ntime[index]+tfix
                                    name[chan] = filename
                            elif extrema == 'maxDis':
                                for i in range(len(data)):
                                    data[i] = abs(data[i])
                                val, index = self.max(data)
                                if val > value[chan]:
                                    value[chan] = val
                                    time[chan] = runObj.ntime[index]+tfix
                                    name[chan] = filename
                            elif extrema == 'minDis':
                                for i in range(len(data)):
                                    data[i] = abs(data[i])
                                val, index = self.min(data)
                                if val < value[chan]:
                                    value[chan] = val
                                    time[chan] = runObj.ntime[index]+tfix
                                    name[chan] = filename
        if badfiles:
            text = 'The following file(s) could not be opened: \n  '
            for i in badfiles:
                self.FilesList.remove(i)
                dirname, badfilename = os.path.split(i)
                text+=badfilename+' \n  '
            self.PopulateDisplay()
            dlg = wx.MessageDialog(None,text,'Error',wx.OK)
            result = dlg.ShowModal()
            dlg.Destroy()
        return value, time, name
    
    def max(self, iter):
        """ Iterate through an iterable and find the maximum value.  Also return the 
            index at which the max is.
            This is done primarily to avoid wierdness with the index function where it
            was unable to find the max of a list in the list.
        """
        index = 0
        value = iter[0]
        for i in range(len(iter)):
            if iter[i] > value:
                value = iter[i]
                index = i
        return value, index
        
    def min(self, iter):
        """ Iterate through an iterable and find the minimum value.  Also return the 
            index at which the max is.
            This is done primarily to avoid wierdness with the index function where it
            was unable to find the max of a list in the list.
        """
        index = 0
        value = iter[0]
        for i in range(len(iter)):
            if iter[i] < value:
                value = iter[i]
                index = i
        return value, index
      
class AboutDialog(wx.Dialog):
    text = '''
    <html>
    <body bgcolor="ACAA60">
    <center><table bgcolor="#455481" width="100%" cellspacing="0"
    cellpadding="0" border="1">
    <tr>
        <td align="center"><h1>Find Extrema</h1></td>
    </tr>
    </table>
    </center>
    <p><b>Find Extrema</b> is an application designed to find the maximum, minimum,
        maximum displacement, or minimum diplacement for each selected channel 
        from amongst a group of selected files</p>    
    </body>
    </html>
    '''
    
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About Find Extrema', size=(440, 400) )
        
        html = wx.html.HtmlWindow(self)
        html.SetPage(self.text)
        button = wx.Button(self, wx.ID_OK, "Okay")
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(button, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        
        self.SetSizer(sizer)
        self.Layout()
        
    
class ViewFrame(wx.Frame):    
    def __init__(self, files, chans, chan_names, extrema, part, value, time, name, window_title = 'View', window_size=(400,700)):
        
        self.extremaDictR = {'max':'maximum', 'min':'minimum', 'maxDis':'maximum displacement', 'minDis':'minimum displacement'}
        self.partDictR = {'entire':'entire file', 'approach':'approach only', 'maneuver':'maneuver only'}
        
        wx.Frame.__init__(self, None, title=window_title, size=window_size)
        panel=wx.Panel(self)    
        self.files, self.chans, self.chan_names, self.extrema, self.part, self.value, self.time, self.name = files, chans, chan_names, extrema, part, value, time, name
        
        text = self.TextGen()
        
        mainSizer = wx.FlexGridSizer(cols = 1, hgap = 5, vgap = 5)
        mainSizer.AddGrowableCol(0); mainSizer.AddGrowableRow(0);
        self.textbox = wx.TextCtrl(panel, -1, text, style = wx.TE_READONLY|wx.TE_MULTILINE)
        mainSizer.Add(self.textbox, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        panel.SetSizer(mainSizer)
        self.CreateMenuBar()
        
    def TextGen(self):
        """
            Generate the output text
        """
        text = 'Find the ' + self.extremaDictR[self.extrema] + ' of the following runs through the '+self.partDictR[self.part]+':\n'
        for i in range(len(self.files)):
            dirname, filename = os.path.split(self.files[i])
            text += filename
            if not i == len(self.files)-1:
                text += ', '
            else:
                text += '\n\n'
        for chan in self.chans:
            line = 'Channel '+str(chan)+' ('+self.chan_names[chan]+') \n'
            text += line
            dirname, filename = os.path.split(self.name[chan])
            line = str(self.value[chan])+' at nTime '+str(self.time[chan])+' seconds in file '+filename+'\n\n'
            text += line   
        return text
    
    def CreateMenuBar(self):
        #Menu Bar
        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)
        
        #File menu
        menuFile = wx.Menu()
        open = menuFile.Append(-1,"&Open")
        self.Bind(wx.EVT_MENU, self.OnOpen,open)
        save = menuFile.Append(-1,"&Save")
        self.Bind(wx.EVT_MENU, self.OnSave,save)
        exit = menuFile.Append(-1,"E&xit")
        self.Bind(wx.EVT_MENU, self.OnQuit,exit)
        menuBar.Append(menuFile,"&File")
        
    
    def OnQuit(self,event):
        self.Destroy()
    
    def OnSave(self, event):
        defaultName = 'ExtremaLog-'+str(time_mod.time())
        dlg = wx.FileDialog(None, 'Save', os.curdir+'\output',defaultName,'*.elog',wx.SAVE|wx.OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            f = open(dlg.GetPath(),'wt')
            f.write(self.extrema+'\t'+self.part+'\t'+str(len(self.chans))+'\n')
            for filename in self.files:
                f.write(filename+'\t')
            f.write('\n')
            f.write('chan_#\tchan_name\textrema_value\textrema_time\textrema_file\n')
            i = 0
            for chan in self.chans:
                for val in [str(chan), self.chan_names[chan], str(self.value[chan]), str(self.time[chan]), self.name[chan]]:
                    f.write(val+'\t')
                f.write('\n')
            f.close()
            
    def OnOpen(self, event):
        dlg = wx.FileDialog(None, 'Open', os.curdir+'\output','','*.elog',wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            try:
                f = open(dlg.GetPath(),'r')
                line = f.readline().rstrip().split('\t')
                extrema = line[0]; part = line[1]; numchans = int(line[2])
                line = f.readline().rstrip().split('\t')
                files = []
                for filename in line:
                    files.append(filename)
                line = f.readline().rstrip().split('\t')                           
                chans, chan_names, value, time, name = [], {}, {}, {}, {}
                for i in range(numchans):
                    line = f.readline().rstrip().split('\t')
                    chans.append(int(line[0]))
                    chan_names[chans[-1]] = line[1]
                    value[chans[-1]] = float(line[2])
                    time[chans[-1]] = float(line[3])
                    name[chans[-1]] = line[4]
                f.close()                
                self.files, self.chans, self.chan_names, self.extrema, self.part, self.value, self.time, self.name = files, chans, chan_names, extrema, part, value, time, name
                text = self.TextGen()
                self.textbox.SetValue(text)
            except:
                print "Error somewhere in OnOpen"
            
if __name__ == '__main__':
    app = App(False)    
    app.MainLoop()
