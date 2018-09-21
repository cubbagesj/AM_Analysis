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

def MergeRun(fullname, runnumber, std_dir, merge_file='MERGE.INP'):  

    # LOG File - Open up a file to write diagnostic info to
    #
    print(std_dir+"\n")
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
    try:
        lines = open('run-'+str(runnumber)+'.run').read().splitlines()
    except:
        logfile.write(' Could not open run-'+str(runnumber)+'.run file!')
        sys.exit(1)

    logfile.write('Reading the .run file ........')

    # Start with a dummy title - This is how I used to do it for old AM runs
    for line in lines:
        if line.find('#RUNTYPE:') != -1:
            runtype = line[line.find('#RUNTYPE:')+9:]
            break
        else:
            runtype = 'Run Type Not Defined'
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
        runtype = 'Run Type Not Defined'

    logfile.write('Done')

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
    stdfile.write(" 'AM:run-%d:%3.1f:%d:  %s '\n" % (runnumber, apprU, runkind, runtype))
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
    Uprev = Vprev = Wprev

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
                      runObj.getEUdata(mrg_chans[34]) +
                      runObj.getEUdata(mrg_chans[35])) / 4.0
        elif mrg_chans[i] == 881:                                   #Equiv Rudder
            EUdata = (-runObj.getEUdata(mrg_chans[32]) +
                      runObj.getEUdata(mrg_chans[33]) -
                      runObj.getEUdata(mrg_chans[34]) +
                      runObj.getEUdata(mrg_chans[35]))/4.0

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
    logfile.close()

    # The following code is used to offset and rotate the x,y, positions so that
    # the position at execute is (0,0) and the initial track is along the x-axis
    # To do this we need to re-read the file to get the stats and then rewrite the 
    # new data back out.

    # At this point in the code the name of the std file is in stdfilename.  Us this 
    # in a call to the OBCFile class to read in the file and get the stats

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
        pass

    return 


if __name__ == "__main__":
    # Test for merge
    os.chdir('f:\\Analysis\\VPM_DDS_082018\\20180912')
    MergeRun('F:\\Analysis\\VPM_DDS_082018\\20180912\\run-13020.obc',
             13020,
             'F:\\Analysis',
             'F:\\Analysis\\MERGE_VPM-BLKV-DDSHatch.txt')
