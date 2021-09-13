# tdms_calfile.py
#
# Copyright (C) 2006-20021 - Samuel J. Cubbage
#
#  This program is part of the Autonomous Model Software Tools Package
#
"""
This module provides a TdmsCalFile class for extracting the 6DOF
calibration information from the new TDMS files on CB12.  The information
is now embedded into the TDMS file in the file properties section

This class mimics the standard CalFile class and returns the needed
6DOF information in the same format as the normal version

The class provides the following methods and attributes:

Methods:
    '__init__' -- Creates a parser object using the cfgparse module and a
                    passed in filename

    'ParseAll'    -- Parses the cal file to retrieve the calibration info
    'ParseSingle' -- Parses the normal single channels
    'ParseGauge'  -- Parses a special gauge (SOF, Kistler etc...)

Members:


Credits:
    Sam Cubbage - 09/10/2021


"""

import numpy as np

class TdmsCalFile:
    """ This class extracts the 6DOF calibration information from the
    Tdms file properties

    Calibration data is returned as a set of dictionaries containing
    the values
    """

    def __init__(self, tdms_file):
        """ Initialize the calfile object to the given file and path
        and read in the header info to set the special gauge flags
        """
        self.tdms_file = tdms_file

        # Check for the special gauges and set the flags
        self.hasRotor = tdms_file.properties['DEFAULT_rotor'].strip().upper()
        self.hasStator = tdms_file.properties['DEFAULT_stator'].strip().upper()
        self.hasSOF1 = tdms_file.properties['DEFAULT_SOF1'].strip().upper()
        self.hasSOF2 = tdms_file.properties['DEFAULT_SOF2'].strip().upper()

        # hasKistler refers to the standard 4-guage kistler
        self.hasKistler = tdms_file.properties['DEFAULT_kistler'].strip().upper()
        self.hasKistler3 = 'FALSE'

        # Added Kistler 3 but not all old files have it so handle missing flag
        try:
            self.hasKistler3 = tdms_file.properties['DEFAULT_kistler3'].strip().upper()
        except:
            # If key not found then set to false
            self.hasKistler3 = 'FALSE'

        # For SSGN needed 2 3 button kistlers so add a new type, kistler3_2
        #  but not all old files have it so handle missing flag
        try:
            self.hasKistler3_2 = tdms_file.properties['DEFAULT_kistler3_2'].strip().upper()
        except:
            # If key not found then set to false
            self.hasKistler3_2 = 'FALSE'

        # Deck no longer used
        self.hasDeck = 'FALSE'

        # Not using 6DOF appendage dynos either
        self.has6DOF = 'FALSE'

        # Setup the gauge item lists
        self.itemlist = {}

        self.itemlist['prop'] = (('Fx', 'string'),
                                 ('Fy', 'string'),
                                 ('Fz', 'string'),
                                 ('Mx', 'string'),
                                 ('My', 'string'),
                                 ('Mz', 'string'),
                                 ('weight', 'float'),
                                 ('arm', 'float'),
                                 ('armx', 'float'),
                                 ('army', 'float'),
                                 ('armz', 'float'),
                                 ('position', 'float'),
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
        self.itemlist['6dof'] = (('Fx', 'string'),
                                 ('Fy', 'string'),
                                 ('Fz', 'string'),
                                 ('Mx', 'string'),
                                 ('My', 'string'),
                                 ('Mz', 'string'),
                                 ('weight', 'float'),
                                 ('arm', 'float'),
                                 ('armx', 'float'),
                                 ('army', 'float'),
                                 ('armz', 'float'),
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
        self.itemlist['kistler'] = (('Fx1', 'string'),
                                    ('Fy1', 'string'),
                                    ('Fz1', 'string'),
                                    ('Fx2', 'string'),
                                    ('Fy2', 'string'),
                                    ('Fz2', 'string'),
                                    ('Fx3', 'string'),
                                    ('Fy3', 'string'),
                                    ('Fz3', 'string'),
                                    ('Fx4', 'string'),
                                    ('Fy4', 'string'),
                                    ('Fz4', 'string'),
                                    ('xdist', 'float'),
                                    ('ydist', 'float'),
                                    ('gagex', 'float'),
                                    ('gagey', 'float'),
                                    ('gagez', 'float'),
                                    ('arm', 'float'),
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
        self.itemlist['kistler3'] = (('Fx1', 'string'),
                                     ('Fy1', 'string'),
                                     ('Fz1', 'string'),
                                     ('Fx2', 'string'),
                                     ('Fy2', 'string'),
                                     ('Fz2', 'string'),
                                     ('Fx3', 'string'),
                                     ('Fy3', 'string'),
                                     ('Fz3', 'string'),
                                     ('xdist', 'float'),
                                     ('ydist', 'float'),
                                     ('gagex', 'float'),
                                     ('gagey', 'float'),
                                     ('gagez', 'float'),
                                     ('arm', 'float'),
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

        
        # Special gauges based on the gauge flags
        if self.hasRotor == "TRUE":
            self.rotor = self.ParseGauge('ROTOR', type='prop')
        if self.hasStator == "TRUE":
            self.stator = self.ParseGauge('STATOR', type='6dof')
        if self.hasKistler == "TRUE":
            self.kistler = self.ParseGauge('KISTLER', type='kistler')
        if self.hasKistler3 == "TRUE":
            self.kistler3 = self.ParseGauge('KISTLER3', type='kistler3')
        if self.hasKistler3_2 == "TRUE":
            self.kistler3_2 = self.ParseGauge('KISTLER3_2', type='kistler3')
        if self.hasSOF1 == "TRUE":
            self.SOF1 = self.ParseGauge('SOF1', type='6dof')
        if self.hasSOF2 == "TRUE":
            self.SOF2 = self.ParseGauge('SOF2', type='6dof')

    def ParseGauge(self, section, type='6dof'):
        """ Read in the cal info for the gauge.  Items to read is based on
        the type and section tells where to read from
        """

        gauge = {}
        for item, itype in self.itemlist[type]:
            try:
                prop = self.tdms_file.properties[section+'_'+item]
                if itype == 'string':
                    gauge[item] = prop
                if itype == 'float':
                    gauge[item] = float(prop)

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

        gauge['Int_Mat'] = np.array(rows, dtype=float)

        rows = []
        for i in range(1,7):
            row = []
            rowstr = gauge['orient_row%d' % i]
            cols = rowstr.strip().split()
            for col in cols:
                row.append(float(col))
            rows.append(row)

        gauge['Orient_Mat'] = np.array(rows, dtype=float)

        return gauge    

if __name__ == '__main__':
    cfile = CalFile('tdms_to_obc.cal', '.')
    cfile.ParseAll()
    print("Channels:", cfile.channels)
    print("Gains:", cfile.gains)
    print("Rotor Fx:", cfile.rotor['Fx'])
    print("Rotor:", cfile.rotor['Orient_Mat'])
    print("Rotor:", cfile.rotor['Int_Mat'])
