#!/usr/bin/env python

import os,sys
import wx
from am_merge import MergeRun

# This routine allows for batch processing of a set of runs
# It reads a text file with the filename and path, the mrgdir and the merge file
# and then runs the merge

#testname = '/frmg/Autonomous_Model/Test_Data/OHIO_Replacement/10_02_35X/20120111/run-4765.obc'

# Open and read the batch script file
if len(sys.argv) < 2:
    print "Usage: merge_batch.py {scriptfile}"
else:

    try:
        print "Processing the batch file...\n"
        f = open(sys.argv[1], 'r')
        batch_lines = f.read().splitlines()
    except:
        print "Could not read batch file!"
        raise


    app=wx.PySimpleApp()

    for line in batch_lines:

        fullname, std_dir, merge_file = line.split()

        # First we need to extract the runnumber and merge parameters
        obcpath =  os.path.dirname(fullname)

        rootname, ext = os.path.splitext(os.path.basename(fullname))
        runnumber = rootname[4:]

        print "runnumber = ", runnumber
        print "stddir = " , std_dir
        print "merge_file = ", merge_file

        # Now change to the directory with the run
        os.chdir(obcpath)

        try:
            MergeRun(int(runnumber), std_dir, merge_file)
        except:
            print "Merge failed for run: ", runnumber
            

