# AM_Merge.py
#
# Copyright (C) 2006-2018 - Samuel J. Cubbage
# 
#  This program is part of the Autonomous Model Software Tools Package
# 
"""
    AM_merge - This program is part of the Autonomous Model (AM) software
    suite.  It converts the onboard data file (.obc) into the NSWC standard 
    merge file (.STD) using the DELIMTXT format.

    This program must be run from the directory containing the run data,
    including the .obc, .cal and .run files. The channels to place in the merged
    file are defined in the merge.inp file that is located in the operating 
    directory.  See the notes in this file for how to specify channel parameters.

    The merge process converts the data into engineering units and scales the 
    values based on the scaling parameters defined in the merge.inp file.  The 
    program also processes the data from the dynos and handles all of the
    conversions and interaction matricies.

    The output of this merge program have been compared to that of the original 
    merge program on the ALPHA and verified to be accurate.  Every attempt has
    been made to make the program code as modular as possible in order to handle
    any future changes in instrumentation.


    REV. HISTORY:
        04/07/06 - Initial development
        04/20/06 - Modified to read constants from merge.inp file
        04/21/06 - Adding 6DOF dyno processing
        05/23/06 - Fixed bug in alpha computation
        01/29/07 - Placed under revision control using Subversion
        04/10/07 - Modified for inclusion in AM_Tools program
        10/29/07 - Updated to use calfile class
        09/12/18 - Rewrite to use pandas structures
"""
# ---------------------  Imports --------------------
# cfgparse is to handle the merge.inp file
# dynos for the dyno classes
#----------------------------------------------------

import os, sys, time
import utm
import plottools as plottools
import pandas as pd
import numpy as np
from filetypes import STDFile
import datatools as dt

