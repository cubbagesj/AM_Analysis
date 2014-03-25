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

class CalFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, title="Cal Patch", size=(650,700))

        # Create the notebook control
        nb = wx.aui.AuiNotebook(self)

        # Add the pages to the notebook
        for eachPage, eachTitle in self.pageData():
            nb.AddPage(eachPage(nb), eachTitle)

        # add a status bar
        self.statusbar = self.CreateStatusBar()

        # build the menubar
        self.createMenuBar()


    def pageData(self):
        return ((self.makeSinglePanel, "Patch Single"),
                (self.makeBatchPanel, "Patch Batch"))

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

    def makeSinglePanel(self, parent):

        # Make the basic panel
        p = wx.Panel(parent, -1, style=wx.SUNKEN_BORDER)

        # Create the decorations
        topLbl = wx.StaticText(p, -1, "Select File")
        topLbl.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))

 

        patchBtn = wx.Button(p, -1, "Patch")
        patchBtn.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL))



        #Now do the Layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(topLbl, 0, wx.ALL, 5)
        mainSizer.Add(wx.StaticLine(p), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)

        mainSizer.Add(patchBtn, 0, wx.ALL, 10)
        p.SetSizer(mainSizer)
        p.Layout()
        p.Fit()

        return p

    def makeBatchPanel(self, parent):
        p = wx.Panel(parent, -1, style=wx.SUNKEN_BORDER)
        
        topLbl = wx.StaticText(p, -1, "Select Files")
        topLbl.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(topLbl, 0, wx.ALL, 5)
        mainSizer.Add(wx.StaticLine(p), 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 5)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)


        p.SetSizer(mainSizer)

        return p

    def OnBoatChoice(self, evt):
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
    frame = CalFrame()
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()