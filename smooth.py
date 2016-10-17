#!/usr/bin/env python
# smooth.py
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
import matplotlib.pyplot as plt
import numpy as np
import textwrap as tw
import matplotlib.backend_bases as beb

from plottools import *
from multicanvas import MultiCanvasFrame

class TableFrame(wx.Frame):
    
    
    def __init__(self):
        

        wx.Frame.__init__(self, None, -1, 'Input Runs for Plotting',size=(540,150), pos=(150,600))
        self.SetBackgroundColour(wx.NamedColor("LIGHTGREY"))

        self.runBtn = wx.Button(self, -1, "Load Runs", pos = (10,10))
        self.Bind(wx.EVT_BUTTON, self.OnFileClick, self.runBtn)

        # Instructions for Button use  
        self.runnumText_ld = wx.StaticText(self, -1, "Click 'Load Runs' to Load '.STT' files for Plot group",pos=(150,20))
        

        # Layout Screen - Set up the layout with sizers
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.SetSizer(mainSizer)
        self.Fit()




############################################################################
#   Define the load files Button    
############################################################################
    def OnFileClick(self, evt):
        
        click = 0
        # delete any existing filelist to avoid replication in table if no fils are selected and 'cancel' is clicked
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

        print(runPath)
        # Open "File Save Dialog" window      
        dlg = wx.FileDialog(self, "Choose Run File for Plot Group",
                                defaultDir=runPath, wildcard="*.std",
                                style=wx.MULTIPLE)
        
        if dlg.ShowModal() == wx.ID_OK:
            self.filelist = dlg.GetPaths()
            self.filename = dlg.GetPath()
        dlg.Destroy()
##############################################################################
        #  Generate array to display in table frame window
        try:
            click_p = click
            click = click + len(self.filelist)

 
            for click_it in range(0, len(self.filelist)):
                keep='no'
                stats = os.stat(self.filelist[click_it])
                if stats.st_size>0:
                   data_row = [line.strip() for line in open(self.filelist[click_it])]
                   header = data_row[4][1:15].split("'")
 
                   a=len(data_row)
                   udata=[[]*a for x in xrange(a)]
                   u2data=[[]*a for x in xrange(a)]
                   vdata=[[]*a for x in xrange(a)]
                   time=[[]*a for x in xrange(a)]
                   slope=[[]*a for x in xrange(a)]
                   drop_out=[[]*a for x in xrange(a)]
                   drop_out_V=[[]*a for x in xrange(a)]
                   drop_out_U2=[[]*a for x in xrange(a)]
                   drop_out_time=[[]*a for x in xrange(a)]
                   drop_out_neg=[[]*a for x in xrange(a)]
                   drop_out_neg_V=[[]*a for x in xrange(a)]
                   drop_out_neg_U2=[[]*a for x in xrange(a)]
                   drop_out_time_neg=[[]*a for x in xrange(a)]
                   x_data_U=[[]*a for x in xrange(a)]
                   y_data_U=[[]*a for x in xrange(a)]
                   x_data_U2=[[]*a for x in xrange(a)]
                   y_data_U2=[[]*a for x in xrange(a)]
                   x_data_V=[[]*a for x in xrange(a)]
                   y_data_V=[[]*a for x in xrange(a)]


                   
                   

                   data_row_new=data_row
                   for inc in range(6,a):
                       b=data_row[inc].split("  ")
                       data_row_new[inc]=data_row[inc].split("  ")
                       
                       udata[inc-6]=float(b[0])
                       vdata[inc-6]=float(b[1])
                       u2data[inc-6]=float(b[6])
                       time[inc-6]=float(inc*0.2)
                   
    #######################################################################
    #
    #  code for U velocity smoothing
    #
    #######################################################################
                   point=1
                   point_neg=1
                   
                   for inc in range(7,len(udata)-7):
                       slope[inc]=(udata[inc+1]-udata[inc-1])/4
                       
                       if slope[inc]>0.8:                    
                          drop_out[point] = udata[inc]
                          drop_out_V[point] = vdata[inc]
                          drop_out_U2[point] = u2data[inc]
                          drop_out_time[point] = time[inc]
                          point=point+1

                       if slope[inc]<-0.8:                    
                          drop_out_neg[point_neg] = udata[inc]
                          drop_out_neg_V[point_neg] = vdata[inc]
                          drop_out_neg_U2[point_neg] = u2data[inc]
                          drop_out_time_neg[point_neg] = time[inc]
                          point_neg=point_neg+1
    #####################################################################
    #
    #    if condition statements for good data and bad end data
    #
    #####################################################################
                   
                   if point>1 and point_neg>1:
