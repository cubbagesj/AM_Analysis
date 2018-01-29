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

# Imports - Locale Packages
from search_file import search_file_walk


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
            fname = (run_number+'.std', search_path)
            print(fname)

        if not fullname:
            if not search_path == 'c:\AM_merge_data':
                if not os.path.exists(search_path):
                    # if the file does not exist and the search path does not exist
                    # check the default local directory as a last resort
                    fullname = search_file_walk(run_number+'.std', 'c:\AM_merge_data')

        if not fullname:
            # Populate empty structure if no file found
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

                f.close()

                # Now use pandas to get the data and channel names
                self.data = pd.read_table(fullname, sep='\s+', skiprows=4)
                self.chan_names = self.data.columns

                # Time is found in column 26
                self.time = self.data["'time'"]
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
            
            channel is a number
        """

        if channel < 0 or channel > self.nchans:
            return None
        else:
            return self.dataEU.ix[:,channel]

    def getRAWData(self, channel):
        """ Returns an array containing the request channel of data
            in raw units (no conversion)
        """
        
        if channel < 0 or channel > self.nchans:
            return None
        else:
            return self.data.ix[:,channel]

    def run_stats(self):
        """ Calculate important run stats like time of execute"""

        # Status is always at channel 25

        try:
            # Find where the status goes to 5, this is execute time
            status = list(self.data.ix[:,25])
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
                chan_avg += self.data.ix[x,channel]
                count += 1
            self.init_values.append(chan_avg/count)

        # Now compute the approach value of each channel btwn stdby and 
        # execute and store this

        self.appr_values = []
        for channel in range(self.nchans):
            chan_avg = 0.0
            count = 0
            for x in range(self.stdbyrec, self.execrec):
                chan_avg += self.data.ix[x,channel]
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
        # Removed for now until I can work out with new structure
        pass

    def compZnosesail(self, geometry, data):
        """ Computes the nose and sail depth based on the geometry info
        Assumes that ZGA is at 22, pitch at 8, and roll at 7
        """
        # Removed for now until I can work out with new structure
        pass

    def turnstats(self):
        """
            Returns the advance, transfer and tactical diameter
            for a turn maneuver
        """

        # Removed for now until I can work out with new structure
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
