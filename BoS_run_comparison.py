"""
Created on Mon Aug 09 07:47:12 2010

Check if two given STD files are "close enough" to one another and return a list of
any channels that aren't "close enough"
Used to compare beginning of run files to determine if any dynos have gone bad.

@author: C.Michael Pietras
"""

#correlation threshhold.  This is the number the correlation between the two runs
#must be above for the run not to be flagged
correlation_threshold = .5

import os
from filetypes import STDFile
import numpy as np
from scipy import signal
from plottools import PlotPageWrapped
from multicanvas import MultiCanvasFrame
import wx

class CorrelateFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Compare Beginning of Shift Runs", size = (310, 155),
                          style = wx.DEFAULT_FRAME_STYLE^(wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER))
        
        panel = wx.Panel(self)
        
        runLabel = wx.StaticText(panel, -1, "Run Numbers To Compare:", size = (300, 25))
        self.runNo1 = wx.TextCtrl(panel, -1, size=(300, 25))
        self.runNo2 = wx.TextCtrl(panel, -1, size=(300, 25))
        self.compBtn = wx.Button(panel, -1, "Compare", size = (300,25))
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        for i in [runLabel, self.runNo1, self.runNo2, self.compBtn]:
            mainSizer.Add(i)
        
        panel.SetSizer(mainSizer)        
        
        self.Bind(wx.EVT_BUTTON, self.OnCompare, self.compBtn)        
        
        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)
        menuEdit = wx.Menu()
        exclusion = menuEdit.Append(-1,"Channel &Exclusion List")
        self.Bind(wx.EVT_MENU, self.OnChangeExcluded,exclusion)
        menuBar.Append(menuEdit,"&Edit")        
        
    def OnCompare(self,evt):
        """
            Compare the two runs.  If one does't exist, print an error message.
            Make the message a dialog box at some point.
        """
        if not self.STDCompare(self.runNo1.GetValue(), self.runNo2.GetValue()):
            print("One of those runs doesn't exist")
            
    def OnChangeExcluded(self, evt):
        """
            Change which runs are not checked for closeness
        """
        frame = ExclusionFrame(self)
        frame.Show()
        
    def STDCompare(self, title1, title2):        
        std_path = '/disk2/home/'+os.environ['USER']
        file1 = STDFile(title1, search_path=std_path)
        file2 = STDFile(title2, search_path=std_path)
        if (file1.data == []) | (file2.data == []):
            return False
        if file1.nchans >= file2.nchans:
            chans = range(file1.nchans)
        else:
            chans = range(file2.nchans)
            
        #load in a list of channels to ignore
        file = open("lib/BoS_ignore_channels.txt")
        for line in file.readlines():
            ignore = int(line.split()[0])
            if ignore in chans:
                chans.remove(ignore)
            
        brokenchans = []
        for chan in chans:
            #Get the data from both files and filter it
            data1 = signal.lfilter(np.ones(20)/20,1,file1.getEUData(chan))
            data2 = signal.lfilter(np.ones(20)/20,1,file2.getEUData(chan))
            offset = np.average(data1[:file1.execrec][-30:]-data2[:file2.execrec][-30:])
            data2 = data2+offset
            file1.data[:,chan] = data1
            file2.data[:,chan] = data2
            
            if len(data1[file1.execrec:]) <= len(data2[file2.execrec:]):
                length = len(data1[file1.execrec:])
            else:
                length = len(data2[file2.execrec:])
            ntime = file1.ntime[file1.execrec:file1.execrec+length]
            data1 = data1[file1.execrec:file1.execrec+length]
            data2 = data2[file2.execrec:file2.execrec+length]
            
            #Use numpy's corrcoef function
            corr = np.corrcoef(data1,data2)[0,1]
            if corr < correlation_threshold:
                brokenchans.append(chan)  
            
        #Give an output message
        if not brokenchans: 
            dlg = wx.MessageDialog(None, 'All channels were within acceptable ranges', "No Channels Found", wx.OK)
            result = dlg.ShowModal()
            dlg.Destroy()  
        else:
            text = 'The following channels fell out of acceptable ranges:'
            for i in brokenchans: text+= ' '+str(i)+','
            text = text[:-1]
            dlg = wx.MessageDialog(None, text, "No Channels Found", wx.OK)
            result = dlg.ShowModal()
            dlg.Destroy()  
            
        #Produce plots of the potential problem channels
        if brokenchans:
            runobjs = [file1, file2]
            titles = [title1, title2]       
                    
            funcs = []
            ychans = brokenchans
            ymins = []
            ymaxs = []
            yscales = []
            yoffsets = []
            yxforms = []
            ychanlists = []
            for i in ychans:
                funcs.append('=$'+str(i))
                ymins.append(0)
                ymaxs.append(0)
                yscales.append(1)
                yoffsets.append(0)
                yxforms.append(0)
                ychanlists.append([i])
                    
            iniData = {'numchans':len(brokenchans), 'funcs':funcs, 'ychans':ychans, 'ymins':ymins, 'ymaxs':ymaxs,
                            'yscales':yscales, 'yoffsets':yoffsets, 'yxforms':yxforms, 'ychanlists':ychanlists}
                
            plotData = PlotPageWrapped(runobjs, iniData = iniData)
            frame = MultiCanvasFrame(plotData, titles, 0)
            frame.Show()
        return True
    
