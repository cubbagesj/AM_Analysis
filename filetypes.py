# FileTypes.py
#
# Copyright (C) 2006-2018 - Samuel J. Cubbage
#
# This program is part of the Autonomous Model Software Tools Package
#
# A Class library for the various filetypes used for FRMM and AM data.
# These classes provide an interface to the different types of
# model data

# 10/02/2006 - sjc

# Updated 8/13/2010 by C.Michael Pietras

# Updated 3/10/2016 to add .tdms data file support by Woody Pfitsch

# sjc - 1/2018 - Updates to convert to using pandas for the data struture

# Imports - Standard Libraries
import numpy as np
import pandas as pd
from nptdms import TdmsFile  #package for importing tdms file data into python using numpy arrays
import os.path, time
from scipy.interpolate import interp1d
import struct

# Imports - Local Packages
from search_file import search_file_walk
from calfile_new import CalFile
import dynos_array as dynos


class STDFile:
    """ Run file class for manipulation of standard merge data:
        Initializing an instance of the class reads
        the run into memory and provides methods for accessing and
        getting info on the run.

        Public Methods are:
            __init__    : Intializes object, finds run and loads data
            info        : Prints the run information
            getEUData   : Returns a column of data converted to EU
            getRawData  : Returns a column of raw data
    """
    # Set up the boat geometry info based on ship length
    # Format is len: [radius, xnose, xsail, hsail]
    GeoTable = {'688/751':[16.50, 164.4, 66.21, 16.19],
                'S21':[20.0, 160.04, 66.21, 17.0],
                'TB':[16.25, 130.0, 53.80, 13.813],
                'S23':[20.0, 209.93, 116.10, 17.0],
                'VA':[17.0, 172.27, 89.25, 19.58],
                'SSGN':[21.0, 257.42, 154.96, 26.6],
                'OR':[21.67, 253.67, 157.3, 33.2],
                'VPM97':[17.0, 221.62, 138.61, 19.58],
                'VPM62':[17.0, 172.27, 89.25, 19.58],
                'VPM':[17.0, 180.0, 100.0, 19.58]}

    def __init__(self, run_number='0', search_path='.'):
        """ Initializes the run, finds and reads in the data. and
        sets up various variables
        The search_path defaults to the local directory. 
        
        If the run is not found it returns an empty structure
        """

        # Check if we know the path already
        if search_path == 'known':
            # In this case we are passing the full pathname
            fullname = run_number
        else:
            # Attempt to find the run on the path
            fullname = search_file_walk(run_number+'.std', search_path)

        if not fullname:
            if not search_path == 'c:\AM_merge_data':
                if not os.path.exists(search_path):
                    # if the file does not exist and the search path does not exist
                    # check the default local directory as a last resort
                    fullname = search_file_walk(run_number+'.std', 'c:\AM_merge_data')

        if not fullname:
            # Populate empty structure if no file found
            # This is to keep various othr parts of code from breaking if no file
            self.filename = ''
            self.dirname = ''
            self.filetype = ''
            self.title = ''
            self.timestamp = ''
            self.nchans = 0
            self.data = []
            self.dataEU=[]
            self.time = []
            self.dt = 0
            self.len = 0.0
        else:      
            dirname, filename = os.path.split(fullname)

            # First open the file and read the header info
            f = open(fullname, 'r')

            self.filename = filename
            self.dirname = dirname
            self.filetype = f.readline().strip()
            # STD files come in two flavors, DELIMTXT and Block. 
            # First line contains the type flag
            # Check for the file type so we know how to read.
            if self.filetype.find("DELIMTXT") != -1:
                # Delimtxt format
                
                # Next two lines are title and timestamp
                self.title = f.readline().strip()
                self.timestamp = f.readline().strip()

                # Next line contains number of channels, DT and length
                line1 = f.readline().strip()
                line1 = line1.replace(',', ' ')
                self.nchans = int(line1.split()[0])
                self.dt = float(line1.split()[1])
                try:
                    self.length = float(line1.split()[2])
                except:
                    # Set default length to 1.0
                    self.length = 1.0

                # Set boat flag to default. This gets updated by user at runtime
                self.boat = 'default'
                
                # Need to clean up names before reading in
                rawnames = f.readline().strip()
                cleannames = rawnames.lower().replace("' '", "''").replace(" ","_").replace("''","' '").split()
                channames = []
                idx = 0
                for chan in cleannames:
                    if chan[1] == '-':
                        channames.append("'empty_%d'" % idx)
                        idx += 1
                    else:
                        channames.append(chan)

                f.close()

                # Now use pandas to get the data and channel names
                self.data = pd.read_table(fullname, sep='\s+', skiprows=5, names=channames)
                self.chan_names = self.data.columns

                # Time is found in column 26 - subtract initial point to zero
                self.data.iloc[:,26] -= self.data.iloc[0,26]
                self.time = self.data.iloc[:,26]
                
                # get the geometry info from the table based on boat length
                if abs(self.length - 362) < 0.8 :
                    self.boat = '688/751'
                elif abs(self.length - 361) < 1:
                    self.boat = 'S21'
                elif abs(self.length - 461.63) < .1:
                    self.boat = 'S23'
                elif abs(self.length - 377.33) < 1 :
                    self.boat = 'VA'
                elif abs(self.length - 560 ) < 1:
                    self.boat = 'SSGN'
                elif abs(self.length - 299.25) < 1:
                    self.boat = 'TB'
                elif abs(self.length - 555.08) < 1:
                    self.boat = 'OR'
                elif abs(self.length - 474.33) < 1:
                    self.boat = 'VPM97'
                elif abs(self.length - 439.33) < 1:
                    self.boat = 'VPM62'
                elif abs(self.length - 461.5) < .1:
                    self.boat = 'VPM'
                else:
                    self.boat = '688/751'
                
            else:
                # Block
                self.title = self.filetype
                self.timestamp = f.readline().strip()

                line1 = f.readline().strip()
                line1 = line1.replace(',', ' ')
                self.nchans = int(line1.split()[0])
                self.dt = float(line1.split()[1])

                # Chan names are 6 per line
                self.chan_names = []
                for cnt in range(self.nchans/6):
                    line1 = f.readline()
                    for x in range(6):
                        if x == 0:
                            name = line1[3:13]
                        else:
                            name = line1[3+(13*x):13+(13*x)]
                        self.chan_names.append(name)
                if (cnt+1)*6 != self.nchans:
                    line1 = f.readline()
                    for x in range(self.nchans - ((cnt+1) * 6)):
                        if x == 0:
                            name = line1[5:13]
                        else:
                            name = line1[5+(12*x):13+(12*x)]
                        self.chan_names.append(name)

                # get the rest of the file in one big gulp
                alldata = f.read().split()
                datalist = []
                rowdata = []
                colcnt = 0
                for value in alldata:
                    rowdata.append(float(value))
                    colcnt += 1
                    if colcnt >= self.nchans:
                        datalist.append(rowdata)
                        rowdata = []
                        colcnt = 0
                self.data = np.array(datalist, dtype=float)
                # There is no time channel, so make one
                self.time = np.arange(0, len(self.data), dtype=float)
                self.time = self.time * self.dt


            # For STD files, the gains are 1 and zeros are zero
            self.gains = np.ones((self.nchans), dtype = float)
            self.zeros = np.zeros((self.nchans), dtype = float)
            
            self.dataEU = (self.data - self.zeros) * self.gains

            # Compute the run stats
            self.run_stats()
            
            # Map navigation info
            self.mapNavInfo()

    def info(self):
        """ Prints information on the run"""

        print("Filename: %s" % self.filename)
        try:
            print("Filetype: %s" % self.filetype)
            print("Title: %s" % self.title)
            print("Timestamp: %s" % self.timestamp)
            print("# of channels: %d" % self.nchans)
            print("DT: %f" % self.dt)
            print("Channel Names: ")
            for name in self.chan_names:
                print(name,)
            print()
            print("Standby at record: %d  time: %f" % (self.stdbyrec, self.stdbytime))
            print("Execute at record: %d  time: %f" % (self.execrec, self.exectime))

        except:
            pass

    def getEUData(self, channel):
        """ Returns an array containing the request channel of data
            in engineering units - Full scale values
            
            channel is a column number or column name
        """
        if type(channel) != str:
            if channel < 0 or channel > self.nchans:
                return None
            else:
                return self.dataEU.iloc[:,channel]
        else:
            return self.dataEU.loc[:,channel]

    def getRAWData(self, channel):
        """ Returns an array containing the request channel of data
            in raw units (no conversion)
            For STD files this is same as EUData
            
            channel is a column number or column name
        """
        if type(channel) != str:
            if channel < 0 or channel > self.nchans:
                return None
            else:
                return self.data.iloc[:,channel]
        else: 
            return self.data.loc[:,channel]

    def run_stats(self):
        """ Calculate important run stats like time of execute"""

        # Status is always at channel 25

        try:
            # Find where the status goes to 5, this is execute time
            status = list(self.data.iloc[:,25])
            self.execrec = status.index(5)
            self.exectime = self.time[self.execrec]
            self.stdbyrec = status.index(2)
            self.stdbytime = self.time[self.stdbyrec]

            # Compute the normalized time, i.e. time from execute
            self.ntime = self.time - self.exectime
        except:
            self.ntime = self.time
            self.execrec = 0
            self.exectime = 0
            self.stdbyrec = 0
            self.stdbytime = 0

        # Now compute the value of each channel for 10 steps before
        # execute and store this in case we want to match up initial values

        self.init_values = []
        for channel in range(self.nchans):
            chan_avg = 0.0
            count = 0
            for x in range(self.execrec-10, self.execrec):
                chan_avg += self.data.iloc[x,channel]
                count += 1
            self.init_values.append(chan_avg/count)

        # Now compute the approach value of each channel btwn stdby and 
        # execute and store this

        self.appr_values = []
        for channel in range(self.nchans):
            chan_avg = 0.0
            count = 0
            for x in range(self.stdbyrec, self.execrec):
                chan_avg += self.data.iloc[x,channel]
                count += 1
            try:
                self.appr_values.append(chan_avg/count)
            except:
                self.appr_values.append(0.0)

    def mapNavInfo(self):
        """ Maps the navigation information to standard
        names for use in calculations
        """
        try:
            self.theta = self.dataEU["'pitch'"]
            self.phi = self.dataEU["'roll'"]
            try:
                self.psi = self.dataEU["'yaw'"]
            except:
                self.psi = self.dataEU["'heading'"]

            self.p = self.dataEU["'p'"]
            self.q = self.dataEU["'q'"]
            self.r = self.dataEU["'r'"]
            

            # These are the pre-processed adcp data
            self.u_adcp = self.dataEU["'u_ft/s'"]
            self.v_adcp = self.dataEU["'v_ft/s'"]
            self.w_adcp = self.dataEU["'w_ft/s'"]

            # These are the raw adcp data
            self.u_adcp_raw = self.dataEU["'raw_u_ft/s'"]
            self.v_adcp_raw = self.dataEU["'raw_v_ft/s'"]
            self.w_adcp_raw = self.dataEU["'raw_w_ft/s'"]

            self.depth = self.dataEU["'zsensor'"]
        except:
            # FST runs use different names so just skip
            pass

    def compStats(self, start=None, end=None):
        """ This routine will compute the max/min for each data channel
        between start and end times.  The values are stored in 4 seperate lists
        that can be used by the analysis routines
        """
        # the first thing to do is to create a subset of the run data to search over
        # This defaults to the data from execute to the end of the run
        if start == None:
            start = self.execrec
        if end == None:
            rundata = self.data[start:]
        else:
            rundata = self.data[start:end]

        # Compute the nose and sail depths
        self.compZnosesail(STDFile.GeoTable[self.boat], rundata)

        # Now to get the max and mins for the normal channels
        self.maxValues = rundata.max()            
        self.minValues = rundata.min()
        self.maxIndices = rundata.idxmax()
        self.minIndices = rundata.idxmin()

        # Compute the maxes and mins of the nose and sail depth channels
        self.maxZnose = self.Znose.max()
        self.maxZnoseIndex = self.Znose.idxmax()
        self.minZnose = self.Znose.min()
        self.minZnoseIndex = self.Znose.idxmin()
        self.maxZsail = self.Zsail.min()
        self.maxZsailIndex = self.Zsail.idxmax()
        self.minZsail = self.Zsail.min()
        self.minZsailIndex = self.Zsail.idxmin()
        
    def compZnosesail(self, geometry, data):
        """ Computes the nose and sail depth based on the geometry info
        Assumes that ZGA is at 22, pitch at 8, and roll at 7
        """
        radius, xnose, xsail, hsail = geometry
        zsail = -(hsail+radius)
        # Get the approach value based on appr pitch/roll
        self.Znoseappr = self.appr_values[22] + (-xnose * np.sin(np.radians(self.appr_values[8])))
        self.Zsailappr = self.appr_values[22] + (-xsail * np.sin(np.radians(self.appr_values[8]))+
                                                 zsail * np.cos(np.radians(self.appr_values[8]))*
                                                 np.cos(np.radians(self.appr_values[7])))

        sinTH = np.sin(np.radians(data[data.columns[8]]))
        cosTH = np.cos(np.radians(data[data.columns[8]]))
        cosPH = np.cos(np.radians(data[data.columns[7]]))
        self.Znose = data[data.columns[22]] + (-xnose * sinTH)
        self.Zsail = data[data.columns[22]] + (-xsail * sinTH + zsail * cosTH * cosPH)


    def turnstats(self):
        """
            Returns the advance, transfer and tactical diameter
            for a turn maneuver
        """

        # extract the yaw data 
        yaw180 = self.psi
        yawrate = self.r

        #compute the approach yaw
        yawappr = yaw180[self.stdbyrec:self.execrec].mean()

        # Now for advance/xfer  - where yaw has changed by 90
        # Need to look for both positive and negative yaw change

        yawpos90 = yawappr + 90
        if yawpos90 > 180:
            yawpos90 -= 360

        yawneg90 = yawappr - 90
        if yawneg90 < -180:
            yawneg90 += 360

        # Now look for this value in the data
        # need to look in both directions and see which comes first

        try:
            posIndex90 = np.where(abs(yaw180-yawpos90)<0.1)[0][0]
        except IndexError:
            posIndex90 = 0
        try:
            negIndex90 = np.where(abs(yaw180-yawneg90)<0.1)[0][0]
        except IndexError:
            negIndex90 = 0


        if posIndex90 != 0 and yawrate[posIndex90] > 0:
            self.index90 = posIndex90
        else:
            self.index90 = negIndex90

        self.advance = abs(self.getEUData(20)[self.index90])
        self.transfer = abs(self.getEUData(21)[self.index90])

        self.time90 = self.ntime[self.index90]

        # Now for tactical Diam  - where yaw has changed by 180
        # Need to look for both positive and negative yaw change
        yawpos180 = yawappr + 180
        if yawpos180 > 180:
            yawpos180 -= 360

        yawneg180 = yawappr - 180
        if yawneg180 < -180:
            yawneg180 += 360

        # Now look for this value in the data
        # need to look in both directions and see which comes first

        if yawpos180 > 0:
            try:
                posIndex180 = np.where(abs(yaw180-yawpos180)< 0.1)[0][0]
            except IndexError:
                posIndex180 = 0
        else:
            posIndex180 = 0

        if yawneg180 < 0:
            try:
                negIndex180 = np.where(abs(yaw180-yawneg180)<0.1)[0][0]
            except IndexError:
                negIndex180 = 0
        else:
            negIndex180 = 0

        # The advance occurs at the lowest non zero index

        self.index180 = min(posIndex180, negIndex180)

        if self.index180 == 0:
            self.index180 = max(posIndex180, negIndex180)


        self.tactdiam = abs(self.getEUData(21)[self.index180])
        self.time180 = self.ntime[self.index180]



