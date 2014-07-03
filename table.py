#!/usr/bin/env python
# Table.py
#
# Copyright (C) 2014 - Robert F. Bussink III
# 		          
#  This program is part of the Autonomous Model Software Tools Package
# 
"""
This class defines a Table frame that allows users to tabulate analyzed
model data from ".STT files.  The frame can be standalone or is normally
called from the AM_tools utility

"""
import xlrd
import xlwt
import wx
import wx.grid
import os
import math

class TableFrame(wx.Frame):
    
    
    def __init__(self):
        
        
        self.click = 0
        self.v=[[]*500 for x in xrange(500)]
        self.stats_all = [[]*500 for x in xrange(500)]
        wx.Frame.__init__(self, None, -1, 'Input Runs for Table',size=(540,150), pos=(100,400))
        self.SetBackgroundColour(wx.NamedColor("LIGHTGREY"))

        self.runBtn = wx.Button(self, -1, "Load Runs", pos = (10,10))
        self.Bind(wx.EVT_BUTTON, self.OnFileClick, self.runBtn)
        self.writeBtn = wx.Button(self, -1, "Write Table", pos = (10,75))
        self.Bind(wx.EVT_BUTTON, self.OnWriteClick, self.writeBtn)
        self.clearBtn = wx.Button(self, -1, "Clear Table", pos = (10,42.5))
        self.Bind(wx.EVT_BUTTON, self.OnClearClick, self.clearBtn)

        # Instructions for Button use  
        self.runnumText_wr = wx.StaticText(self, -1, "Click to write xls file and clear displayed table for new table",pos=(150,80))
        self.runnumText_ld = wx.StaticText(self, -1, "Click 'Load Runs' to Load '.STT' files and display the table",pos=(150,20))
        self.runnumText_Cl = wx.StaticText(self, -1, "Click 'Clear Table' to Clear data displayed in the table",pos=(150,50))

        # Layout Screen - Set up the layout with sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.SetSizer(mainSizer)
        self.Fit()
############################################################################
#   Define the write Button
############################################################################    
    def OnWriteClick(self, evt):
        
        

        # Hide previouse table frame from screen
        try:
            frame1.Hide()
        except NameError:             # Circumvent first click on button with no table frame error
            pass
        except wx._core.PyDeadObjectError:
            pass

        try:
            runPath = self.runFile[:-10]
        except:
            runPath = '/disk2/home/'+os.environ['USER']+'/rcmdata' 
        # Open "File Open Dialog" window   
        dlg = wx.FileDialog(self, "Choose File Name to Save",
                                defaultDir=runPath, wildcard="*.xls",
                                style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename2 = dlg.GetPath()
        dlg.Destroy()



        
        # Create excel workbook to save table to

        workbook = xlwt.Workbook(encoding='ascii')    
        worksheet = workbook.add_sheet('My_Sheet')
      
        try:
            header = self.stats_all[0].split(",") #split header string into individual strings for col labels 
            for k in range(0,len(header)-1):
                worksheet.write(0, k+1, label = header[k])  # write to workbook       
            
            for count in range(1,self.click+1):
                self.v[count] = str(self.v[count])    
                self.stats_all[count] = self.stats_all[count].split(",")
                worksheet.write(count,0, label = self.v[count]) 
                stats = self.stats_all[count]
                
                
                
                for k in range(1,len(self.stats_all[count])-1):
                    worksheet.write(count, k, label = float(stats[k])) # write stats from .STT' file as foating point number
            # empty table arrays to reset for next table
            self.stats_all = [[]*500 for x in xrange(500)]
            self.v = [[]*500 for x in xrange(500)]
            self.click = 0
            workbook.save(self.filename2)
        except AttributeError:
            pass
    
############################################################################
#   Define the Clear Button
############################################################################    
    def OnClearClick(self, evt):  
        

        # Hide previouse table frame from screen
        try:
            frame1.Hide()
        except NameError:             # Circumvent first click on button with no table frame error
            pass
        except wx._core.PyDeadObjectError:
            pass
        # empty table arrays to reset for next table
        self.stats_all = [[]*500 for x in xrange(500)]
        self.v = [[]*500 for x in xrange(500)]
        self.click = 0
        



############################################################################
#   Define the load files Button    
############################################################################
    def OnFileClick(self, evt):


        try:
            del(self.filelist)
        except AttributeError:
            pass

        # Hide previouse table frame from screen
        try:
            frame1.Hide()
        except NameError:
            pass
        except wx._core.PyDeadObjectError:
            pass

        """ 
            Pops up a dialog to choose the run and then opens and 
            loads the run into memory
        """
        try:
            runPath = self.runFile[:-10]
        except:
            runPath = '/disk2/home/'+os.environ['USER']+'/rcmdata' 
        # Open "File Save Dialog" window      
        dlg = wx.FileDialog(self, "Choose Run File for Table",
                                defaultDir=runPath, wildcard="*.STT",
                                style=wx.MULTIPLE)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.filelist = dlg.GetPaths()
            self.filename = dlg.GetPath()
        dlg.Destroy()
        #  Generate array to display in table frame window
        try:
            click_p = self.click
            self.click = self.click + len(self.filelist)
            for click_it in range(0, len(self.filelist)):
                data_row = [line.strip() for line in open(self.filelist[click_it])]
                header = 'Appr_Upw' +"," +data_row[11]
                dir_name=self.filelist[click_it].split("/")
                run_number = dir_name[len(dir_name)-1].split(".")[0]
                U_Pw = data_row[27][8:13].split(",")
                self.v[click_p+click_it+1] = run_number
                stats_str =  run_number+',' + U_Pw[0]+','+data_row[12]
                self.stats_all[click_p+click_it+1] = stats_str

                self.stats_all[0] = header
             
            class TestFrame(wx.Frame):
                
                for k in range(1,len(self.v)):
                    self.v[k] = str(self.v[k]) 
                rowLabels = self.v
                numrows = self.click
                colLabels = header.split(",") #split header sring for col labels
                numcols = len(colLabels)
                stats_all = self.stats_all
                
                # Create Frame with grid table for display
                def __init__(self):
                    wx.Frame.__init__(self, None, title = "Analysis Table", size=(1075,600), pos=(650,100))
                    grid = wx.grid.Grid(self)
                    grid.CreateGrid(self.numrows,self.numcols-1)
                    for col in range(self.numcols-1):
                        grid.SetColLabelValue(col, self.colLabels[col])

                    for row in range(1, self.numrows+1):
                        grid.SetRowLabelValue(row-1,self.rowLabels[row])
                        stat = str(self.stats_all[row])
                        stats = stat.split(",")
                        for col in range(1,self.numcols):
                            try:
                                grid.SetCellValue(row-1, col-1, stats[col])
                            except IndexError:
                                pass
                                
                            
            app = wx.PySimpleApp()
            frame1 = TestFrame()
            frame1.Show()
            app.MainLoop()
        except AttributeError:
            pass
        except wx._core.PyDeadObjectError:
            pass
        
            
if __name__ == "__main__":
    app = wx.PySimpleApp(redirect=False)
    frame = TableFrame()
    frame.Show()
    app.MainLoop()

