"""
This module provides a calfile class for handling Autonomous
Model calibration files.  It is used by various AM software tools
that need to handle the standard cal file format.

The class provides the following methods and attributes:

Methods:
    '__init__' -- Creates a parser object using the cfgparse module and a
                    passed in filename
                    
    'parseall'    -- Parses the cal file to retrieve the calibration info
    
Members:
    
    
Credits:
    Sam Cubbage - 06/07/06

This class makes use of the cfgparse module

"""

__version__ = 1.0
__author__ = "Sam Cubbage"

import cfgparse, os
from Numeric import *

class Calfile:
    """ This class implements a calibration file object that is used to
    read and parse Autonomous Model calibration files"""
    
    def __init__(self, fname, dirname = '.'):
        """ Initialize the calfile object to the given file and path"""
        
        if dirname == '.':
            dirname = os.getcwd()
        
        fullpath = os.path.join(dirname, fname)
        if not os.path.isfile(fullpath):
            print "ERROR - Could not find calibration file: %s" % fullpath
        self.c = cfgparse.ConfigParser()
        self.c.add_file(fullpath)

        #  Set up some variables to hold the cal values
        self.gains = []
        self.zeros = []
        self.sys_names = []
        self.alt_names = []
        self.data_pkt_locs = []
        self.eng_units = []
        self.cal_dates = []
        
        self.rotor={}
	self.stator={}
    
    
    def parseall(self):
        """ This routine parses all of the info out of the cal file."""
        
        # First is the header information
        self.channels = self.c.add_option('obc_channels', type='int').get()
        self.calfile_version = self.c.add_option('cal_file_version', type='int').get()
        self.rotor['installed'] = self.c.add_option('rotor').get().upper()
        self.stator['installed'] = self.c.add_option('stator').get().upper()
        self.SOF1 = self.c.add_option('SOF1').get().upper()
        self.SOF2 = self.c.add_option('SOF2').get().upper()
        self.kistler = self.c.add_option('kistler').get().upper()
        self.num_6DOF = self.c.add_option('num_6DOF_dynos', type='int').get()
        
        
        # Second - Get the normal channels cals
        for channel in range(self.channels):
          self.gains.append(self.c.add_option('gain', type='float', keys='CHAN%d' % channel).get())
          self.zeros.append(self.c.add_option('zero', type='float', keys='CHAN%d' % channel).get())
          self.sys_names.append(self.c.add_option('sys_name', keys='CHAN%d' % channel).get())
          self.alt_names.append(self.c.add_option('alt_name', keys='CHAN%d' % channel).get())
          self.data_pkt_locs.append(self.c.add_option('data_pkt_loc', type='int', keys='CHAN%d' % channel).get())
          self.eng_units.append(self.c.add_option('eng_units', keys='CHAN%d' % channel).get())
          self.cal_dates.append(self.c.add_option('cal_date', keys='CHAN%d' % channel).get())
          
        # Third - Process the special gauges
        if self.rotor['installed'] == "TRUE":
            self.rotor['Fx_chan'] = self.c.add_option('Fx', type='int', keys='ROTOR').get()
            self.rotor['Fy_chan'] = self.c.add_option('Fy', type='int', keys='ROTOR').get()
            self.rotor['Fz_chan'] = self.c.add_option('Fz', type='int', keys='ROTOR').get()
            self.rotor['Mx_chan'] = self.c.add_option('Mx', type='int', keys='ROTOR').get()
            self.rotor['My_chan'] = self.c.add_option('My', type='int', keys='ROTOR').get()
            self.rotor['Mz_chan'] = self.c.add_option('Mz', type='int', keys='ROTOR').get()
      
            self.rotor['weight'] = self.c.add_option('weight', type = 'float', keys='ROTOR').get()
            self.rotor['arm'] = self.c.add_option('arm', type = 'float', keys='ROTOR').get()

            rows = []
            for i in range(1,7):
                row = []
                rowstr = self.c.add_option('int_row%d' % i, keys='ROTOR').get()
                cols = rowstr.strip().split()
                for col in cols:
                    row.append(float(col))
                rows.append(row)
        
            self.rotor['Int_Mat'] = array(rows, Float)
            
            rows = []
            for i in range(1,7):
                row = []
                rowstr = self.c.add_option('orient_row%d' % i, keys='ROTOR').get()
                cols = rowstr.strip().split()
                for col in cols:
                    row.append(float(col))
                rows.append(row)
        
            self.rotor['Orient_Mat'] = array(rows, Float)
             
        if self.stator['installed'] == "TRUE":
            self.stator['Fx_chan'] = self.c.add_option('Fx', type='int', keys='STATOR').get()
            self.stator['Fy_chan'] = self.c.add_option('Fy', type='int', keys='STATOR').get()
            self.stator['Fz_chan'] = self.c.add_option('Fz', type='int', keys='STATOR').get()
            self.stator['Mx_chan'] = self.c.add_option('Mx', type='int', keys='STATOR').get()
            self.stator['My_chan'] = self.c.add_option('My', type='int', keys='STATOR').get()
            self.stator['Mz_chan'] = self.c.add_option('Mz', type='int', keys='STATOR').get()
      
            self.stator['weight'] = self.c.add_option('weight', type = 'float', keys='STATOR').get()
            self.stator['arm'] = self.c.add_option('arm', type = 'float', keys='STATOR').get()

            rows = []
            for i in range(1,7):
                row = []
                rowstr = self.c.add_option('int_row%d' % i, keys='STATOR').get()
                cols = rowstr.strip().split()
                for col in cols:
                    row.append(float(col))
                rows.append(row)
        
            self.stator['Int_Mat'] = array(rows, Float)
            
            rows = []
            for i in range(1,7):
                row = []
                rowstr = self.c.add_option('orient_row%d' % i, keys='STATOR').get()
                cols = rowstr.strip().split()
                for col in cols:
                    row.append(float(col))
                rows.append(row)
        
            self.stator['Orient_Mat'] = array(rows, Float)
         
if __name__ == '__main__':
    cfile = Calfile('cal.ini', '.')
    cfile.parseall()
    print "Channels:", cfile.channels
    print "Gains:", cfile.gains
