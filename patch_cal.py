#!/usr/bin/env python
# patch_cal.py
#
# Copyright (C) 2012 - Samuel J. Cubbage
#
# This program is part of the Autonomous Model Software Tools Package
#
# a wxPython program to facilitate patching AM cal files to update channel cals
#
# 9/13/2012

import os, time
import wx
import wx.aui
import wx.html
import socket, struct
from pylab import *
import glob


obcDir = '/frmg/Autonomous_Model/Test_Data'


class PatchFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title="Cal Patch", size=(650,700))
        self.SetBackgroundColour(wx.NamedColour("LIGHTGREY"))

        self.dataDir = '/frmg/Autonomous_Model/Test_Data/'

        #select files section
        fileLabel = wx.StaticText(self, -1, "Files to Patch:")

        self.dirpick = wx.DirPickerCtrl(self, -1, path=self.dataDir, message="Choose Directory")
        self.dirpick.SetTextCtrlGrowable(grow=True)
        self.dirpick.SetTextCtrlProportion(1)
        self.dirpick.SetPickerCtrlProportion(0)
        self.fileList = wx.CheckListBox(self, -1, size=(200,200), style=wx.LB_MULTIPLE)

        self.Bind(wx.EVT_DIRPICKER_CHANGED,  self.OnDirPick, self.dirpick)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck, self.fileList)


        #Now do the Layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(fileLabel, 0, wx.ALL, 5)

        fileSizer = wx.FlexGridSizer(cols=1, hgap=5, vgap=5)
        fileSizer.AddGrowableCol(0)
        fileSizer.Add(self.dirpick, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        fileSizer.Add(self.fileList, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        mainSizer.Add(fileSizer, 0, wx.EXPAND|wx.ALL, 5)



        self.SetSizer(mainSizer)
        self.Layout()
        self.Fit()


        # add a status bar
        self.statusbar = self.CreateStatusBar()

        # build the menubar
        self.createMenuBar()

    def OnDirPick(self, evt):
        global obcDir
        self.dataDir = self.dirpick.GetPath()
        obcDir = self.dataDir
        runsToMerge = []
        self.fileList.Set(self.getFiles())

    def getFiles(self):
        obcfiles = []
        
        for file in glob.glob(os.path.join(self.dataDir,'*.cal')):
            head, tail = os.path.split(file)
            name, ext = os.path.splitext(tail)
            obcfiles.append(name)
        return obcfiles
 
    def OnCheck(self, evt):
        global runsToMerge
        runsToMerge = []
        for item in range(self.fileList.GetCount()):
            if self.fileList.IsChecked(item):
                try:
                    runsToMerge.index(self.fileList.GetString(item))
                except:
                    runsToMerge.append(self.fileList.GetString(item))
    
    def menuData(self):
        return (("&File",
                 ("&Quit", "Quit", self.OnCloseWindow)),
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


    def OnFileClick(self, event):
        pass


    def OnCloseWindow(self, event):
        self.Destroy()

    def OnAbout(self, event):
        dlg = ToolsAbout(self)
        dlg.ShowModal()
        dlg.Destroy()

class ToolsAbout(wx.Dialog):
    text = '''
    <html>
    <body bgcolor="ACAA60">
    <center><table bgcolor="#455481" width="100%" cellspacing="0"
    cellpadding="0" border="1">
    <tr>
        <td align="center"><h1>Cal_Patch</h1></td>
    </tr>
    </table>
    </center>
    <p><b>Patch_Cal</b> is a tool to patch
    the Autonomous Model cal files</p>

    <p><b>Patch_Cal</b> is brought to you by Sam Cubbage, Copyright &copy; 2012.</p>
    </body>
    </html>
    '''
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, 'About Patch_Cal', size=(440, 400) )

        html = wx.html.HtmlWindow(self)
        html.SetPage(self.text)
        button = wx.Button(self, wx.ID_OK, "Okay")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(button, 0, wx.ALIGN_CENTER|wx.ALL, 5)

        self.SetSizer(sizer)
        self.Layout()


if __name__ == "__main__":
    os.chdir('..')

    app = wx.PySimpleApp(0)
    frame = PatchFrame()
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