def MergeRun(fullname, runnumber, std_dir, merge_file='MERGE.INP'):  

    # LOG File - Open up a file to write diagnostic info to
    #
    try:
        logfile = open('merge.log','w')
    except:
        logfile = open('/dev/null', 'w')
    logfile.write("AM_merge:  Merging run %d \n" % runnumber)
    logfile.write('Full pathname: %s \n' % fullname)
    logfile.write('STD Directory: %s \n' % std_dir)
    logfile.write("AM_Merge.py -- Autonomous model merge program\n")
    logfile.write(time.strftime("%a %b %d %H:%M:%S %Y")+" \n")

    #----------------------------------
    #  Read and process the merge.inp file
    #----------------------------------
    logfile.write("Configuring the merge program......\n",)
    try:
        logfile.write("Opening the merge input file\n")
        f = open(merge_file, 'r')
        merge_lines = f.read().splitlines()
        logfile.write("%s opened and %d lines read \n" % (merge_file,len(merge_lines)))
    except:
        logfile.write('Could not open the merge.inp file!')
        f.close()
        return

    # Now we need to split the merge file into 2 sections. So search for our markers
    # and filter out the comments

    input_sec = []
    chan_sec = []
    input_flag = 0
    chan_flag = 0

    logfile.write("\nParsing the merge.inp file....\n")
    for line in merge_lines:
        if line == '':
            continue
        elif line[0] == '#':
            continue
        elif line.find('[END_INPUTS]') != -1:
            logfile.write('END_INPUTS found\n')
            input_flag = 0
        elif line.find('[END_CHANS]') != -1:
            logfile.write('END_CHANS found\n')
            chan_flag = 0

        if chan_flag == 1:
            chan_sec.append(line)
        elif input_flag == 1:
            input_sec.append(line)

        if line.find('[BEGIN_INPUTS]') != -1:
            logfile.write('BEGIN_INPUTS found\n')
            input_flag = 1
        elif line.find('[BEGIN_CHANS]') != -1:
            logfile.write('BEGIN_CHANS found\n')
            chan_flag = 1
        elif line.find('[END_CHANS]') != -1:
            logfile.write('END_CHANS found\n')
            chan_flag = 0   

    # Convert the inputs section into a dictionary for later use
    mrg_input = {}
    for line in input_sec:
        line = line.upper()
        entry = line.split()
        mrg_input[entry[0]] = float(entry[1])

    logfile.write('\nInputs section converted - INPUTS:\n')
    logfile.write('Key\t\tValue\n')
    for temp in mrg_input.keys():
        logfile.write('%s \t\t %s \n' % (temp, mrg_input[temp]))

    # Read the channels for the merge out of the channel section

    mrg_names = []
    mrg_chans = []
    mrg_scale = []
    mrg_zero = []

    for line in chan_sec:
        values = line.split()
        mrg_names.append(values[0])
        mrg_chans.append(int(values[1]))
        mrg_scale.append(float(values[2]))
        mrg_zero.append(int(values[3]))
    
    logfile.write('\nMerge Channels Processed - MERGE CHANNELS\n')
    logfile.write('Chan \t Name \t OBC Chan \t Scale \t Zero\n')
    for x in range(len(mrg_names)):
        logfile.write('%d\t%s\t%d\t\t%f\t%d\n' % (x, mrg_names[x], mrg_chans[x], mrg_scale[x], mrg_zero[x]))
    logfile.write('Merge Configuration Completed\n')

    # Main Program Loop - Do this for each run in the input list
    #----------------------------------------
    # Read in the file using the library routines
    #----------------------------------------
    logfile.write('\nProcessing run: run-'+str(runnumber))
    logfile.write('\n------------------------------------------\n')
    
    runObj = plottools.get_run(fullname)


    #--------------------------------------
    # Now we start to process the OBC file
    #
    # This is where the bulk of the work in the
    # program is done
    #--------------------------------------


    logfile.write('\nProcessing the OBC file............ \n')
    logfile.write('Created: ' + time.ctime(os.path.getmtime(fullname)))
    logfile.write('\nFile size: %d bytes\n' % os.path.getsize(fullname))
    logfile.write('Approx Run Length: %4.1f seconds\n' % (os.path.getsize(fullname)/155366.0))


    # First set up some constants used in the calculations
    # These come from the values read from the input file
    cb_id = int(mrg_input['CB_ID'])
    c_dt = mrg_input['OBC_DT']
    c_skip = mrg_input['SKIP']
    c_lambda = mrg_input['LAMBDA']
    c_sqrtlambda = pow(c_lambda, .5)
    c_FSdt = c_dt * c_sqrtlambda
    c_length = mrg_input['LENGTH']
    
    mode_chan = int(mrg_input['MODE'])
    u_chan = int(mrg_input['U_CHAN'])
    v_chan = int(mrg_input['V_CHAN'])
    w_chan = int(mrg_input['W_CHAN'])
    big_u_chan = int(mrg_input['BIG_U_CHAN'])
    
    # This is for the TB model that had two props
    try:
        stbd_rpm_chan = int(mrg_input['STBD_RPM_CHAN'])
        port_rpm_chan = int(mrg_input['PORT_RPM_CHAN'])
        stbd_rpm_com = int(mrg_input['STBD_RPM_COM'])
        port_rpm_com = int(mrg_input['PORT_RPM_COM'])
    except:
        stbd_rpm_chan = 29
        port_rpm_chan = 30
        stbd_rpm_com = 217
        port_rpm_com = 232


    # Depth sensor location and channel
    zsensor = (mrg_input['Z_X_LOC'],
               mrg_input['Z_Y_LOC'],
               mrg_input['Z_Z_LOC'],
               int(mrg_input['Z_CHAN']))

    try:
        zsensor2 = (mrg_input['Z2_X_LOC'],
                   mrg_input['Z2_Y_LOC'],
                   mrg_input['Z2_Z_LOC'],
                   int(mrg_input['Z2_CHAN']))
    except: 
        zsensor2 = (0, 0, 0, 0)

    # ADCP Location
    ADCPLoc = (mrg_input['ADCP_X'],
               mrg_input['ADCP_Y'],
               mrg_input['ADCP_Z'])

    # Open the STD file to write the header information

    apprU = runObj.getEUData(336).mean()/100 * c_sqrtlambda
    runkind = runObj.getEUData(343).mean()

    stdfilename = std_dir+'/'+str(cb_id)+'-'+str(runnumber)+'.std'
    stdfile = open(stdfilename, 'w')

    stdfile.write(" 'DELIMTXT' \n")
    stdfile.write(" 'AM:run-%d:%3.1f:%d:  %s '\n" % (runnumber, apprU, runkind, runObj.title))
    stdfile.write(" '"+time.ctime(os.path.getmtime(fullname))+"' \n")
    stdfile.write(" %d, %10.6f, %8.4f \n" %(len(mrg_names), c_FSdt*c_skip, c_length))

    for name in mrg_names:
        stdfile.write("'%s' " % name)

    stdfile.write("\n")

    logfile.close()
    EUdata = []
    # Now we start the process of converting to fullscale values

    # Set up some convience values for later use
    # Body Angles in radians
    theta = np.radians(runObj.theta)
    phi = np.radians(runObj.phi)
    psi = np.radians(runObj.psi)
    
    p_FS = runObj.p.copy()
    p_FS *= pow(c_lambda, -.5)
    q_FS = runObj.q.copy()
    q_FS *= pow(c_lambda, -.5)
    r_FS = runObj.r.copy()
    r_FS *= pow(c_lambda, -.5)

    # Initialize spike filters
    Uprev = Vprev = Wprev = 0.0

    rawStatus = runObj.getEUData(mode_chan).copy()

    for i in range(len(mrg_names)):

        if mrg_chans[i] < 800:              # Normal Channel
            EUdata = runObj.getEUData(mrg_chans[i]).values
            EUdata -= runObj.avgEUzeros[mrg_chans[i]]*mrg_zero[i]
            EUdata *= pow(c_lambda, mrg_scale[i])
                    
            if mrg_scale[i] >= 3:
                EUdata *= 1.0284
            if mrg_scale[i] == 4:       # in-lb to ft-lb conversion
                EUdata *= 0.083333            
                
        elif mrg_chans[i] == 800:            # Empty channel
            EUdata = np.zeros(len(runObj.getEUData(0)))
            # Need to add number to blank names to avoid duplcates
            mrg_names[i] += str(i)
        elif mrg_chans[i] == 801:          # Time Channel 
            EUdata = (runObj.time * 100) * c_FSdt
            
        elif mrg_chans[i] == 802:     # ZCG
            EUdata = (runObj.getEUData(mrg_chans[zsensor[3]])).copy()
            EUdata *= pow(c_lambda, 1)
            EUdata += (zsensor[0] * np.sin(theta)) - np.cos(theta)*(zsensor[1] * np.sin(phi) + zsensor[2] * np.cos(phi))

        elif mrg_chans[i] == 804:           #Filtered and Corr. ADCP u
            EUdata = runObj.u_adcp.copy()
            for t in range(len(EUdata)):
                if abs(EUdata[t]) > 70:
                    EUdata[t] = Uprev
                Uprev = EUdata[t]
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata -= ((q_FS/57.296)*ADCPLoc[2])
            # We need this later on for alpha/beta calcs so store it
            u_FS = EUdata.copy()
            
        elif mrg_chans[i] == 805:           #Filtered and Corr ADCP v
            EUdata = runObj.v_adcp.copy()
            for t in range(len(EUdata)):
                if abs(EUdata[t]) > 15:
                    EUdata[t] = Vprev
                Vprev = EUdata[t]
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata += (((p_FS/57.296)*ADCPLoc[2])-((r_FS/57.296)*ADCPLoc[0]))
            # We need this later on for alpha/beta calcs so store it
            v_FS = EUdata.copy()
            
        elif mrg_chans[i] == 806:           #Filtered and Corr ADCP w
            EUdata = runObj.w_adcp.copy()
            for t in range(len(EUdata)):
                if abs(EUdata[t]) > 15:
                    EUdata[t] = Wprev
                Wprev = EUdata[t]
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata += (((q_FS/57.296)*ADCPLoc[0])-((p_FS/57.296)*ADCPLoc[1]))
            # We need this later on for alpha/beta calcs so store it
            w_FS = EUdata.copy()

        elif mrg_chans[i] == 807 and 'Rotor' in runObj.sp_gauges:         # Computed Rotor Fx
            EUdata = runObj.getEUData('Rotor_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 808 and 'Rotor' in runObj.sp_gauges:         # Computed Rotor Fy
            EUdata = runObj.getEUData('Rotor_CFy') 
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 809 and 'Rotor' in runObj.sp_gauges:         # Computed Rotor Fz
            EUdata = runObj.getEUData('Rotor_CFz') 
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 810 and 'Rotor' in runObj.sp_gauges:         # Computed Rotor Mx
            EUdata = runObj.getEUData('Rotor_CMx') 
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 811 and 'Rotor' in runObj.sp_gauges:         # Computed Rotor My
            EUdata = runObj.getEUData('Rotor_CMy') 
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 812 and 'Rotor' in runObj.sp_gauges:         # Computed Rotor Mz
            EUdata = runObj.getEUData('Rotor_CMz') 
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333

        elif mrg_chans[i] == 813 and 'Stator' in runObj.sp_gauges:         # Computed Stator Fx
            EUdata = runObj.getEUData('Stator_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 814 and 'Stator' in runObj.sp_gauges:         # Computed Stator Fy
            EUdata = runObj.getEUData('Stator_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 815 and 'Stator' in runObj.sp_gauges:         # Computed Stator Fz
            EUdata = runObj.getEUData('Stator_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 816 and 'Stator' in runObj.sp_gauges:         # Computed Stator Mx
            EUdata = runObj.getEUData('Stator_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 817 and 'Stator' in runObj.sp_gauges:         # Computed Stator My
            EUdata = runObj.getEUData('Stator_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 818 and 'Stator' in runObj.sp_gauges:         # Computed Stator Mz
            EUdata = runObj.getEUData('Stator_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333

        elif mrg_chans[i] == 820:           # Status
            EUdata = rawStatus.replace([0x0F33, 0x0F43, 4097, 19, 0x0F13,0x0F23, 1],
                                       [2, 5,0,0,0,0,0]).values
        elif mrg_chans[i] == 821:           # Alpha
            EUdata = np.degrees(np.arctan2(w_FS, u_FS))
        elif mrg_chans[i] == 822:           # Beta
            np.seterr(divide='ignore', invalid='ignore')
            EUdata = -np.degrees(np.arcsin(np.divide(v_FS, bigU_FS)))
        elif mrg_chans[i] == 823:           # Big U from ADCP
            EUdata = runObj.bigU.copy()
            EUdata *= pow(c_lambda, .5)
            # We need this later on for alpha/beta calcs so store it
            bigU_FS = EUdata.copy()

        elif mrg_chans[i] == 824:           # Big U from ADCP in knots
            EUdata = runObj.bigU.copy()
            EUdata *= pow(c_lambda, .5)
            EUdata /= 1.6878

        elif mrg_chans[i] == 830 and 'SOF1' in runObj.sp_gauges:         # Computed SOF1 Fx
            EUdata = runObj.getEUData('SOF1_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 831 and 'SOF1' in runObj.sp_gauges:         # Computed SOF1 Fy
            EUdata = runObj.getEUData('SOF1_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 832 and 'SOF1' in runObj.sp_gauges:         # Computed SOF1 Fz
            EUdata = runObj.getEUData('SOF1_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 833 and 'SOF1' in runObj.sp_gauges:         # Computed SOF1 Mx
            EUdata = runObj.getEUData('SOF1_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 834 and 'SOF1' in runObj.sp_gauges:         # Computed SOF1 My
            EUdata = runObj.getEUData('SOF1_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 835 and 'SOF1' in runObj.sp_gauges:         # Computed SOF1 Mz
            EUdata = runObj.getEUData('SOF1_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333

        elif mrg_chans[i] == 840 and 'SOF2' in runObj.sp_gauges:         # Computed SOF2 Fx
            EUdata = runObj.getEUData('SOF2_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 841 and 'SOF2' in runObj.sp_gauges:         # Computed SOF2 Fy
            EUdata = runObj.getEUData('SOF2_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 842 and 'SOF2' in runObj.sp_gauges:         # Computed SOF2 Fz
            EUdata = runObj.getEUData('SOF2_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 843 and 'SOF2' in runObj.sp_gauges:         # Computed SOF2 Mx
            EUdata = runObj.getEUData('SOF2_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 844 and 'SOF2' in runObj.sp_gauges:         # Computed SOF2 My
            EUdata = runObj.getEUData('SOF2_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 845 and 'SOF2' in runObj.sp_gauges:         # Computed SOF2 Mz
            EUdata = runObj.getEUData('SOF2_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333

        elif mrg_chans[i] == 850 and 'Kistler' in runObj.sp_gauges:         # Computed Kistler Fx
            EUdata = runObj.getEUData('Kistler_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 851 and 'Kistler' in runObj.sp_gauges:         # Computed Kistler Fy
            EUdata = runObj.getEUData('Kistler_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 852 and 'Kistler' in runObj.sp_gauges:         # Computed Kistler Fz
            EUdata = runObj.getEUData('Kistler_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 853 and 'Kistler' in runObj.sp_gauges:         # Computed Kistler Mx
            EUdata = runObj.getEUData('Kistler_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 854 and 'Kistler' in runObj.sp_gauges:         # Computed Kistler My
            EUdata = runObj.getEUData('Kistler_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 855 and 'Kistler' in runObj.sp_gauges:         # Computed Kistler Mz
            EUdata = runObj.getEUData('Kistler_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
            
        elif mrg_chans[i] == 860 and '6DOF1' in runObj.sp_gauges:         # Computed 6DOF1 Fx
            EUdata = runObj.getEUData('6DOF1_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 861 and '6DOF1' in runObj.sp_gauges:         # Computed 6DOF1 Fy
            EUdata = runObj.getEUData('6DOF1_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 862 and '6DOF1' in runObj.sp_gauges:         # Computed 6DOF1 Fz
            EUdata = runObj.getEUData('6DOF1_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 863 and '6DOF1' in runObj.sp_gauges:         # Computed 6DOF1 Mx
            EUdata = runObj.getEUData('6DOF1_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 864 and '6DOF1' in runObj.sp_gauges:         # Computed 6DOF1 My
            EUdata = runObj.getEUData('6DOF1_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 865 and '6DOF1' in runObj.sp_gauges:         # Computed 6DOF1 Mz
            EUdata = runObj.getEUData('6DOF1_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333

        elif mrg_chans[i] == 870 and '6DOF2' in runObj.sp_gauges:         # Computed 6DOF1 Fx
            EUdata = runObj.getEUData('6DOF2_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 871 and '6DOF2' in runObj.sp_gauges:         # Computed 6DOF1 Fy
            EUdata = runObj.getEUData('6DOF2_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 872 and '6DOF2' in runObj.sp_gauges:         # Computed 6DOF1 Fz
            EUdata = runObj.getEUData('6DOF2_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 873 and '6DOF2' in runObj.sp_gauges:         # Computed 6DOF1 Mx
            EUdata = runObj.getEUData('6DOF2_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 874 and '6DOF2' in runObj.sp_gauges:         # Computed 6DOF1 My
            EUdata = runObj.getEUData('6DOF2_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 875 and '6DOF2' in runObj.sp_gauges:         # Computed 6DOF1 Mz
            EUdata = runObj.getEUData('6DOF2_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333

        elif mrg_chans[i] == 880:                                   #Equiv Stern
            EUdata = (runObj.getEUData(mrg_chans[32]) +
                      runObj.getEUData(mrg_chans[33]) +
                      runObj.getEUData(mrg_chans[34]) +
                      runObj.getEUData(mrg_chans[35])) / 4.0
        elif mrg_chans[i] == 881:                                   #Equiv Rudder
            EUdata = (-runObj.getEUData(mrg_chans[32]) +
                      runObj.getEUData(mrg_chans[33]) -
                      runObj.getEUData(mrg_chans[34]) +
                      runObj.getEUData(mrg_chans[35]))/4.0

##                elif mrg_chans[i] == 890:                                   #Stbd RPM Flip
##                    EUdata[i] = (rawdata[stbd_rpm_chan]-cal.zeros[stbd_rpm_chan])*cal.gains[stbd_rpm_chan]
##                    if rawdata[stbd_rpm_com] < -50:
##                        EUdata[i] *= -1
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                elif mrg_chans[i] == 891:                                   #Port RPM Flip
##                    EUdata[i] = (rawdata[port_rpm_chan]-cal.zeros[port_rpm_chan])*cal.gains[port_rpm_chan]
##                    if rawdata[port_rpm_com] < -50:
##                        EUdata[i] *= -1
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##              
        elif mrg_chans[i] == 890 and '6DOF3' in runObj.sp_gauges:         # Computed 6DOF1 Fx
            EUdata = runObj.getEUData('6DOF3_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 891 and '6DOF3' in runObj.sp_gauges:         # Computed 6DOF1 Fy
            EUdata = runObj.getEUData('6DOF3_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 892 and '6DOF3' in runObj.sp_gauges:         # Computed 6DOF1 Fz
            EUdata = runObj.getEUData('6DOF3_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 893 and '6DOF3' in runObj.sp_gauges:         # Computed 6DOF1 Mx
            EUdata = runObj.getEUData('6DOF3_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 894 and '6DOF3' in runObj.sp_gauges:         # Computed 6DOF1 My
            EUdata = runObj.getEUData('6DOF3_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 895 and '6DOF3' in runObj.sp_gauges:         # Computed 6DOF1 Mz
            EUdata = runObj.getEUData('6DOF3_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333

        elif mrg_chans[i] == 900 and '6DOF4' in runObj.sp_gauges:         # Computed 6DOF1 Fx
            EUdata = runObj.getEUData('6DOF4_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 901 and '6DOF4' in runObj.sp_gauges:         # Computed 6DOF1 Fy
            EUdata = runObj.getEUData('6DOF4_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 902 and '6DOF4' in runObj.sp_gauges:         # Computed 6DOF1 Fz
            EUdata = runObj.getEUData('6DOF4_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 903 and '6DOF4' in runObj.sp_gauges:         # Computed 6DOF1 Mx
            EUdata = runObj.getEUData('6DOF4_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 904 and '6DOF4' in runObj.sp_gauges:         # Computed 6DOF1 My
            EUdata = runObj.getEUData('6DOF4_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 905 and '6DOF4' in runObj.sp_gauges:         # Computed 6DOF1 Mz
            EUdata = runObj.getEUData('6DOF4_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333

        elif mrg_chans[i] == 910 and '6DOF5' in runObj.sp_gauges:         # Computed 6DOF1 Fx
            EUdata = runObj.getEUData('6DOF5_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 911 and '6DOF5' in runObj.sp_gauges:         # Computed 6DOF1 Fy
            EUdata = runObj.getEUData('6DOF5_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 912 and '6DOF5' in runObj.sp_gauges:         # Computed 6DOF1 Fz
            EUdata = runObj.getEUData('6DOF5_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 913 and '6DOF5' in runObj.sp_gauges:         # Computed 6DOF1 Mx
            EUdata = runObj.getEUData('6DOF5_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 914 and '6DOF5' in runObj.sp_gauges:         # Computed 6DOF1 My
            EUdata = runObj.getEUData('6DOF5_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 915 and '6DOF5' in runObj.sp_gauges:         # Computed 6DOF1 Mz
            EUdata = runObj.getEUData('6DOF5_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333

        elif mrg_chans[i] == 920 and '6DOF6' in runObj.sp_gauges:         # Computed 6DOF1 Fx
            EUdata = runObj.getEUData('6DOF6_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 921 and '6DOF6' in runObj.sp_gauges:         # Computed 6DOF1 Fy
            EUdata = runObj.getEUData('6DOF6_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 922 and '6DOF6' in runObj.sp_gauges:         # Computed 6DOF1 Fz
            EUdata = runObj.getEUData('6DOF6_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 923 and '6DOF6' in runObj.sp_gauges:         # Computed 6DOF1 Mx
            EUdata = runObj.getEUData('6DOF6_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 924 and '6DOF6' in runObj.sp_gauges:         # Computed 6DOF1 My
            EUdata = runObj.getEUData('6DOF6_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 925 and '6DOF6' in runObj.sp_gauges:         # Computed 6DOF1 Mz
            EUdata = runObj.getEUData('6DOF6_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
 
##                elif mrg_chans[i] == 960:                                   #gps Easting
##                    EUdata[i] = easting
##                    EUdata[i] *=pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 3.2808399
##                elif mrg_chans[i] == 961:                                   #gps Northing
##                    EUdata[i] = -northing
##                    EUdata[i] *=pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 3.2808399
##
##                elif mrg_chans[i] == 965:                                   # Computed pitch from depth gages
##                    # compute pitch using depth2 and depth3 - hardwired for now
##                    EUdata[i] = degrees(arcsin((EUdata[zsensor[3]] - EUdata[zsensor2[3]])/(zsensor2[0] - zsensor[0])))
##
        elif mrg_chans[i] == 970 and 'Kistler3' in runObj.sp_gauges:         # Computed Kistler Fx
            EUdata = runObj.getEUData('Kistler3_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 971 and 'Kistler3' in runObj.sp_gauges:         # Computed Kistler Fy
            EUdata = runObj.getEUData('Kistler3_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 972 and 'Kistler3' in runObj.sp_gauges:         # Computed Kistler Fz
            EUdata = runObj.getEUData('Kistler3_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 973 and 'Kistler3' in runObj.sp_gauges:         # Computed Kistler Mx
            EUdata = runObj.getEUData('Kistler3_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 974 and 'Kistler3' in runObj.sp_gauges:         # Computed Kistler My
            EUdata = runObj.getEUData('Kistler3_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 975 and 'Kistler3' in runObj.sp_gauges:         # Computed Kistler Mz
            EUdata = runObj.getEUData('Kistler3_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333

        elif mrg_chans[i] == 980 and 'Kistler3_2' in runObj.sp_gauges:         # Computed Kistler Fx
            EUdata = runObj.getEUData('Kistler3_2_CFx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 981 and 'Kistler3_2' in runObj.sp_gauges:         # Computed Kistler Fy
            EUdata = runObj.getEUData('Kistler3_2_CFy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 982 and 'Kistler3_2' in runObj.sp_gauges:         # Computed Kistler Fz
            EUdata = runObj.getEUData('Kistler3_2_CFz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
        elif mrg_chans[i] == 983 and 'Kistler3_2' in runObj.sp_gauges:         # Computed Kistler Mx
            EUdata = runObj.getEUData('Kistler3_2_CMx')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 984 and 'Kistler3_2' in runObj.sp_gauges:         # Computed Kistler My
            EUdata = runObj.getEUData('Kistler3_2_CMy')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333
        elif mrg_chans[i] == 985 and 'Kistler3_2' in runObj.sp_gauges:         # Computed Kistler Mz
            EUdata = runObj.getEUData('Kistler3_2_CMz')
            EUdata *= pow(c_lambda, mrg_scale[i])
            EUdata *= 1.0284
            EUdata *= .083333


        if i == 0:  # First time through
            dataSTD = pd.DataFrame(EUdata, columns=[mrg_names[i]], dtype=float)
        else:
            dataSTD[mrg_names[i]] = EUdata
    
    # Append rawstatus to the end for filtering
    dataSTD['rawStatus'] = rawStatus
    
    # Only want approach through run
    dataSTDrun = dataSTD.loc[((dataSTD['rawStatus'] >= 0x0F23) & 
                              (dataSTD['rawStatus']  <= 0x0f43)) | 
                              (dataSTD['rawStatus'] <= 1)  ].copy(deep=True)
    # Drop the rawStatus Column
    dataSTDrun.drop('rawStatus', 1, inplace=True)
       
    # Now write out the data
    dataSTDrun.to_csv(stdfile, index=False, header=False, sep=' ', float_format='%12.7e')
    
 
    stdfile.close()

    # The following code is used to offset and rotate the x,y, positions so that
    # the position at execute is (0,0) and the initial track is along the x-axis
    # To do this we need to re-read the file to get the stats and then rewrite the 
    # new data back out.

    # At this point in the code the name of the std file is in stdfilename.  Us this 
    # in a call to the STDFile class to read in the file and get the stats

    # Wrap it in a try clause in case we get an error
    try:
        stdrun = STDFile(stdfilename, 'known')
        
        stdrunxpos = stdrun.getEUData(20)
        stdrunypos = stdrun.getEUData(21)
        
        t1 = stdrunypos[stdrun.execrec]
        t2 = stdrunypos[stdrun.execrec-50]
        t3 = stdrunxpos[stdrun.execrec]
        t4 = stdrunxpos[stdrun.execrec-50]
        if t3 - t4 != 0:
            test = (stdrunypos[stdrun.execrec]-stdrunypos[stdrun.execrec-50])/(stdrunxpos[stdrun.execrec] - stdrunxpos[stdrun.execrec-50])
            stdruntrack = np.arctan(test)
        else:
            stdruntrack = 0
       
        if stdruntrack <=0:
            stdruntrack = stdruntrack + 2*np.pi
        else:
            stdruntrack = stdruntrack + np.pi
    
        stdrunxposzero = (stdrunxpos[stdrun.execrec]*np.cos(stdruntrack) + 
                          stdrunypos[stdrun.execrec]*np.sin(stdruntrack))
        stdrunyposzero = (-stdrunxpos[stdrun.execrec]*np.sin(stdruntrack) + 
                          stdrunypos[stdrun.execrec]*np.cos(stdruntrack))
        
        # Got needed info, now process
    
        stdfile = open(stdfilename, 'r')
        newfile = open(stdfilename+'new','w')
        
        # Copy over the header information
        for x in range(5):
            newfile.write(stdfile.readline())
    
    
        rot_x = (stdrun.dataEU[stdrun.dataEU.columns[20]] * np.cos(stdruntrack) + 
                 stdrun.dataEU[stdrun.dataEU.columns[21]] * np.sin(stdruntrack))
        rot_y = (-stdrun.dataEU[stdrun.dataEU.columns[20]] * np.sin(stdruntrack) + 
                 stdrun.dataEU[stdrun.dataEU.columns[21]] * np.cos(stdruntrack))

        stdrun.dataEU[stdrun.dataEU.columns[20]] = (rot_x - stdrunxposzero)
        stdrun.dataEU[stdrun.dataEU.columns[21]] = (rot_y - stdrunyposzero)
    
        stdrun.dataEU.to_csv(newfile, index=False, header=False, sep=' ', float_format='%12.7e')
    

        stdfile.close()
        newfile.close()
        os.remove(stdfilename)
        os.rename(stdfilename+'new', stdfilename)
    except:
        logfile.write('Error in rotating track data!\n')
        
        
    # Data Consistency Check
    # This section performs a data consistency check on the velocity and motions 
    # data.  It creates computed values of u, v, w from the motions data and appends
    # these columns to the STD file
    
#    logfile.write('Computing data consistency\n' )
    rundata = STDFile(stdfilename, 'known')
    
    # Now we have the data so we begin the processing
    # We are going to assume that phi, theta, psi are correct along with u,v from
    # the ADCP

    # LN200 Checkout -----------
    
    # The first step is to check if p,q,r are consistant with phi, theta, psi
    # We can do this by using phi, theta, psi to compute p,q,r.
    # The steps are: - differentiate phi,theta, psi to get phidot, thetadot, psidot
    #                - transform to body coordinates using equations from 2510
    #                - Compare the computed versus the measured values
    #
    # Before we differentiate need to convert and filter signals
    #
    # Convert to radians for easier math

    # Get original phi,theta,psi and p,q,r
    # yawFilter removes the yaw flips
    thetarad = np.radians(rundata.theta)
    phirad = np.radians(rundata.phi)
    psirad = np.radians(dt.yawFilter(rundata.psi))

    prad = np.radians(rundata.p)
    qrad = np.radians(rundata.q)
    rrad = np.radians(rundata.r)
    
    pradf = dt.butter_lowpass_filter(prad, .01/rundata.dt, 1/rundata.dt, 2)
    qradf = dt.butter_lowpass_filter(qrad, .01/rundata.dt, 1/rundata.dt, 2)
    rradf = dt.butter_lowpass_filter(rrad, .01/rundata.dt, 1/rundata.dt, 2)
    

    # Filter angles so derivatives are smooth - bit resolution noise makes original
    # signal steppy.
    thetaradf = dt.butter_lowpass_filter(thetarad, .01/rundata.dt, 1/rundata.dt, 2)
    phiradf = dt.butter_lowpass_filter(phirad, .01/rundata.dt, 1/rundata.dt, 2)
    psiradf = dt.butter_lowpass_filter(psirad, .01/rundata.dt, 1/rundata.dt, 2)

    # Now we get thetadot, psidot, phidot by differentiating
    # add a point to the end to keep array size the same

    thetadot = np.append(np.diff(thetaradf)/(rundata.dt), 0.0)
    phidot = np.append(np.diff(phiradf)/(rundata.dt), 0.0)
    psidot = np.append(np.diff(psiradf)/(rundata.dt), 0.0)

    # Now we can compute p,q,r from these values using 2510 equations

    pcomp = phidot - psidot*np.sin(thetaradf)
    qcomp = psidot*np.cos(thetaradf)*np.sin(phiradf) + thetadot*np.cos(phiradf)
    rcomp = psidot*np.cos(thetaradf)*np.cos(phiradf) - thetadot*np.sin(phiradf)

    # So now we have the computed p,q,r from phi, theta, psi. Add these
    # to the original dataFrame. (convert to degrees first)
    
    # We also need to fix the delay caused by the filter so drop first delay points
    
    buff = np.zeros(20)             
    
    rundata.dataEU["'compP'"] = np.degrees(np.concatenate((pcomp[20:], buff)))
    rundata.dataEU["'compQ'"] = np.degrees(np.concatenate((qcomp[20:], buff)))
    rundata.dataEU["'compR'"] = np.degrees(np.concatenate((rcomp[20:], buff)))
    
    
    # ADCP Velocity Check ------
    
    # Next we want to see if the adcp w velocity is consistant with the
    # depth gage. We assume that adcp_u and adcp_v are correct
    # The process is:
    #               - Compute a trajectory using u,v,w and the p,q,r that
    #                 was verified above as correct
    #               - Compare the Z to the ZCG
    #               - To go the other way, take the X,Y and ZCG and
    #                 differentiate to get Xdot, Ydot, zdot
    #               - Rotate to body coordinate to get u,v,w
    #               - Compare to adcp_w.
    

    # We need to get the velocities from adcp,
    # These are raw adcp velocities so first do a spike filter to remove
    # adcp dropouts
    u_adcp = dt.spikeFilter(rundata.u_adcp_raw, 10)
    v_adcp = dt.spikeFilter(rundata.v_adcp_raw, 10)
    w_adcp = dt.spikeFilter(rundata.w_adcp_raw, 10)

    # Now filter to smooth bit noise steps
    u_adcpf = dt.butter_lowpass_filter(u_adcp, .01/rundata.dt, 1/rundata.dt, 2)
    v_adcpf = dt.butter_lowpass_filter(v_adcp, .01/rundata.dt, 1/rundata.dt, 2)
    w_adcpf = dt.butter_lowpass_filter(w_adcp, .01/rundata.dt, 1/rundata.dt, 2)

    # There might be a misalignment of the adcp in Pitch
    # Do this to try and correct for this before proceeding
    offset = 0.0
    adcp_pitch_offset = np.ones(len(u_adcp)) * np.radians(offset)
    adcp_roll_offset = np.zeros(len(u_adcp))
    adcp_yaw_offset = np.zeros(len(u_adcp))

    # Try a rotation on the adcp velocities to account for a physical alignment
    u_adcpr, v_adcpr, w_adcpr = dt.doTransform(u_adcpf, v_adcpf, 
                                               w_adcpf,adcp_pitch_offset,
                                               adcp_roll_offset,
                                               adcp_yaw_offset, 'toBody')

    # ADCP is not at CG so need to translate it to CG to get CG velocities
    # This translation uses the location specified in this program, not what was
    # used during the merge in the case of the STD files
    u_adcpfc  = u_adcpr - (qrad * ADCPLoc[2])
    v_adcpfc  = v_adcpr + ((prad*ADCPLoc[2])-(rrad*ADCPLoc[0]))
    w_adcpfc  = w_adcpr + ((qrad*ADCPLoc[0])-(prad*ADCPLoc[1]))

    # Do the same for the unfiltered ADCP 
    # This translation uses the location specified in this program, not what was
    # used during the merge in the case of the STD files
    u_adcpc  = u_adcp - (qrad * ADCPLoc[2])
    v_adcpc  = v_adcp + ((prad*ADCPLoc[2])-(rrad*ADCPLoc[0]))
    w_adcpc  = w_adcp + ((qrad*ADCPLoc[0])-(prad*ADCPLoc[1]))

    # We also need to get ZCG - Since this is using sensor data, need to
    # translate Zsensor to ZCG using the sensor location specified
    z_depth = rundata.depth
    
    # Skip depth filter
    #z_depthf = dt.butter_lowpass_filter(z_depth, .01/rundata.dt, 1/rundata.dt, 2)
    #z_depthf = z_depth

    zcg = z_depth + (zsensor[0] * np.sin(thetaradf) -
                                     np.cos(thetaradf)*(zsensor[1]*np.sin(phiradf)) +
                                     zsensor[2] * np.cos(phiradf))
    zcgf = dt.butter_lowpass_filter(zcg, .01/rundata.dt, 1/rundata.dt, 2)


    # Now we have correct clean adcp velocities, compute the trajectory
    # from p,q,r & u,v,w.  Use (0,0,Z0) as the initial position and
    # the initial phi,theta,psi.  From there we integrate
    # Using pcomp,qcomp,rcomp which are consistant with phi,theta, psi
    xcomp, ycomp, zcomp, phicomp, thetacomp, psicomp = dt.compTrajectory(0,0,zcgf[0],
                                                                      thetaradf[0],phiradf[0],psiradf[0],
                                                                      u_adcpfc, v_adcpfc,w_adcpfc,
                                                                      pcomp, qcomp, rcomp, rundata.dt)

    # For the second part use xcomp, ycomp and ZCG to get velocities
    # Compute xdot, ydot, zdot
    xcompdot = np.diff(xcomp)/rundata.dt
    ycompdot = np.diff(ycomp)/rundata.dt
    zcgdot = np.append(np.diff(zcgf)/rundata.dt, 0.0)

    # Transform these to body to get u,v,w
    #ucomp, vcomp, wcomp = doTransform(xcompdot, ycompdot, zcgdot, phiradf, thetaradf, psiradf, 'toBody')
    ucomp, vcomp, wcomp = dt.doTransform(xcompdot, ycompdot, zcgdot, phicomp, thetacomp, psicomp, 'toBody')
    
    # So now we have the computed u,v,w from trajectory and ZCG. Add these
    # to the original dataFrame.

    # We also need to fix the delay caused by the filter so drop first delay points
    
    buff = np.zeros(20)             

    rundata.dataEU["'compU'"] = np.concatenate((ucomp[20:], buff))
    rundata.dataEU["'compV'"] = np.concatenate((vcomp[20:], buff))
    rundata.dataEU["'compW'"] = np.concatenate((wcomp[20:], buff))
      
    # Rewrite STD file
        
    with open(stdfilename, mode='w') as file:
        file.write("'DELIMTXT'\n")
        file.write(rundata.title + "\n")
        file.write(rundata.timestamp + "\n")
        file.write(' %d, %f, %f \n' % (rundata.nchans+6, rundata.dt, rundata.length))
    
        rundata.dataEU.to_csv(file, index=False, header=True, sep=' ', float_format='%12.7e')
    

    logfile.close()
    
    return 


if __name__ == "__main__":
    # Test for merge
    os.chdir('C:\\Users\\CubbageSJ\\Documents\\Test_Data\\VIRGINIA\\VPM_Hatch-2018\\12112018')
    MergeRun('C:\\Users\\CubbageSJ\\Documents\\Test_Data\\VIRGINIA\\VPM_Hatch-2018\\12112018\\run-13657.obc',
             1657,
             'C:\\Users\\CubbageSJ\\Documents\\Test_Data\\STD_Data\\NSSN_VA',
             'C:\\Users\\CubbageSJ\\Documents\\Test_Data\\Merge_Files\\CB10\\MERGE_VPM-SDI-ConcDynos-Submerged-Column-10694_on.txt')
