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

from tools.search_file import *
from pylab import *
import cfgparse
import os.path, time

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
        """ Initialize the run, find and read in the data.
        The search_path defaults to the local directory.  The files must
        conform to the DELIMTXT format for now.  In the future maybe handle
        other formats."""

        # Attempt to find the run on the path, return empty structure if not found
        fullname = search_file(run_number+'.std', search_path)

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
        else:      
            dirname, filename = os.path.split(fullname)

            # First open the file and read the header info
            f = open(fullname, 'r')

            self.filename = filename
            self.dirname = dirname
            self.filetype = f.readline().strip()
            self.title = f.readline().strip()
            self.timestamp = f.readline().strip()

            line1 = f.readline().strip()
            line1 = line1.replace(',', ' ')
            self.nchans = int(line1.split()[0])
            self.dt = float(line1.split()[1])

            line1 = f.readline().strip()
            line1 = line1.replace("' '", "'  '")
            self.chan_names = line1.split("'  '")
            f.close()

            # Now use the matplotlib load method to get the data

            self.data = load(fullname, skiprows=5)

            # Time is found in column 26
            self.time = self.data[:,26]

            # For STD files, the gains are 1 and zeros are zero
            self.gains = ones((self.nchans), Float)
            self.zeros = zeros((self.nchans), Float)

            # Compute the run stats
            self.run_stats()

    def info(self):
        """ Prints information on the run"""

        print "Filename: %s" % self.filename
        try:
            print "Filetype: %s" % self.filetype
            print "Title: %s" % self.title
            print "Timestamp: %s" % self.timestamp
            print "# of channels: %d" % self.nchans
            print "DT: %f" % self.dt
            print "Channel Names: "
            for name in self.chan_names:
                print name,
            print
            print "Standby at record: %d  time: %f" % (self.stdbyrec, self.stdbytime)
            print "Execute at record: %d  time: %f" % (self.execrec, self.exectime)

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

        # Find where the status goes to 5, this is execute time
        status = list(self.data[:,25])
        self.execrec = status.index(5)
        self.exectime = self.time[self.execrec]
        self.stdbyrec = status.index(2)
        self.stdbytime = self.time[self.stdbyrec]

        # Compute the normalized time, i.e. time from execute
        self.ntime = self.time - self.exectime

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
        fullname = search_file_walk('run-'+run_number+'.obc', search_path)


        if not fullname:
            self.filename = ''
            self.dirname = ''
            self.filetype = 'None'
            self.title = ''
            self.timestamp = ''
            self.nchans = 0
            self.data = []
            self.time = []
            self.dt = 0

        else:      
            dirname, filename = os.path.split(fullname)
            runfile = os.path.join(dirname, 'run-'+run_number+'.run')
            calfile = os.path.join(dirname, 'run-'+run_number+'.cal')

            self.filename = filename
            self.dirname = dirname
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
            self.time = arange(0, len(self.data), typecode=Float)
            self.time = self.time * .01

        # try to get the run info from runfile
        try:
            lines = open(runfile).read().splitlines()
            for line in lines:
                if line.find('#RUNTYPE:') <> -1:
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
            c.add_file(calfile)
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
                self.chan_names.append(c.add_option('sys_name', keys='CHAN%d' % channel).get())
                self.alt_names.append(c.add_option('alt_name', keys='CHAN%d' % channel).get())
                self.data_pkt_locs.append(c.add_option('data_pkt_loc', type='int', keys='CHAN%d' % channel).get())
                self.eng_units.append(c.add_option('eng_units', keys='CHAN%d' % channel).get())
                self.cal_dates.append(c.add_option('cal_date', keys='CHAN%d' % channel).get())

            self.run_stats()
        except:
            self.nchans = 0
            self.gains = ones((self.nchans), Float)
            self.zeros = zeros((self.nchans), Float)


    def info(self):
        """ Prints information on the run"""

        print "Filename: %s" % self.filename
        try:
            print "Filetype: %s" % self.filetype
            print "Title: %s" % self.title
            print "Timestamp: %s" % self.timestamp
            print "# of channels: %d" % self.nchans
            print "DT: %f" % self.dt
            print "Channel Names: "
            for name in self.chan_names:
                print name,
            print
            print "Execute at record: %d  time: %f" % (self.execrec, self.exectime)
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

            col_array = array((column), Float)
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

            col_array = array((column), Float)
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
            status.append(int(self.data[x][325]))

        self.stdbyrec = status.index(0x0F33)
        self.stdbytime = self.time[self.stdbyrec]
        self.execrec = status.index(0x0F43)
        self.exectime = self.time[self.execrec]

        # Create a normalized time i.e. time since execute
        self.ntime = self.time - self.exectime

        # For obc, we don't want to do the initial values for all 364
        # channels, so just set these to zeros
        self.init_values = zeros((self.nchans), Float)


if __name__ == "__main__":

    test = OBCFile('2282')
    test.info()
    dummy = test.getEUData(12)
    print dummy