class OBCFile:
    """ Run file class for manipulation of AM OBC data:
        Initializing an instance of the class reads
        the run into memory and provides methods for accessing and
        getting info on the run.

        Public Methods are:
            __init__    : Intializes objetc, finds run and loads data
            info        : Prints the run information
            getEUData   : Returns a column of data converted to EU
            getRawData  : Returns a column of raw data
    """

    def __init__(self, run_number='0', search_path='.'):
        """ Initialize the run, find and read in the data.
            The search_path defults to only the local directory.
        """
        
        # Check if we know the path already
        if search_path == 'known':
            fullname = run_number
        else:
            # Attempt to find the run on the path, return NONE if not found
            fullname = search_file_walk(str('run-'+run_number+'.obc'), search_path)
            
        if not fullname:
            if not search_path == 'c:\AM_data':
                if not os.path.exists(search_path):
                    #if the file does not exist and the search path does not exist
                    #check the default local directory
                    fullname = search_file_walk('run-'+run_number+'.obc', 'c:\AM_data')

        if not fullname:
            self.filename = ''
            self.dirname = ''
            self.filetype = 'None'
            self.title = ''
            self.timestamp = ''
            self.nchans = 0
            self.data = []
            self.dataEU = []
            self.time = []
            self.dt = 0

        else:      
            dirname, filename = os.path.split(fullname)
            runfile = os.path.join(dirname, 'run-'+run_number+'.run')
            calfilename = os.path.join(dirname, 'run-'+run_number+'.cal')
            

            self.filename = filename
            self.dirname = dirname
            self.basename = 'run-'+run_number
            self.filetype = 'AM-obc'
            self.title = ''
            self.timestamp = time.ctime(os.path.getmtime(fullname))
            self.nchans = 0
            self.dt = 0.01


            self.data = []
            obcfile = open(fullname, 'r')
            
            # Setup a config file parser
            cal = CalFile(calfilename)
            
            # Now parse the calfile
            cal.ParseAll()

            # extract the # chans
            self.nchans = cal.channels

            # And the list of channel names.  Need to modify the list to avoid duplicates
            
            chan_names = []
            for channel in range(self.nchans):
                name = cal.sys_names[channel]
                if chan_names.count(name) == 0:
                    chan_names.append(name)
                else:
                    chan_names.append(name+str(channel))
            self.chan_names = chan_names

            # Now get the gains
            self.gains = cal.gains
            self.zeros = cal.zeros
            self.alt_names = cal.alt_names
            self.eng_units = cal.eng_units
            self.data_pkt_locs = cal.data_pkt_locs
            self.cal_dates = cal.cal_dates

            gainss = pd.Series(self.gains, index=chan_names)
            zeross = pd.Series(self.zeros, index=chan_names)
            
            # Set up the special gauges
            self.sp_gauges = {}
            # Rotor 
            if cal.hasRotor == 'TRUE':
                self.sp_gauges['Rotor'] = dynos.Rot_Dyno6(cal.rotor)
        
            # Stator
            if cal.hasStator == 'TRUE':
                self.sp_gauges['Stator'] = dynos.Dyno6(cal.stator)
        
            # SOF1
            if cal.hasSOF1 == 'TRUE':
                self.sp_gauges['SOF1'] = dynos.Dyno6(cal.SOF1)
        
            # SOF2
            if cal.hasSOF2 == 'TRUE':
                self.sp_gauges['SOF2'] = dynos.Dyno6(cal.SOF2)
        
            # Kistler 
            if cal.hasKistler == 'TRUE':
                self.sp_gauges['Kistler'] = dynos.Kistler6(cal.kistler)
        
            if cal.hasKistler3 == "TRUE":
                self.sp_gauges['Kistler3'] = dynos.Kistler3(cal.kistler3)

            if cal.hasKistler3_2 == "TRUE":
                self.sp_gauges['Kistler3_2'] = dynos.Kistler3(cal.kistler3_2)
         
            if cal.hasDeck == "TRUE":
                self.sp_gauges['Deck'] = dynos.Deck(cal.deck)
        
            # And finally the 6DOF appendage gauges
            if cal.has6DOF == "TRUE":
                for i in range(1,cal.num_6DOF+1):
                    self.sp_gauges['6DOF%d' %i] = dynos.Dyno6(cal.sixDOF[i-1])
                   

            # Finally read in raw data and convert to EU
            data = pd.read_table(obcfile, sep='\s+', header=None, names=chan_names)
            self.data = data
            
            self.dataEU = (self.data - zeross) * gainss

            # There is no time channel, so make one
            self.time = np.arange(0, len(self.data), dtype=float)
            self.time = self.time * .01

            #----------------------------------
            #  Build the runtype from the maneuver settings in the .run file
            #  MOPT 30 defines the type of maneuver and the other settings are for
                # plane angles etc.
            #------------------------------------
            mantypes = ['Set Planes',
                        'Controlled Turn',
                        'Plane Jam',
                        'FST Correlation',
                        'System Ident',
                        'Diagnostic Turn',
                        'Contt test',
                        'Horizontal Overshoot',
                        'Vertical Overshoot',
                        'Special',
                        'Surface Turn with fixed sterns',
                        'Toms rudder on/off',
                        'Turn with fixed sternplanes',
                        'Acceleration run',
                        'Deceleration Run',
                        'Horizontal stability run',
                        'Ordered R at execute',
                        'Flowvis',
                        'ZIGZAG',
                        'Shore Test',
                        'Speed Cal Jam',
                        'Uncontrolled Turn',
                        'Manual Mode',
                        'Shore Test',
                        'Todds Astern 3 turn',
                        'Rudder Perturbation']

            # try to get the run info from runfile
            try:
                lines = open(runfile).read().splitlines()
                for line in lines:
                    if line.find('#RUNTYPE:') != -1:
                        runtype = line[line.find('#RUNTYPE:') +9:]
                        self.title = "AM:run-%s: %s" % (run_number, runtype)
                        break
                    else:
                        self.title = "Title Not Defined"
            except:
                self.title = ''

            # Now lets get the MOPT 30 value
            lcount = 0
            for line in lines:
                if line.find('#MOPT2') != -1:
                    break
                else:
                    lcount += 1
            mopts = []
            for mopt in lines[lcount+1].split(','):
                try:
                    mopts.append(int(mopt))
                except ValueError:
                    pass
            try:
                runtype = mantypes[mopts[9]]
            except:
                runtype = ''
            
            # Add to title
            self.title = runtype + ' ' + self.title

            # Compute the run stats
            self.run_stats()
            
            # Map the navigation data 
            self.mapNavInfo()
            
            # Compute the 6DOF dynos
            self.computeSpecials()
            
            # Read the BMS packet
            self.readBMS()
            
            

    def info(self):
        """ Prints information on the run"""

        print("Filename: %s" % self.filename)
        try:
            print("Filetype: %s" % self.filetype)
            print("Title: %s" % self.title)
            print("Timestamp: %s" % self.timestamp)
            print("# of channels: %d" % self.nchans)
            print("DT: %f" % self.dt)
            print("Channel Names: ")
            for name in self.chan_names:
                print(name,)
            print()
            print("Execute at record: %d  time: %f" % (self.execrec, self.exectime))
        except:
            pass

    def getEUData(self, channel):
        """ Returns a copy of a series containing the request channel of data
            in engineering units - Model Scale Units
            channel is a column number or column name
        """
        if type(channel) != str:
            if channel < 0 or channel > self.nchans:
                return None
            else:
                return self.dataEU.iloc[:,channel].copy(deep=True)
        else:
            return self.dataEU.loc[:,channel].copy(deep=True)

    def getRAWData(self, channel):
        """ Returns an series containing the request channel of data
            in raw units (no conversion)
            channel is a column number or column name
        """
        if type(channel) != str:
            if channel < 0 or channel > self.nchans:
                return None
            else:
                return self.data.iloc[:,channel]
        else: 
            return self.data.loc[:,channel]

    def run_stats(self):
        """ Calculate important run stats.
            Current Stats:
                time of standby
                time of execute
                normalized time (from exe)
                
                Also the values during zeros and the approach values
        """


        # First we need to extract the mode channel
        status = list(self.data.iloc[:,325])
        try: 
            self.stdbyrec = status.index(0x0F33)
            self.stdbytime = self.time[self.stdbyrec]
            self.execrec = status.index(0x0F43)
            self.exectime = self.time[self.execrec]
        except:
            self.stdbyrec = 0
            self.stdbytime = 0.0
            self.execrec = 0
            self.exectime = 0.0
        # Create a normalized time i.e. time since execute
        self.ntime = self.time - self.exectime

        
        # Get the values during zeros
        self.avgEUzeros = self.dataEU.query('mode325 == 0x0F13').mean()
        self.avgRawzeros = self.data.query('mode325 == 0x0F13').mean()
        # And approach
        self.avgappr = self.dataEU.query('mode325 == 0x0F33').mean()
        # Initial values - Legacy
        self.init_values = self.avgappr.values
        

    def mapNavInfo(self):
        """ Maps the navigation information to standard
        names for use in calculations
        
        Change this section to define source of nav data that is used
        """
        try:
            self.theta = self.dataEU.ln200_pitch.values
            self.phi = self.dataEU.ln200_roll.values
            self.psi = self.dataEU.ln200_heading.values

            self.p = self.dataEU.ln200_x_ang_rate.values
            self.q = self.dataEU.ln200_y_ang_rate.values
            self.r = self.dataEU.ln200_z_ang_rate.values

            self.u_adcp = self.dataEU.adcp_x_vel_btm.values
            self.v_adcp = self.dataEU.adcp_y_vel_btm.values
            self.w_adcp = self.dataEU.adcp_z_vel_btm.values

            self.u_adcp_raw = self.dataEU.adcp_x_vel_btm.values
            self.v_adcp_raw = self.dataEU.adcp_y_vel_btm.values
            self.w_adcp_raw = self.dataEU.adcp_z_vel_btm.values
            
            self.bigU = np.sqrt(self.dataEU.adcp_x_vel_btm.values ** 2 +
                                self.dataEU.adcp_y_vel_btm.values ** 2 +
                                self.dataEU.adcp_z_vel_btm.values ** 2)

            self.depth = self.dataEU.obs_depth2.values
        except:
            pass
    
    def computeSpecials(self):
        """
            This section does the computations for the special gauges
            like the 6DOF Dynos.  The computed channels are added to the data
            structure as additional columns
        """
        # Pitch
        theta = np.radians(self.theta)

        #Roll
        phi = np.radians(self.phi)

        # Yaw
        psi = np.radians(self.psi)

        bodyAngles = [phi, theta, psi]

        
        for gauge in self.sp_gauges.keys():
            # Compute the special gauges - The Deck is not used and has not been updates
            if (gauge != 'Deck'):
                
                # Before computing the data, need to compute the zeros
                # This is done by passing in a subset of the data (usually the zeros section mode=0x0F13)
                # and having this data processed and averaged
                
                # But for the rotor we want the running zero during the approach (mode=0x0F33)
                # This can cause an error though if there was no standby (i.e. and aborted run)
                # so we wrap this in a try clause and default back to the zeros portion if necessary
                
                if (gauge == 'Rotor'):
                    try:
                        self.sp_gauges[gauge].compute(self.dataEU.query('mode325 == 0x0F33'),
                                      bodyAngles, 
                                      cb_id = 10,
                                      doZeros = 0.0)
                    except:
                        self.sp_gauges[gauge].compute(self.dataEU.query('mode325 == 0x0F13'),
                                      bodyAngles, 
                                      cb_id = 10,
                                      doZeros = 0.0)

                else:
                    self.sp_gauges[gauge].compute(self.dataEU.query('mode325 == 0x0F13'),
                                  bodyAngles, 
                                  cb_id = 10,
                                  doZeros = 0.0)

                self.sp_gauges[gauge].compute(self.dataEU,
                              bodyAngles, 
                              cb_id = 10,
                              doZeros = 1.0)

                # Then append to the EU dataframe
                self.dataEU[gauge+'_CFx'] = self.sp_gauges[gauge].CFx
                self.dataEU[gauge+'_CFy'] = self.sp_gauges[gauge].CFy
                self.dataEU[gauge+'_CFz'] = self.sp_gauges[gauge].CFz
                self.dataEU[gauge+'_CMx'] = self.sp_gauges[gauge].CMx
                self.dataEU[gauge+'_CMy'] = self.sp_gauges[gauge].CMy
                self.dataEU[gauge+'_CMz'] = self.sp_gauges[gauge].CMz
                # Update the channel names and number
                self.chan_names = self.dataEU.columns.values.tolist()
                self.nchans = len(self.chan_names)
    
    def readBMS(self):
        """
            This routine reads the BMS packet (if present) and adds the
            data to the dataEU array so that it can be plotted
        """
        # This could go bad and it is optional so wrap it all in a try
        try:
            # BMS Pkt format - 208 bytes It has both big and little endian
            # numbers so need to read it in parts
            bmsFmtA = '<71B2h8B2h8Bh3Bh5B2h3B2h'
            bmsFmtB = '>36h6B6h'
            
            # Read in channel names and scale factors
            
            self.bmsNames = []
            self.bmsGains = []
            with open('bmsNameMap.txt', mode='r') as file:
                NameMap = file.read().splitlines()
            for line in NameMap:
                name, gain = line.split(',')
                self.bmsNames.append(name)
                self.bmsGains.append(float(gain))
            
            bmsfilename = os.path.join(self.dirname, self.basename+'.bms')
            # First open and read in the bms file
            with open(bmsfilename, mode='rb') as file:
                bmsFile = file.read()
            
            # Now parse it
            index = 0
            bmsArray=[]
            bmsRow=[]
            for n in range(int(len(bmsFile)/208)):
                rowA = struct.unpack_from(bmsFmtA, bmsFile, offset=index)
                index += struct.calcsize(bmsFmtA)
                for item in rowA:
                    bmsRow.append(item)
                
                rowB = struct.unpack_from(bmsFmtB, bmsFile, offset=index)
                index += struct.calcsize(bmsFmtB)
                for item in rowB:
                    bmsRow.append(item)
                
                # Now pad to 100 Hz
                for n in range(99):
                    bmsArray.append(bmsRow)
                bmsRow=[]
                
            self.bmsData = pd.DataFrame(np.array(bmsArray), columns=self.bmsNames) * self.bmsGains
            self.dataEU = pd.concat([self.dataEU, self.bmsData], axis=1)
            # Clean up the na values caused by the concat
            self.dataEU.fillna(0, inplace=True)
            
            # Update the channel names and number
            self.chan_names = self.dataEU.columns.values.tolist()
            self.nchans = len(self.chan_names)
            
            # Recreate nTime because of BMS data mismatch
            self.time = np.arange(0, len(self.dataEU), dtype=float)
            self.time = self.time * 0.01
            self.ntime = self.time - self.exectime
        except:
            pass
            
