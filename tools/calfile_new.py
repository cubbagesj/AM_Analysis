# calfile_new.py
#
# Copyright (C) 2006-2007 - Samuel J. Cubbage
#
#  This program is part of the Autonomous Model Software Tools Package
#
"""
This module provides a CalFile class for handling Autonomous
Model calibration files.  It is used by various AM software tools
that need to handle the standard cal file format.

The class provides the following methods and attributes:

Methods:
    '__init__' -- Creates a parser object using the cfgparse module and a
                    passed in filename
                    
    'ParseAll'    -- Parses the cal file to retrieve the calibration info
    'ParseSingle' -- Parses the normal single channels
    'ParseGauge'  -- Parses a special gauge (SOF, Kistler etc...)
    
Members:
    
    
Credits:
    Sam Cubbage - 06/07/06

This class makes use of the cfgparse module and the Numeric module

"""

import cfgparse, os
from numpy import *

class CalFile:
    """ This class implements a calibration file object that is used to
    read and parse Autonomous Model calibration files
    
    Calibration data is returned as a set of dictionaries containing
    the values
    """
    
    def __init__(self, fname, dirname = '.'):
        """ Initialize the calfile object to the given file and path
        and read in the header info to set the special gauge flags
        """
        
        # If no dir given, use the current dir
        if dirname == '.':
            dirname = os.getcwd()
        
        fullpath = os.path.join(dirname, fname)
        if not os.path.isfile(fullpath):
            print "ERROR - Could not find calibration file: %s" % fullpath
        self.c = cfgparse.ConfigParser()
        self.c.add_file(fullpath)

        # Get the header info from the cal file
        self.channels = self.c.add_option('obc_channels', type='int').get()
        self.date = self.c.add_option('cal_file_date').get() 
        self.calfile_version = self.c.add_option('cal_file_version', type='int').get()

        # Check for the special gauges and set the flags
        self.hasRotor = self.c.add_option('rotor').get().upper()
        self.hasStator = self.c.add_option('stator').get().upper()
        self.hasSOF1 = self.c.add_option('SOF1').get().upper()
        self.hasSOF2 = self.c.add_option('SOF2').get().upper()

        # hasKistler refers to the standard 4-guage kistler
        self.hasKistler = self.c.add_option('kistler').get().upper()
        self.hasKistler3 = 'FALSE'
        try:
            self.hasKistler3 = self.c.add_option('kistler3').get().upper()
        except:
            # If key not found then set to false
            self.hasKistler3 = 'FALSE'
            
        self.num_6DOF = self.c.add_option('num_6DOF_dynos', type='int').get()           
        if self.num_6DOF > 0:
            self.has6DOF = 'TRUE'
        else:
            self.has6DOF = 'FALSE'
        # Setup the gauge item lists
        self.itemlist = {}
        
        self.itemlist['prop'] = (('Fx', 'int'),
                                 ('Fy', 'int'),
                                 ('Fz', 'int'),
                                 ('Mx', 'int'),
                                 ('My', 'int'),
                                 ('Mz', 'int'),
                                 ('weight', 'float'),
                                 ('arm', 'float'),
                                 ('position', 'int'),
                                 ('int_row1', 'string'),
                                 ('int_row2', 'string'),
                                 ('int_row3', 'string'),
                                 ('int_row4', 'string'),
                                 ('int_row5', 'string'),
                                 ('int_row6', 'string'),
                                 ('orient_row1', 'string'),
                                 ('orient_row2', 'string'),
                                 ('orient_row3', 'string'),
                                 ('orient_row4', 'string'),
                                 ('orient_row5', 'string'),
                                 ('orient_row6', 'string'),
                                 ('serial_num', 'string'))
        self.itemlist['6dof'] = (('Fx', 'int'),
                                 ('Fy', 'int'),
                                 ('Fz', 'int'),
                                 ('Mx', 'int'),
                                 ('My', 'int'),
                                 ('Mz', 'int'),
                                 ('angle', 'float'),
                                 ('int_row1', 'string'),
                                 ('int_row2', 'string'),
                                 ('int_row3', 'string'),
                                 ('int_row4', 'string'),
                                 ('int_row5', 'string'),
                                 ('int_row6', 'string'),
                                 ('orient_row1', 'string'),
                                 ('orient_row2', 'string'),
                                 ('orient_row3', 'string'),
                                 ('orient_row4', 'string'),
                                 ('orient_row5', 'string'),
                                 ('orient_row6', 'string'),
                                 ('serial_num', 'string'))
        self.itemlist['kistler'] = (('Fx1', 'int'),
                                    ('Fy1', 'int'),
                                    ('Fz1', 'int'),
                                    ('Fx2', 'int'),
                                    ('Fy2', 'int'),
                                    ('Fz2', 'int'),
                                    ('Fx3', 'int'),
                                    ('Fy3', 'int'),
                                    ('Fz3', 'int'),
                                    ('Fx4', 'int'),
                                    ('Fy4', 'int'),
                                    ('Fz4', 'int'),
                                    ('xdist', 'float'),
                                    ('ydist', 'float'),
                                    ('gagex', 'float'),
                                    ('gagey', 'float'),
                                    ('gagez', 'float'),
                                    ('armx', 'float'),
                                    ('army', 'float'),
                                    ('armz', 'float'),
                                    ('weight', 'float'),  
                                    ('int_row1', 'string'),
                                    ('int_row2', 'string'),
                                    ('int_row3', 'string'),
                                    ('int_row4', 'string'),
                                    ('int_row5', 'string'),
                                    ('int_row6', 'string'),
                                    ('orient_row1', 'string'),
                                    ('orient_row2', 'string'),
                                    ('orient_row3', 'string'),
                                    ('orient_row4', 'string'),
                                    ('orient_row5', 'string'),
                                    ('orient_row6', 'string'))
        self.itemlist['kistler3'] = (('Fx1', 'int'),
                                    ('Fy1', 'int'),
                                    ('Fz1', 'int'),
                                    ('Fx2', 'int'),
                                    ('Fy2', 'int'),
                                    ('Fz2', 'int'),
                                    ('Fx3', 'int'),
                                    ('Fy3', 'int'),
                                    ('Fz3', 'int'),
                                    ('xdist', 'float'),
                                    ('ydist', 'float'),
                                    ('gagex', 'float'),
                                    ('gagey', 'float'),
                                    ('gagez', 'float'),
                                    ('armx', 'float'),
                                    ('army', 'float'),
                                    ('armz', 'float'),
                                    ('weight', 'float'),  
                                    ('int_row1', 'string'),
                                    ('int_row2', 'string'),
                                    ('int_row3', 'string'),
                                    ('int_row4', 'string'),
                                    ('int_row5', 'string'),
                                    ('int_row6', 'string'),
                                    ('orient_row1', 'string'),
                                    ('orient_row2', 'string'),
                                    ('orient_row3', 'string'),
                                    ('orient_row4', 'string'),
                                    ('orient_row5', 'string'),
                                    ('orient_row6', 'string'))

    def ParseAll(self):
        """ This routine parses all of the info out of the cal file.  It calls
        the individual parse methods for each of the gauges based on the gauge
        flags.  Each of the special gauge parse routines will return a
        dictionary with the cal info
        """
        
        # Single channels are not in a dictionary
        self.ParseSingle()
        
        # Special gauges based on the gauge flags
        if self.hasRotor == "TRUE":
            self.rotor = self.ParseGauge('ROTOR', type='prop')
        if self.hasStator == "TRUE":
            self.stator = self.ParseGauge('STATOR', type='prop')
        if self.hasKistler == "TRUE":
            self.kistler = self.ParseGauge('KISTLER', type='kistler')
        if self.hasKistler3 == "TRUE":
            self.kistler3 = self.ParseGauge('KISTLER3', type='kistler3')
        if self.hasSOF1 == "TRUE":
            self.SOF1 = self.ParseGauge('SOF1', type='6dof')
        if self.hasSOF2 == "TRUE":
            self.SOF2 = self.ParseGauge('SOF2', type='6dof')
        if self.has6DOF == "TRUE":
            self.sixDOF = []
            for i in range(self.num_6DOF):
                self.sixDOF.append(self.ParseGauge('6DOF%d'% (i+1), type='6dof'))
  
    def ParseSingle(self):
        """ Retrieve the single channel calibrations from the cal file
        These are always present so there is no need for a flag like the special
        gauges
        """
        
        #  Set up some variables to hold the cal values
        self.gains = []
        self.zeros = []
        self.sys_names = []
        self.alt_names = []
        self.data_pkt_locs = []
        self.eng_units = []
        self.cal_dates = []
        
        # Read the calibration info
        for channel in range(self.channels):
          self.gains.append(self.c.add_option('gain', type='float', keys='CHAN%d' % channel).get())
          self.zeros.append(self.c.add_option('zero', type='float', keys='CHAN%d' % channel).get())
          self.sys_names.append(self.c.add_option('sys_name', keys='CHAN%d' % channel).get())
          self.alt_names.append(self.c.add_option('alt_name', keys='CHAN%d' % channel).get())
          self.data_pkt_locs.append(self.c.add_option('data_pkt_loc', type='int', keys='CHAN%d' % channel).get())
          self.eng_units.append(self.c.add_option('eng_units', keys='CHAN%d' % channel).get())
          self.cal_dates.append(self.c.add_option('cal_date', keys='CHAN%d' % channel).get())
            
    def ParseGauge(self, section, type='6dof'):
        """ Read in the cal info for the gauge.  Items to read is based on
        the type and section tells where to read from
        """
        
        gauge = {}
        for item, itype in self.itemlist[type]:
            try:
                gauge[item] = self.c.add_option(item, type=itype, keys=section).get()
            except:
                gauge[item] = None
      
        # Build the interaction/orient matrices
        rows = []
        for i in range(1,7):
            row = []
            rowstr = gauge['int_row%d' % i]
            cols = rowstr.strip().split()
            for col in cols:
                row.append(float(col))
            rows.append(row)
    
        gauge['Int_Mat'] = array(rows, dtype=float)
        
        rows = []
        for i in range(1,7):
            row = []
            rowstr = gauge['orient_row%d' % i]
            cols = rowstr.strip().split()
            for col in cols:
                row.append(float(col))
            rows.append(row)
    
        gauge['Orient_Mat'] = array(rows, dtype=float)
        
        return gauge    
        
if __name__ == '__main__':
    cfile = CalFile('cal.ini', '.')
    cfile.ParseAll()
    print "Channels:", cfile.channels
    print "Gains:", cfile.gains
    print "Rotor Fx:", cfile.rotor['Fx']