##                      stdfile=open(self.filelist[click_it],'r')
##                      
##                      newfile = open(self.filelist[click_it]+'new', 'w')
##                               # Copy the first three line over
##                      for x in range(6):
##                          newfile.write(stdfile.readline())
##                       
                   
                      
                      plt.plot(time[0:a-10],udata[0:a-10])
                      plt.plot(time[0:a-10],vdata[0:a-10])
                      plt.plot(time[0:a-10],u2data[0:a-10])
                      plt.legend(('small u', 'small v', 'Big U'))

                      plt.plot(time[100:len(udata)-100],slope[100:len(udata)-100], 'k')


                      plt.scatter(drop_out_time[1:point],drop_out[1:point], c='blue')
                      plt.scatter(drop_out_time_neg[1:point_neg],drop_out_neg[1:point_neg],c='red')
                 
                      var=0
                      power=1
                      inc_var=0
                      inc_var_d=0
                      
                      for inc in range(1,point,2):
                          dumb=inc+inc_var+inc_var_d
                          switch='no'

                          for inc_check in range(1,point_neg,2):
                              if drop_out_time[inc+1]<drop_out_time_neg[inc_check] and drop_out_time[inc+3] and drop_out_time[inc+3]>drop_out_time_neg[inc_check]:
                                 switch='yes'


                          if inc+2==point:
                             switch='yes'
                             

                          if switch=='no':
                              inc_var_d=inc_var_d-2
                             


                          if drop_out_time[inc+3] and drop_out_time_neg[dumb+3] and drop_out_time[inc+3]<drop_out_time_neg[dumb]:
                             diff=(drop_out_time[inc+1]-drop_out_time_neg[dumb])
                             var=drop_out_time[inc+1]

                          if drop_out_time_neg[dumb]<var and drop_out[inc+1] and drop_out_time_neg[inc]:
                             inc_var=2
                             dumb=inc+inc_var
 

                          if drop_out_time[inc+1] and drop_out_time_neg[dumb] and (drop_out_time[inc+1]-drop_out_time_neg[dumb])<0: 
                             inc_var=inc_var-2
                             dumb=inc_var + dumb
                             diff=(drop_out_time[inc+1]-drop_out_time_neg[dumb])

                          
                          if drop_out_time_neg[dumb]>var and switch=='yes' and drop_out_time[inc+1] and drop_out_time_neg[dumb] and (drop_out_time[inc+1]-drop_out_time_neg[dumb])>0 and (drop_out_time[inc+1]-drop_out_time_neg[dumb])<100:
                             
                              
                             var=drop_out_time[inc+1]
                             time_diff=int((drop_out_time[inc+1]-drop_out_time_neg[dumb])/0.2)
           
                             increment=0.2

                             pfit=np.polyfit([drop_out_time_neg[dumb],drop_out_time[inc+1]],[drop_out_neg[dumb],drop_out[inc+1]],power)
                             for t_inc in range(1,time_diff+2,1):
                                 y_data_U[t_inc]=0
                                 x_data_U[t_inc]=drop_out_time_neg[dumb]+increment*(t_inc-1)
                                 for add_pow in range(0,power+1):                       
                                     y_data_U[t_inc]=y_data_U[t_inc]+(pfit[add_pow])*(x_data_U[t_inc])**(power-add_pow)
                                 bnew = data_row_new[int(drop_out_time_neg[dumb]/0.2)+t_inc]
                                 bnew[0]= str(" %12.5e " % y_data_U[t_inc])
                                 data_row_new[int(drop_out_time_neg[dumb]/0.2)+t_inc]=bnew
                                  
                             
                              
                             pfit=np.polyfit([drop_out_time_neg[dumb],drop_out_time[inc+1]],[drop_out_neg_V[dumb],drop_out_V[inc+1]],power)
                             for t_inc in range(1,time_diff+2,1):
                                 y_data_V[t_inc]=0
                                 x_data_V[t_inc]=drop_out_time_neg[dumb]+increment*(t_inc-1)
                                 for add_pow in range(0,power+1):                       
                                     y_data_V[t_inc]=y_data_V[t_inc]+(pfit[add_pow])*(x_data_V[t_inc])**(power-add_pow)
                                 bnew = data_row_new[int(drop_out_time_neg[dumb]/0.2)+t_inc]
                                 bnew[1]= str(" %12.5e " % y_data_V[t_inc])
                                 data_row_new[int(drop_out_time_neg[dumb]/0.2)+t_inc]=bnew

                             pfit=np.polyfit([drop_out_time_neg[dumb],drop_out_time[inc+1]],[drop_out_neg_U2[dumb],drop_out_U2[inc+1]],power)
                             for t_inc in range(1,time_diff+2,1):
                                 y_data_U2[t_inc]=0
                                 x_data_U2[t_inc]=drop_out_time_neg[dumb]+increment*(t_inc-1)
                                 for add_pow in range(0,power+1):                       
                                     y_data_U2[t_inc]=y_data_U2[t_inc]+(pfit[add_pow])*(x_data_U2[t_inc])**(power-add_pow)
                                 bnew = data_row_new[int(drop_out_time_neg[dumb]/0.2)+t_inc]
                                 bnew[6]= str(" %12.5e " % y_data_U2[t_inc])
                                 data_row_new[int(drop_out_time_neg[dumb]/0.2)+t_inc]=bnew

                           
                             current_plot=plt.plot(x_data_U[1:time_diff+2],y_data_U[1:time_diff+2],'k')
                             current_plot=plt.plot(x_data_V[1:time_diff+2],y_data_V[1:time_diff+2],'k')
                             current_plot=plt.plot(x_data_U2[1:time_diff+2],y_data_U2[1:time_diff+2],'k')
                             
                             plt.title(self.filelist[click_it].split("/")[len(self.filelist[click_it].split("/"))-1])
                             
                             plt.show()
                             

                      choices_d =["keep patchs and save", "don't save"]
                      dialog_pop = wx.SingleChoiceDialog(None, "Make up your mind!", "Keep data or not?", choices_d)
                      if dialog_pop.ShowModal() == wx.ID_OK:
                         keep=dialog_pop.GetStringSelection()
                      dialog_pop.Destroy()

                   else:
                      print("ok" , self.filelist[click_it], keep)


                             
                         

         #######################################################################
         #
         #  save data to file
         #
         #######################################################################

                   

                   if keep=="keep patchs and save":



                      stdfile=open(self.filelist[click_it],'r')
                      newfile = open(self.filelist[click_it]+'new', 'w')
                               # Copy the first three line over
                      for x in range(6):
                          newfile.write(stdfile.readline())
                      


                      
                      col_len=len(data_row_new[6])
                      for inc_row in range(6,a):
                          for col_inc in range(0,col_len):
                             newfile.write(" %12.5e " % float(data_row_new[inc_row][col_inc]))
                          newfile.write('\n')
                      stdfile.close()
                      newfile.close()
                      plt.close()

                      os.remove(self.filelist[click_it])
                      os.rename(self.filelist[click_it]+'new', self.filelist[click_it])
                      
                      
                   if keep=="no" or keep=="don't save":
                      plt.close()

                   
                
                udata=[[]*a for x in xrange(a)]
                u2data=[[]*a for x in xrange(a)]
                vdata=[[]*a for x in xrange(a)]
                time=[[]*a for x in xrange(a)]
                slope=[[]*a for x in xrange(a)]
                drop_out=[[]*a for x in xrange(a)]
                drop_out_V=[[]*a for x in xrange(a)]
                drop_out_U2=[[]*a for x in xrange(a)]
                drop_out_time=[[]*a for x in xrange(a)]
                drop_out_neg=[[]*a for x in xrange(a)]
                drop_out_neg_V=[[]*a for x in xrange(a)]
                drop_out_neg_U2=[[]*a for x in xrange(a)]
                drop_out_time_neg=[[]*a for x in xrange(a)]
                x_data_U=[[]*a for x in xrange(a)]
                y_data_U=[[]*a for x in xrange(a)]

                x_data_U2=[[]*a for x in xrange(a)]
                y_data_U2=[[]*a for x in xrange(a)]
                x_data_V=[[]*a for x in xrange(a)]
                y_data_V=[[]*a for x in xrange(a)]

                    

                
                    



                 

        except AttributeError:
            pass
        except wx._core.PyDeadObjectError:
            pass

            
#################################################################################            
if __name__ == "__main__":
    app = wx.PySimpleApp(redirect=False)
    frame = TableFrame()
    frame.Show()
    app.MainLoop()