class TDMSFile:
    """ Run file class for manipulation of AM TDMS data:
        Initializing an instance of the class reads
        the run into memory and provides methods for accessing and
        getting info on the run.
        
        TDMS is a National Instruments binary format, nptdms imported above
        provides functions used in this class for unpacking the binary TDMS files
        and returning the data
        
        Public Methods are:
            __init__    : Intializes objetc, finds run and loads data
            info        : Prints the run information
            getEUData   : Returns a column of data converted to EU
            getRawData  : Returns a column of raw data
    """      
    def __init__(self, run_number='0', search_path='.'):
        """ Initialize the run, find and read in the data.
            The search_path defults to only the local directory.
        """
        
        # Check if we know the path already
        if search_path == 'known':
            fullname = run_number
        else:
            # Attempt to find the run on the path, return NONE if not found
            fullname = search_file_walk(str('run_'+run_number+'.tdms'), search_path)
        
        if not fullname:
            if not search_path == 'c:\AM_data':
                if not os.path.exists(search_path):
                    #if the file does not exist and the search path does not exist
                    #check the default local directory
                    fullname = search_file_walk('run-'+run_number+'.tdms', 'c:\AM_data')
        
        if not fullname:
            self.filename = ''
            self.dirname = ''
            self.filetype = 'None'
            self.title = ''
            self.timestamp = ''
            self.nchans = 0
            self.data = []
            self.dataEU = []
            self.time = []
            self.dt = 0
            
        else:      
            dirname, filename = os.path.split(fullname)
        
            self.filename = filename
            self.dirname = dirname
            self.basename = 'run-'+run_number
            self.filetype = 'AM-tdms'
            self.title = ''
            self.timestamp = time.ctime(os.path.getmtime(fullname))
            self.nchans = 0
            self.dt = 0.01

            self.tdms_file_obj = TdmsFile(fullname)  #open the tdms file using nptdms package
            #Get the length of the data by looking at one of the channels
            self.tdm_length = len(self.tdms_file_obj.channel_data('DATA', self.tdms_file_obj.group_channels('DATA')[0].path.split("'")[3]))
            
            # Get the channel mapping for the special gauges from the tdms_to_obc.cal file
            calfilename = os.path.join(dirname, 'tdms_to_obc.cal')
            cal = CalFile(calfilename)
            
            # Now parse the calfile
            cal.ParseAll()
            
            #import or create the time channel
            try:
                self.time = self.tdms_file_obj.channel_data('DATA', 'sys_time') #import absolute time channel
                self.time = self.time - self.time[0] # make the time channel relative to the start of the file
            except:
                # There is no time channel, so make one
                self.time = np.arange(0, self.tdm_length, dtype=float)
                self.time = self.time * .01
            
            # Get the run type out of the tdms file properties
            try:
                fileobj = self.tdms_file_obj.object()
                self.title = fileobj.properties['script_run_type']
            except:
                self.title = 'No Run Type Property Defined' 
                
            # Cals and channel names are all stored in the tdms_file_obj channel objects   
            try:
                #  Set up some variables to hold the values
                self.nchans = len(self.tdms_file_obj.group_channels('DATA'))
                self.cals = {}  #Dictionary to hold calibration info for each channel
                self.alt_names = []
                for i in range(self.nchans):
                    self.alt_names.append(str(self.tdms_file_obj.group_channels('DATA')[i].path.split("'")[3]))
                self.chan_names = sorted(self.alt_names, key=str.lower)
                self.data_pkt_locs = []
                self.eng_units = []
                self.cal_dates = []
                
                def nocal(prescaledVal):
                    '''
                    Function to return input float value or numpy array because no cal was defined
                    '''
                    return prescaledVal
                            
                # Then read the tdms file for the channel cals
                for channel in self.chan_names:
                    chan_obj = self.tdms_file_obj.object('DATA', channel)
                    try:
                        self.eng_units.append(chan_obj.properties['eng_units'])
                    except:
                        self.eng_units.append('NA')
                    try:
                        scaletype = str(chan_obj.properties['NI_Scale[0]_Scale_Type'])
                        #Linear calibration scaling, dictionary will hold a lambda function to apply the linear cal to a given prescaled value
                        if scaletype == 'Linear': 
                            self.cals[channel] = (lambda x, m=chan_obj.properties['NI_Scale[0]_Linear_Slope'], b=chan_obj.properties['NI_Scale[0]_Linear_Y_Intercept'] : m*x+b)
                        #Linear interpolation scaling between point in Table, dictionary will hold a scipy interpolation function 
                        elif scaletype == 'Table':
                            #import scaled values from the tdms file properties
                            scaled = []
                            i = 0
                            while True:
                                try:
                                    scaled.append(chan_obj.properties['NI_Scale[0]_Table_Scaled_Values[' + str(i) + ']'])
                                except:
                                    break
                                else:
                                    i += 1
                            #import pre-scaled values from the tmds file properties
                            prescaled = []
                            i = 0
                            while True:
                                try:
                                    prescaled.append(chan_obj.properties['NI_Scale[0]_Table_Pre_Scaled_Values[' + str(i) + ']'])
                                except:
                                    break
                                else:
                                    i += 1
                            self.cals[channel] = interp1d(prescaled, scaled, bounds_error=False)
                        #No scaling is applied if no valid scaling type is found
                        else: 
                            self.cals[channel] = nocal
                    except:
                        self.cals[channel] = nocal
                        
                
            except:
                self.nchans = 0
                self.cals = {}
                print('we got an error')
                raise

            # Set up the special gauges
            self.sp_gauges = {}
            # Rotor 
            if cal.hasRotor == 'TRUE':
                self.sp_gauges['Rotor'] = dynos.Rot_Dyno6(cal.rotor)
        
            # Stator
            if cal.hasStator == 'TRUE':
                self.sp_gauges['Stator'] = dynos.Dyno6(cal.stator)
        
            # SOF1
            if cal.hasSOF1 == 'TRUE':
                self.sp_gauges['SOF1'] = dynos.Dyno6(cal.SOF1)
        
            # SOF2
            if cal.hasSOF2 == 'TRUE':
                self.sp_gauges['SOF2'] = dynos.Dyno6(cal.SOF2)
        
            # Kistler 
            if cal.hasKistler == 'TRUE':
                self.sp_gauges['Kistler'] = dynos.Kistler6(cal.kistler)
        
            if cal.hasKistler3 == "TRUE":
                self.sp_gauges['Kistler3'] = dynos.Kistler3(cal.kistler3)
        
            if cal.hasDeck == "TRUE":
                self.sp_gauges['Deck'] = dynos.Deck(cal.deck)
        
            # And finally the 6DOF appendage gauges
            if cal.has6DOF == "TRUE":
                for i in range(1,cal.num_6DOF+1):
                    self.sp_gauges['6DOF%d' %i] = dynos.Dyno6(cal.sixDOF[i-1])
                 
            #read in all the data from the tmds file    
            data = self.tdms_file_obj.channel_data('DATA', self.chan_names[0])
            dataEU = self.cals[self.chan_names[0]](self.tdms_file_obj.channel_data('DATA', self.chan_names[0]))
            for i in range(1, self.nchans):
                data = np.column_stack((data, self.tdms_file_obj.channel_data('DATA', self.chan_names[i])))
                dataEU = np.column_stack((dataEU, self.cals[self.chan_names[i]](self.tdms_file_obj.channel_data('DATA', self.chan_names[i]))))
            
            self.data = pd.DataFrame(data, columns=self.chan_names)
            self.dataEU = pd.DataFrame(dataEU, columns=self.chan_names)
            
            # It is hard to update TDMS file cals so check if there are
            # any updates that are needed in the tdms_cal_updates.txt file
            
            try:
                f = open('tdms_cal_updates.txt', 'r')
                calupdates = f.read().splitlines()
                print('Processing TDMS cal updates...')
                for line in calupdates:
                    update = line.split(',')
                    self.dataEU[update[0]] = self.dataEU[update[0]] * float(update[1])
                f.close()
            except:
                print('No TDMS updates to process')
            
            # Compute the run stats
            self.run_stats()
            
            # Map the navigation data
            self.mapNavInfo()
            
            # Compute the 6DOF dynos
            self.computeSpecials()


    def info(self):
        """ Prints information on the run"""
        
        print("Filename: %s" % self.filename)
        try:
            print("Filetype: %s" % self.filetype)
            print("Title: %s" % self.title)
            print("Timestamp: %s" % self.timestamp)
            print("# of channels: %d" % self.nchans)
            print("DT: %f" % self.dt)
            print("Channel Names: ")
            for name in self.chan_names:
                print(name,)
            print()
            print("Execute at record: %d  time: %f" % (self.execrec, self.exectime))
        except:
            pass
        
    def getEUData(self, channel):
        """ Returns an array containing the request channel of data
            in engineering units - Model Scale Units
        """
        
        if type(channel) != str:
            if channel < 0 or channel > self.nchans:
                return None
            else:
                return self.dataEU.iloc[:,channel]
        else:
            return self.dataEU.loc[:,channel]

        
    def getRAWData(self, channel):
        """ Returns an array containing the request channel of data
            in raw units (no conversion)
        """

        if type(channel) != str:
            if channel < 0 or channel > self.nchans:
                return None
            else:
                return self.data.iloc[:,channel]
        else: 
            return self.data.loc[:,channel]
        
            
    #AM-tdms files post 2016/02/23 will have the script_mode channel, prior versions will not
    # therefore all stats will be zero for earlier tdms files  
    def run_stats(self):
        """ Calculate important run stats.
            Current Stats:
                time of standby
                time of execute
                normalized time (from exe)
        """
        try: 
            # First we need to extract the mode channel
            status = self.tdms_file_obj.channel_data('DATA', 'script_mode')
            self.stdbyrec = np.where(status == 0x0F33)[0][0]
            self.stdbytime = self.time[self.stdbyrec]
            self.execrec = np.where(status == 0x0F43)[0][0]
            self.exectime = self.time[self.execrec]
        except:
            # If there is no mode channel or no stby or exec flag, return all zeros
            self.stdbyrec = 0
            self.stdbytime = 0.0
            self.execrec = 0
            self.exectime = 0.0
        # Create a normalized time i.e. time since execute
        self.ntime = self.time - self.exectime
 
        # Get the values during zeros
        self.avgEUzeros = self.dataEU.query('script_mode == 0x0F13').mean()
        self.avgRawzeros = self.data.query('script_mode == 0x0F13').mean()
        # And approach
        self.avgappr = self.dataEU.query('script_mode == 0x0F33').mean()
        # Initial values - Legacy
        self.init_values = self.avgappr.values

    def mapNavInfo(self):
        """ Maps the navigation information to standard
        names for use in calculations
        
        Change this section to define source of nav data that is used
        """
        try:
            self.theta = self.dataEU.Pitch.values
            self.phi = self.dataEU.Roll.values
            self.psi = self.dataEU.Yaw.values

            self.p = self.dataEU.X_Ang_Rate.values
            self.q = self.dataEU.Y_Ang_Rate.values
            self.r = self.dataEU.Z_Ang_Rate.values

            self.u_adcp = self.dataEU.BTIR_Xvel.values
            self.v_adcp = self.dataEU.BTIR_Yvel.values
            self.w_adcp = self.dataEU.BTIR_Zvel.values

            self.u_adcp_raw = self.dataEU.BTIR_Xvel.values
            self.v_adcp_raw = self.dataEU.BTIR_Yvel.values
            self.w_adcp_raw = self.dataEU.BTIR_Zvel.values
            
            self.bigU = np.sqrt(self.dataEU.BTIR_Xvel.values ** 2 +
                                self.dataEU.BTIR_Yvel.values ** 2 +
                                self.dataEU.BTIR_Zvel.values ** 2)

            self.depth = self.dataEU.Depth2.values
        except:
            pass
        
    def computeSpecials(self):
        """
            This section does the computations for the special gauges
            like the 6DOF Dynos.  The computed channels are added to the data
            structure as additional columns
        """
        # Pitch
        theta = np.radians(self.theta)

        #Roll
        phi = np.radians(self.phi)

        # Yaw
        psi = np.radians(self.psi)

        bodyAngles = [phi, theta, psi]

        
        for gauge in self.sp_gauges.keys():
            # Compute the special gauges - The Deck is not used and has not been updates
            if (gauge != 'Deck'):
                
                # Before computing the data, need to compute the zeros
                # This is done by passing in a subset of the data (usually the zeros section mode=0x0F13)
                # and having this data processed and averaged
                
                # But for the rotor we want the running zero during the approach (mode=0x0F33)
                # This can cause an error though if there was no standby (i.e. and aborted run)
                # so we wrap this in a try clause and default back to the zeros portion if necessary
                
                if (gauge == 'Rotor'):
                    try:
                        self.sp_gauges[gauge].compute(self.dataEU.query('script_mode == 0x0F33'),
                                      bodyAngles, 
                                      cb_id = 12,
                                      doZeros = 0.0)
                    except:
                        self.sp_gauges[gauge].compute(self.dataEU.query('script_mode == 0x0F13'),
                                      bodyAngles, 
                                      cb_id = 12,
                                      doZeros = 0.0)

                else:
                    self.sp_gauges[gauge].compute(self.dataEU.query('script_mode == 0x0F13'),
                                  bodyAngles, 
                                  cb_id = 12,
                                  doZeros = 0.0)

                self.sp_gauges[gauge].compute(self.dataEU,
                              bodyAngles, 
                              cb_id = 12,
                              doZeros = 1.0)

                # Then append to the EU dataframe
                self.dataEU[gauge+'_CFx'] = self.sp_gauges[gauge].CFx
                self.dataEU[gauge+'_CFy'] = self.sp_gauges[gauge].CFy
                self.dataEU[gauge+'_CFz'] = self.sp_gauges[gauge].CFz
                self.dataEU[gauge+'_CMx'] = self.sp_gauges[gauge].CMx
                self.dataEU[gauge+'_CMy'] = self.sp_gauges[gauge].CMy
                self.dataEU[gauge+'_CMz'] = self.sp_gauges[gauge].CMz
                # Update the channel names and number
                self.chan_names = self.dataEU.columns.values.tolist()
                self.nchans = len(self.chan_names)

             
    def EU_file(self):
        """ Create a csv data file with the EU data
            Created in same dir as obc file with .eu extension
        """
        
	# First build a header with the channel titles in one line
        headerstr = ', '.join(self.chan_names)
        # now build a numpy array with all the EU data
        alldata = self.cals[self.chan_names[0]](self.tdms_file_obj.channel_data('DATA', self.chan_names[0]))
        for i in range(1, self.nchans):
            alldata = np.column_stack((alldata, self.gains[i]*(self.tdms_file_obj.channel_data('DATA', self.chan_names[i]))+self.zeros[i]))
	# Now output to the EU file
        np.savetxt(os.path.join(self.dirname, self.basename+'.eu'), alldata, fmt = '%10.9f', delimiter=', ', header=headerstr)
                                                                     

if __name__ == "__main__":

#    test = OBCFile('13657')
#    test = TDMSFile('1632')
    test = STDFile('10-13657.std', 'known')
#    test.info()
#    test.run_stats()
#    print(test.getEUData(12))
    #print(test.theta)
    
    #test.EU_file()