class ExclusionFrame(wx.Frame):
    """
        Frame that handles changing which channels are excluded from comparison
    """
    def __init__(self, parent):        
        wx.Frame.__init__(self, parent, -1, "Exclusion List",
                          style = wx.DEFAULT_FRAME_STYLE^(wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER))
        names = []
        excluded = []
        
        #Load a the list of channel names and the list of currently excluded channels
        file = open("lib/std_channel_table.txt")
        for line in file.readlines():
            names.append(line.rstrip().split(' - ')[-1])
        file.close()
        file = open("lib/BoS_ignore_channels.txt")
        for line in file.readlines():
            line = int(line)
            if not line >= len(names):
                excluded.append(line)
        file.close()
        
        panel = wx.Panel(self)
        
        #Create a listbox with all the channel names and the excluded channels checked
        self.checklist = wx.CheckListBox(panel, -1, choices = names, size = (400, 600))
        OKButton = wx.Button(panel,-1,'OK', size = (197.5, 25))     
        CancelButton = wx.Button(panel,-1,'Cancel', size = (197.5, 25))   
        self.checklist.SetChecked(excluded)  
        self.Bind(wx.EVT_BUTTON,self.onOK,OKButton)
        self.Bind(wx.EVT_BUTTON,self.onCancel,CancelButton)
        
        buttonSizer = wx.FlexGridSizer(cols = 2, hgap = 5, vgap = 5)
        buttonSizer.AddGrowableCol(0)
        buttonSizer.AddGrowableCol(1)
        buttonSizer.Add(OKButton, wx.EXPAND)
        buttonSizer.Add(CancelButton, wx.EXPAND)
        
        mainSizer = wx.FlexGridSizer(cols = 1, hgap = 5, vgap = 5)
        mainSizer.AddGrowableCol(0); mainSizer.AddGrowableRow(0)
        mainSizer.Add(self.checklist, wx.EXPAND)
        mainSizer.Add(buttonSizer, wx.EXPAND)
        
        panel.SetSizer(mainSizer)
        mainSizer.SetSizeHints(self)
        
        self.names = names
        
    def onOK(self, evt):
        """
            Save which channels are checked back to the file
        """
        text = ''
        for i in self.checklist.GetChecked():
            text+=str(i)+'\n'
        if text: text = text[:-1]
        file = open("lib/BoS_ignore_channels.txt", "wt")
        file.write(text)
        file.close()
        self.Destroy()
        
    def onCancel(self, evt):
        self.Destroy()

def max(iter):
        """ 
            Iterate through an iterable and find the maximum value.  Also return the 
            index at which the max is.
            This is done primarily to avoid wierdness with the index function where it
            was unable to find floats that were definately in the list.
        """
        index = 0
        value = iter[0]
        for i in range(len(iter)):
            if iter[i] > value:
                value = iter[i]
                index = i
        return value, index
        
def min(iter):
        """ 
            Iterate through an iterable and find the minimum value.  Also return the 
            index at which the max is.
            This is done primarily to avoid wierdness with the index function where it
            was unable to find floats that were definately in the list.
        """
        index = 0
        value = iter[0]
        for i in range(len(iter)):
            if iter[i] < value:
                value = iter[i]
                index = i
        return value, index
    

if __name__ == "__main__":
    app = wx.PySimpleApp(redirect=False)
    frame = CorrelateFrame()
    frame.Show()
    app.MainLoop()
