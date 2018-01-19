# FileTypes.py
#
# Copyright (C) 2006-2007 - Samuel J. Cubbage
#
# This program is part of the Autonomous Model Software Tools Package
#
# A Class library for the various filetypes used for RCM and AM data.
# These classes provide an interface to the different types of
# model data

# 10/02/2006 - sjc

# Updated 8/13/2010 by C.Michael Pietras

# Updated 3/10/2016 to add .tdms data file support by Woody Pfitsch

from search_file import *
import math as m
from pylab import *
import cfgparse
import os.path, time
import numpy as np
from scipy.interpolate import interp1d
from nptdms import TdmsFile  #package for importing tdms file data into python using numpy arrays

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
                'VPM62':[17.0, 172.27, 89.25, 19.58]}

    def __init__(self, run_number='0', search_path='.'):
        """ Initialize the run, find and read in the data.
        The search_path defaults to the local directory.  The files must
        conform to the DELIMTXT format for now.  In the future maybe handle
        other formats."""

        # Check if we know the path already
        if search_path == 'known':
            fullname = run_number
        else:
            # Attempt to find the run on the path, return empty structure if not found
            fullname = find_file(run_number+'.std', search_path)

        if not fullname:
            if not search_path == 'c:\AM_merge_data':
                if not os.path.exists(search_path):
                    #if the file does not exist and the search path does not exist
                    #check the default local directory
                    fullname = search_file_walk(run_number+'.std', 'c:\AM_merge_data')

        if not fullname:
            self.filename = ''
            self.dirname = ''
            self.filetype = ''
            self.title = ''
            self.timestamp = ''
            self.nchans = 0
            self.data = []
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
            # STD files come in two flavors, DELIMTXT and Block.  Check
            # for the file type so we know how to read.
            if self.filetype.find("DELIMTXT") != -1:
                # Delimtxt format
                self.title = f.readline().strip()
                self.timestamp = f.readline().strip()

                line1 = f.readline().strip()
                line1 = line1.replace(',', ' ')
                self.nchans = int(line1.split()[0])
                self.dt = float(line1.split()[1])
                try:
                    self.length = float(line1.split()[2])
                except:
                    self.length = 377.33

                # get the geometry info from the table based on boat length
                if abs(self.length - 362) < 0.8 :
                    self.boat = '688/751'
                elif abs(self.length - 361) < 1:
                    self.boat = 'S21'
                elif abs(self.length - 461.63) < 1:
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
                else:
                    self.boat = '688/751'


                line1 = f.readline().strip()
                line1 = line1.replace("' '", "'  '")
                self.chan_names = line1.split("'  '")
                f.close()
                # Now use the matplotlib load method to get the data
                self.data = np.loadtxt(fullname, skiprows=5)
                # Time is found in column 26
                self.time = self.data[:,26]
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
                self.data = array(datalist, dtype=float)
                # There is no time channel, so make one
                self.time = arange(0, len(self.data), dtype=float)
                self.time = self.time * self.dt


            # For STD files, the gains are 1 and zeros are zero
            self.gains = ones((self.nchans), dtype = float)
            self.zeros = zeros((self.nchans), dtype=float)

            # Compute the run stats
            self.run_stats()

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
        """

        if channel < 0 or channel > self.nchans:
            return None
        else:
            return (self.data[:,channel]-self.zeros[channel])* self.gains[channel]

    def getRAWData(self, channel):
        """ Returns an array containing the request channel of data
            in raw units (no conversion)
        """
        # For STD filesm there are no RAW units so return EU instead

        if channel < 0 or channel > self.nchans:
            return None
        else:
            return self.data[:,channel]

    def run_stats(self):
        """ Calculate important run stats like time of execute"""

        # Status is always at channel 25

        try:
            # Find where the status goes to 5, this is execute time
            status = list(self.data[:,25])
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
                chan_avg += self.data[x,channel]
                count += 1
            self.init_values.append(chan_avg/count)

        # Now compute the approach value of each channel btwn stdby and 
        # execute and store this

        self.appr_values = []
        for channel in range(self.nchans):
            chan_avg = 0.0
            count = 0
            for x in range(self.stdbyrec, self.execrec):
                chan_avg += self.data[x,channel]
                count += 1
            try:
                self.appr_values.append(chan_avg/count)
            except:
                self.appr_values.append(0.0)

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
            rundata = self.data[start:,:]
        else:
            rundata = self.data[start:end,:]

        # Compute the nose and sail depths
        self.compZnosesail(STDFile.GeoTable[self.boat], rundata)

        # Now to get the max and mins for the normal channels
        self.maxValues = []
        self.minValues = []
        self.maxTimes = []
        self.minTimes = []
        # set up a filter to eliminate spikes
        tau = 1.0
        tfact = (1 - m.exp(-self.dt/tau))
        for channel in range(self.nchans):
            # filter data first
            data = rundata[:,channel].tolist()
            for i in range(len(data)):
                if i > 0:
                    data[i] = data[i-1] + (data[i] - data[i-1])*tfact
            # Then get values
            chanmax = max(data)
            maxrec = data.index(chanmax)
            chanmin = min(data)
            minrec = data.index(chanmin)
            self.maxValues.append(chanmax)            
            self.minValues.append(chanmin)
            self.maxTimes.append(self.ntime[self.execrec+maxrec])
            self.minTimes.append(self.ntime[self.execrec+minrec])

        # Compute the maxes and mins of the nose and sail depth channels
        # Filter the data first
        for i in range(len(self.Znose)):
            if i > 0:
                self.Znose[i] = self.Znose[i-1] + (self.Znose[i] - self.Znose[i-1]) * tfact
                self.Zsail[i] = self.Zsail[i-1] + (self.Zsail[i] - self.Zsail[i-1]) * tfact
        self.maxZnose = max(self.Znose)
        self.maxZnosetime = self.ntime[self.execrec+self.Znose.index(self.maxZnose)]
        self.minZnose = min(self.Znose)
        self.minZnosetime = self.ntime[self.execrec+self.Znose.index(self.minZnose)]
        self.maxZsail = max(self.Zsail)
        self.maxZsailtime = self.ntime[self.execrec+self.Zsail.index(self.maxZsail)]
        self.minZsail = min(self.Zsail)
        self.minZsailtime = self.ntime[self.execrec+self.Zsail.index(self.minZsail)]



    def compZnosesail(self, geometry, data):
        """ Computes the nose and sail depth based on the geometry info
        Assumes that ZGA is at 22, pitch at 8, and roll at 7
        """
        radius, xnose, xsail, hsail = geometry
        zsail = -(hsail+radius)
        # Get the approach value based on appr pitch/roll
        self.Znoseappr = self.appr_values[22] + (-xnose * m.sin(m.radians(self.appr_values[8])))
        self.Zsailappr = self.appr_values[22] + (-xsail * m.sin(m.radians(self.appr_values[8]))+
                                                 zsail * m.cos(m.radians(self.appr_values[8]))*
                                                 m.cos(m.radians(self.appr_values[7])))

        self.Znose = []
        self.Zsail = []
        for tstep in range(len(data)):
            sinTH = m.sin(m.radians(data[tstep,8]))
            cosTH = m.cos(m.radians(data[tstep,8]))
            cosPH = m.cos(m.radians(data[tstep,7]))
            nosedepth = data[tstep,22] + (-xnose * sinTH)
            saildepth = data[tstep,22] + (-xsail * sinTH + zsail * cosTH * cosPH)
            self.Znose.append(nosedepth)
            self.Zsail.append(saildepth)


    def turnstats(self):
        """
            Returns the advance, transfer and tactical diameter
            for a turn maneuver
        """


        # extract the yaw data 
        yaw180 = self.getEUData(9)
        yawrate = self.getEUData(5)

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

        # Attempt to find the run on the path, return NONE if not found
        fullname = search_file_walk('run-'+run_number+'.tdms', search_path)
        
        if not fullname:
            fullname = search_file_walk('run_'+run_number+'.tdms', search_path)

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
            
            #import or create the time channel
            try:
                self.time = self.tdms_file_obj.channel_data('DATA', 'sys_time') #import absolute time channel
                self.time = self.time - self.time[0] # make the time channel relative to the start of the file
            except:
                # There is no time channel, so make one
                self.time = arange(0, self.tdm_length, dtype=float)
                self.time = self.time * .01
            
            # Get the run type out of the tdms file properties
            try:
                fileobj = self.tdms_file_obj.object()
                self.title = fileobj.properties['script_run_type']
            except:
                self.title = 'No Run Type Property Defined' 
                
            # Cals and channel names are all stored in the tdm_file_obj channel objects   
            try:
                #  Set up some variables to hold the values
                self.nchans = len(self.tdms_file_obj.group_channels('DATA'))
                self.cals = {}  #Dictionary to hold calibration info for each channel
                #self.gains = []
                #self.zeros = []
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
                self.run_stats()
            except:
                self.nchans = 0
                self.cals = {}
                #self.gains = ones((self.nchans), dtype=float)
                #self.zeros = zeros((self.nchans), dtype=float)
                print('we got an error')
                raise
            
            #read in all the data from the tmds file    
            self.data = self.tdms_file_obj.channel_data('DATA', self.chan_names[0])
            self.dataEU = self.cals[self.chan_names[0]](self.tdms_file_obj.channel_data('DATA', self.chan_names[0]))
            for i in range(1, self.nchans):
                self.data = np.column_stack((self.data, self.tdms_file_obj.channel_data('DATA', self.chan_names[i])))
                self.dataEU = np.column_stack((self.dataEU, self.cals[self.chan_names[i]](self.tdms_file_obj.channel_data('DATA', self.chan_names[i]))))

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
        
        if channel < 0 or channel > self.nchans:
            return None
        else:
            channame = self.chan_names[channel]
            col_array = self.tdms_file_obj.channel_data('DATA', channame)
            return self.cals[channame](col_array)
        
    def getRAWData(self, channel):
        """ Returns an array containing the request channel of data
            in raw units (no conversion)
        """
        
        if channel < 0 or channel > self.nchans:
            return None
        else:
            channame = self.chan_names[channel]
            col_array = self.tdms_file_obj.channel_data('DATA', channame)
            return col_array
            
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
         
        # For obc, we don't want to do the initial values for all 364
        # channels, so just set these to zeros
        self.init_values = zeros((self.nchans), dtype=float)

    def EU_file(self):
        """ Create a csv data file with the EU data
            Created in same dir as obc file with .eu extension
        """
        
	# First build a header with the channel titles in one line
        headerstr = ', '.join(self.chan_names)
        # now build a numpy array with all the EU data
        alldata = self.cals[chan_names[0]](self.tdms_file_obj.channel_data('DATA', self.chan_names[0]))
        for i in range(1, self.nchans):
            alldata = np.column_stack((alldata, self.gains[i]*(self.tdms_file_obj.channel_data('DATA', self.chan_names[i]))+self.zeros[i]))
	# Now output to the EU file
        np.savetxt(os.path.join(self.dirname, self.basename+'.eu'), alldata, fmt = '%10.9f', delimiter=', ', header=headerstr)

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

        # Attempt to find the run on the path, return NONE if not found
        fullname = search_file_walk(str('run-'+run_number+'.obc'), search_path)
        fname = (str('run-'+run_number+'.obc'), search_path)
        print(fname)

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
            calfile = os.path.join(dirname, 'run-'+run_number+'.cal')

            self.filename = filename
            self.dirname = dirname
            self.basename = 'run-'+run_number
            self.filetype = 'AM-obc'
            self.title = ''
            self.timestamp = time.ctime(os.path.getmtime(fullname))
            self.nchans = 0
            self.dt = 0.01

            # Because the obc files are large (>10Mb), using the load()
            # call takes 30-40s.  For faster access, keep the values as strings
            # until we need them

            self.data = []
            obcfile = open(fullname, 'r')
            for record in obcfile:
                record = record.rstrip()
                row = record.split()
                self.data.append(row)

            # There is no time channel, so make one
            self.time = arange(0, len(self.data), dtype=float)
            self.time = self.time * .01

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

            # try to get the cals and channel names from cal file    
            c = cfgparse.ConfigParser()
            try:
                c.add_file(str(calfile))
                #  Set up some variables to hold the values
                self.nchans = c.add_option('obc_channels', type='int').get()
                self.gains = []
                self.zeros = []
                self.chan_names = []
                self.alt_names = []
                self.data_pkt_locs = []
                self.eng_units = []
                self.cal_dates = []

                # Then read the ini file for the channel cals
                for channel in range(self.nchans):
                    self.gains.append(c.add_option('gain', type='float', keys='CHAN%d' % channel).get())
                    self.zeros.append(c.add_option('zero', type='float', keys='CHAN%d' % channel).get())
                    self.chan_names.append(c.add_option('sys_name', keys='CHAN%d' % channel).get().strip())
                    self.alt_names.append(c.add_option('alt_name', keys='CHAN%d' % channel).get().strip())
                    self.data_pkt_locs.append(c.add_option('data_pkt_loc', type='int', keys='CHAN%d' % channel).get())
                    self.eng_units.append(c.add_option('eng_units', keys='CHAN%d' % channel).get().strip())
                    self.cal_dates.append(c.add_option('cal_date', keys='CHAN%d' % channel).get())

                self.run_stats()
            except:
                self.nchans = 0
                self.gains = ones((self.nchans), dtype=float)
                self.zeros = zeros((self.nchans), dtype=float)
                raise
            
            self.dataEU = []  
            for row in range(len(self.data)):
                datarow = []
                for column in range(self.nchans):
                    datarow.append((float(self.data[row][column])-self.zeros[column]) * self.gains[column])
                self.dataEU.append(datarow)

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

        if channel < 0 or channel > self.nchans:
            return None
        else:
            column = []
            for x in range(len(self.data)):
                column.append(float(self.data[x][channel]))

            col_array = array((column), dtype=float)
            return (col_array-self.zeros[channel])* self.gains[channel]

    def getRAWData(self, channel):
        """ Returns an array containing the request channel of data
            in raw units (no conversion)
        """

        if channel < 0 or channel > self.nchans:
            return None
        else:
            column = []
            for x in range(len(self.data)):
                column.append(float(self.data[x][channel]))

            col_array = array((column), dtype=float)
            return col_array

    def run_stats(self):
        """ Calculate important run stats.
            Current Stats:
                time of standby
                time of execute
                normalized time (from exe)
        """


        # First we need to extract the mode channel
        status = []
        for x in range(len(self.data)):
            status.append(int(float(self.data[x][325])))
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

        # For obc, we don't want to do the initial values for all 364
        # channels, so just set these to zeros
        self.init_values = zeros((self.nchans), dtype=float)

    def EU_file(self):
        """ Create a csv data file with the EU data
            Created in same dir as obc file with .eu extension
        """

        # First open the output file using the filename
        eufile = open(os.path.join(self.dirname, self.basename+'.eu'), 'w')

        # First ouput the titles in one line
        for name in self.chan_names:
            eufile.write(name+',  ')
        eufile.write('\n')

        # Now output the EU data line by line
        for row in range(len(self.data)):
            for column in range(self.nchans):
                value = (float(self.data[row][column])-self.zeros[column]) * self.gains[column]
                eufile.write(str(value)+', ')
            eufile.write('\n')

        eufile.close()


#if __name__ == "__main__":

    #test = OBCFile('1409')
    #test = STDFile('9-4104.std', 'known')
    #test.info()
    #test.run_stats()
    #dummy = test.getEUData(12)
    #print test.stdbytime
    #print test.exectime
    #test.EU_file()
