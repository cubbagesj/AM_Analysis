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
from calfile_new import CalFile
import wx
import utm
import plottools as plottools


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
    logfile.write('Created: \n' + time.ctime(os.path.getmtime(fullname)))
    logfile.write('File size: %d bytes\n' % os.path.getsize(fullname))
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


    Uprev = Vprev = Wprev = 0.0
    POSprev = 0.0
    direction = 1

    EUData = []
    # Now we start the process of converting to fullscale values
#    for i in range(len(mrg_names)):
    for i in range(1):
        if mrg_chans[i] < 800:       # Normal Channel
            EUdata[i] = runObj.getEUData(mrg_chans[i]) - runObj.avgEUzeros[mrg_chans[i]]*mrg_zero[i]
            EUdata[i] *= pow(c_lambda, mrg_scale[i])
                    
            if mrg_scale[i] >= 3:
                EUdata[i] *= 1.0284
            if mrg_scale[i] == 4:       # in-lb to ft-lb conversion
                EUdata[i] *= 0.083333

##        # At this point we have gone through all of the straight channels
##        # Now we set up some variables for values that will be used to do
##        # the calculated channels
##
##        # Pitch
##        theta = math.radians(EUdata[8])
##
##        #Roll
##        phi = math.radians(EUdata[7])
##
##        # Yaw
##        psi = math.radians(EUdata[9])
##
##        bodyAngles = [phi, theta, psi]
##
##        # Now we have the raw data split out, check for taking zeros
##        if rawdata[mode_chan] == 0x0F13:
##            for i in range(len(mrg_names)):     # zeros on normal channels
##                if mrg_chans[i] < 800:
##                    rawzero[i] += rawdata[mrg_chans[i]]
##
##            # zeros on special gauges
##            for gauge in sp_gauges.keys():
##                sp_gauges[gauge].compute(rawdata, cal.gains, bodyAngles, cb_id, doZeros = 0.0)
##                sp_gauges[gauge].addZero(rawdata)
##
##            zerosdone = 1
##            zerocnt += 1
##
##        # Watch for zeros done and compute zeros
##        elif rawdata[mode_chan] == 0x0013 and zerosdone == 1:
##            for i in range(len(mrg_names)):
##                if mrg_chans[i] < 800:
##                    rawzero[i] /= zerocnt
##                    EUzero[i] = (rawzero[i]-cal.zeros[mrg_chans[i]])*cal.gains[mrg_chans[i]]
##
##            # zeros on special gauges
##            for gauge in sp_gauges.keys():
##                sp_gauges[gauge].compZero(zerocnt)
##
##            zerosdone = 0
##
##        # Now look for actual run
##        # 11/30/07 - Change to only put the data between standby and execute in merge file
##        elif (rawdata[mode_chan] >= 0x0F23 and rawdata[mode_chan] <= 0x0F43) or rawdata[mode_chan] == 1:
##
##            # This is the actual run data - We already have the normal channels
##
##            # And now to process the 6DOF dynos
##            for gauge in sp_gauges.keys():
##                sp_gauges[gauge].compute(rawdata, cal.gains, bodyAngles, cb_id)
##
##            # Now loop for the special channels
##            # All Channels above 800 are computed channels for special gauges
##            
##            for i in range(len(mrg_names)):
##                if mrg_chans[i] == 800:            # Empty channel
##                    EUdata[i] = 0
##                elif mrg_chans[i] == 801:          # Time Channel 
##                    EUdata[i] = c_FSdt * step
##                elif mrg_chans[i] == 802:          # ZCG
##                    EUdata[i] = (EUdata[zsensor[3]] + zsensor[0] * math.sin(theta) -
##                                 math.cos(theta)*(zsensor[1]*math.sin(phi) + zsensor[2] * math.cos(phi)))
##                elif mrg_chans[i] == 820:           # Status
##                    if rawdata[mode_chan] == 0x0F33:
##                        EUdata[i] = 2
##                    elif rawdata[mode_chan] == 0x0F43:
##                        EUdata[i] = 5;
##                    else:
##                        EUdata[i] = 0
##                elif mrg_chans[i] == 804:           #Filtered and Corr. ADCP u
##
##                # first filter the dropouts where there is no velocity
##                    if abs(EUdata[u_chan]) > 70:
##                        EUdata[i] = Uprev
##                        EUdata[u_chan] = 0.0
##                    else:
##                        EUdata[i] = EUdata[u_chan]
##                    Uprev = EUdata[i]
##                    EUdata[i] -= ((EUdata[4]/57.296)*ADCPLoc[2])
##                    
##                elif mrg_chans[i] == 805:           #Filtered and Corr ADCP v
##                    if abs(EUdata[v_chan]) > 15:
##                        EUdata[i] = Vprev
##                        EUdata[v_chan] = 0.0
##                    else:
##                        EUdata[i] = EUdata[v_chan]
##                    Vprev = EUdata[i]
##                    EUdata[i] += (((EUdata[3]/57.296)*ADCPLoc[2])-((EUdata[5]/57.296)*ADCPLoc[0]))
##                    
##                elif mrg_chans[i] == 806:           #Filtered and Corr ADCP w
##                    if abs(EUdata[w_chan]) > 15:
##                        EUdata[i] = Wprev
##                        EUdata[w_chan] = 0.0
##                    else:
##                        EUdata[i] = EUdata[w_chan]
##                    Wprev = EUdata[i]
##                    EUdata[i] += (((EUdata[4]/57.296)*ADCPLoc[0])-((EUdata[3]/57.296)*ADCPLoc[1]))
##
##                elif mrg_chans[i] == 807 and 'Rotor' in sp_gauges:         # Computed Rotor Fx
##                    EUdata[i] = sp_gauges['Rotor'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 808 and 'Rotor' in sp_gauges:         # Computed Rotor Fy
##                    EUdata[i] = sp_gauges['Rotor'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 809 and 'Rotor' in sp_gauges:         # Computed Rotor Fz
##                    EUdata[i] = sp_gauges['Rotor'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 810 and 'Rotor' in sp_gauges:         # Computed Rotor Mx
##                    EUdata[i] = sp_gauges['Rotor'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 811 and 'Rotor' in sp_gauges:         # Computed Rotor My
##                    EUdata[i] = sp_gauges['Rotor'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 812 and 'Rotor' in sp_gauges:         # Computed Rotor Mz
##                    EUdata[i] = sp_gauges['Rotor'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 813 and 'Stator' in sp_gauges:         # Computed Stator Fx
##                    EUdata[i] = sp_gauges['Stator'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 814 and 'Stator' in sp_gauges:         # Computed Stator Fy
##                    EUdata[i] = sp_gauges['Stator'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 815 and 'Stator' in sp_gauges:         # Computed Stator Fz
##                    EUdata[i] = sp_gauges['Stator'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 816 and 'Stator' in sp_gauges:         # Computed Stator Mx
##                    EUdata[i] = sp_gauges['Stator'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 817 and 'Stator' in sp_gauges:         # Computed Stator My
##                    EUdata[i] = sp_gauges['Stator'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 818 and 'Stator' in sp_gauges:         # Computed Stator Mz
##                    EUdata[i] = sp_gauges['Stator'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 821:           # Alpha
##                    EUdata[i] = math.degrees(math.atan2(EUdata[2],EUdata[0]))
##                elif mrg_chans[i] == 822:           # Beta
##                    try:
##                        EUdata[i] = -math.degrees(math.asin(EUdata[1]/EUdata[big_u_chan]))
##                    except:
##                        EUdata[i] = 0
##                elif mrg_chans[i] == 823:           # Big U from ADCP
##                    EUdata[i] = math.sqrt(EUdata[0]**2 + EUdata[1]**2 + EUdata[2]**2)
##
##                elif mrg_chans[i] == 824:           # Big U from ADCP in knots
##                    EUdata[i] = math.sqrt(EUdata[0]**2 + EUdata[1]**2 + EUdata[2]**2)
##                    EUdata[i] /= 1.6878
##
##                elif mrg_chans[i] == 825:    # RPM flip from obs_rpm and rpm cmd
##                # Update this since CB 12 only has pos RPM
##                    EUdata[i] = EUdata[27]
###                    if rawdata[217] < 0:
###                        if rawdata[217] < 0:
##                    if abs(rawdata[183] - POSprev) < 300:
##                        if (rawdata[183] - POSprev) < 0:
##                            direction = -1
##                        else:
##                            direction = 1
##                    EUdata[i] *= direction
##                    POSprev = rawdata[183]
##
##                elif mrg_chans[i] == 830 and 'SOF1' in sp_gauges:         # Computed SOF1 Fx
##                    EUdata[i] = sp_gauges['SOF1'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 831 and 'SOF1' in sp_gauges:         # Computed SOF1 Fy
##                    EUdata[i] = sp_gauges['SOF1'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 832 and 'SOF1' in sp_gauges:         # Computed SOF1 Fz
##                    EUdata[i] = sp_gauges['SOF1'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 833 and 'SOF1' in sp_gauges:         # Computed SOF1 Mx
##                    EUdata[i] = sp_gauges['SOF1'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 834 and 'SOF1' in sp_gauges:         # Computed SOF1 My
##                    EUdata[i] = sp_gauges['SOF1'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 835 and 'SOF1' in sp_gauges:         # Computed SOF1 Mz
##                    EUdata[i] = sp_gauges['SOF1'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 840 and 'SOF2' in sp_gauges:         # Computed SOF2 Fx
##                    EUdata[i] = sp_gauges['SOF2'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 841 and 'SOF2' in sp_gauges:         # Computed SOF2 Fy
##                    EUdata[i] = sp_gauges['SOF2'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 842 and 'SOF2' in sp_gauges:         # Computed SOF2 Fz
##                    EUdata[i] = sp_gauges['SOF2'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 843 and 'SOF2' in sp_gauges:         # Computed SOF2 Mx
##                    EUdata[i] = sp_gauges['SOF2'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 844 and 'SOF2' in sp_gauges:         # Computed SOF2 My
##                    EUdata[i] = sp_gauges['SOF2'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 845 and 'SOF2' in sp_gauges:         # Computed SOF2 Mz
##                    EUdata[i] = sp_gauges['SOF2'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 850 and 'Kistler' in sp_gauges:         # Computed Kistler Fx
##                    EUdata[i] = sp_gauges['Kistler'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 851 and 'Kistler' in sp_gauges:         # Computed Kistler Fy
##                    EUdata[i] = sp_gauges['Kistler'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 852 and 'Kistler' in sp_gauges:         # Computed Kistler Fz
##                    EUdata[i] = sp_gauges['Kistler'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 853 and 'Kistler' in sp_gauges:         # Computed Kistler Mx
##                    EUdata[i] = sp_gauges['Kistler'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 854 and 'Kistler' in sp_gauges:         # Computed Kistler My
##                    EUdata[i] = sp_gauges['Kistler'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 855 and 'Kistler' in sp_gauges:         # Computed Kistler Mz
##                    EUdata[i] = sp_gauges['Kistler'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 860 and '6DOF1' in sp_gauges:         # Computed 6DOF1 Fx
##                    EUdata[i] = sp_gauges['6DOF1'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 861 and '6DOF1' in sp_gauges:         # Computed 6DOF1 Fy
##                    EUdata[i] = sp_gauges['6DOF1'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 862 and '6DOF1' in sp_gauges:         # Computed 6DOF1 Fz
##                    EUdata[i] = sp_gauges['6DOF1'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 863 and '6DOF1' in sp_gauges:         # Computed 6DOF1 Mx
##                    EUdata[i] = sp_gauges['6DOF1'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 864 and '6DOF1' in sp_gauges:         # Computed 6DOF1 My
##                    EUdata[i] = sp_gauges['6DOF1'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 865 and '6DOF1' in sp_gauges:         # Computed 6DOF1 Mz
##                    EUdata[i] = sp_gauges['6DOF1'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 870 and '6DOF2' in sp_gauges:         # Computed 6DOF2 Fx
##                    EUdata[i] = sp_gauges['6DOF2'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 871 and '6DOF2' in sp_gauges:         # Computed 6DOF2 Fy
##                    EUdata[i] = sp_gauges['6DOF2'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 872 and '6DOF2' in sp_gauges:         # Computed 6DOF2 Fz
##                    EUdata[i] = sp_gauges['6DOF2'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 873 and '6DOF2' in sp_gauges:         # Computed 6DOF2 Mx
##                    EUdata[i] = sp_gauges['6DOF2'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 874 and '6DOF2' in sp_gauges:         # Computed 6DOF2 My
##                    EUdata[i] = sp_gauges['6DOF2'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 875 and '6DOF2' in sp_gauges:         # Computed 6DOF2 Mz
##                    EUdata[i] = sp_gauges['6DOF2'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 880:                                   #Equiv Stern
##                    EUdata[i] = (EUdata[32]+EUdata[33]+EUdata[34]+EUdata[35])/4.0
##                elif mrg_chans[i] == 881:                                   #Equiv Rudder
##                    EUdata[i] = (-EUdata[32]+EUdata[33]-EUdata[34]+EUdata[35])/4.0
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
##                elif mrg_chans[i] == 890 and '6DOF3' in sp_gauges:         # Computed 6DOF3 Fx
##                    EUdata[i] = sp_gauges['6DOF3'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 891 and '6DOF3' in sp_gauges:         # Computed 6DOF3 Fy
##                    EUdata[i] = sp_gauges['6DOF3'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 892 and '6DOF3' in sp_gauges:         # Computed 6DOF3 Fz
##                    EUdata[i] = sp_gauges['6DOF3'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 893 and '6DOF3' in sp_gauges:         # Computed 6DOF3 Mx
##                    EUdata[i] = sp_gauges['6DOF3'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 894 and '6DOF3' in sp_gauges:         # Computed 6DOF3 My
##                    EUdata[i] = sp_gauges['6DOF3'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 895 and '6DOF3' in sp_gauges:         # Computed 6DOF3 Mz
##                    EUdata[i] = sp_gauges['6DOF3'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 900 and '6DOF4' in sp_gauges:         # Computed 6DOF4 Fx
##                    EUdata[i] = sp_gauges['6DOF4'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 901 and '6DOF4' in sp_gauges:         # Computed 6DOF4 Fy
##                    EUdata[i] = sp_gauges['6DOF4'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 902 and '6DOF4' in sp_gauges:         # Computed 6DOF4 Fz
##                    EUdata[i] = sp_gauges['6DOF4'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 903 and '6DOF4' in sp_gauges:         # Computed 6DOF4 Mx
##                    EUdata[i] = sp_gauges['6DOF4'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 904 and '6DOF4' in sp_gauges:         # Computed 6DOF4 My
##                    EUdata[i] = sp_gauges['6DOF4'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 905 and '6DOF4' in sp_gauges:         # Computed 6DOF4 Mz
##                    EUdata[i] = sp_gauges['6DOF4'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 910 and '6DOF5' in sp_gauges:         # Computed 6DOF5 Fx
##                    EUdata[i] = sp_gauges['6DOF5'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 911 and '6DOF5' in sp_gauges:         # Computed 6DOF5 Fy
##                    EUdata[i] = sp_gauges['6DOF5'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 912 and '6DOF5' in sp_gauges:         # Computed 6DOF5 Fz
##                    EUdata[i] = sp_gauges['6DOF5'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 913 and '6DOF5' in sp_gauges:         # Computed 6DOF5 Mx
##                    EUdata[i] = sp_gauges['6DOF5'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 914 and '6DOF5' in sp_gauges:         # Computed 6DOF5 My
##                    EUdata[i] = sp_gauges['6DOF5'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 915 and '6DOF5' in sp_gauges:         # Computed 6DOF5 Mz
##                    EUdata[i] = sp_gauges['6DOF5'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 920 and '6DOF6' in sp_gauges:         # Computed 6DOF6 Fx
##                    EUdata[i] = sp_gauges['6DOF6'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 921 and '6DOF6' in sp_gauges:         # Computed 6DOF6 Fy
##                    EUdata[i] = sp_gauges['6DOF6'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 922 and '6DOF6' in sp_gauges:         # Computed 6DOF6 Fz
##                    EUdata[i] = sp_gauges['6DOF6'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 923 and '6DOF6' in sp_gauges:         # Computed 6DOF6 Mx
##                    EUdata[i] = sp_gauges['6DOF6'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 924 and '6DOF6' in sp_gauges:         # Computed 6DOF6 My
##                    EUdata[i] = sp_gauges['6DOF6'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 925 and '6DOF6' in sp_gauges:         # Computed 6DOF6 Mz
##                    EUdata[i] = sp_gauges['6DOF6'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 930 and 'Deck' in sp_gauges:         # Combined Deck Fx
##                    EUdata[i] = sp_gauges['Deck'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 931 and 'Deck' in sp_gauges:         # Combined Deck Fy
##                    EUdata[i] = sp_gauges['Deck'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 932 and 'Deck' in sp_gauges:         # Combined Deck Fz
##                    EUdata[i] = sp_gauges['Deck'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 933 and 'Deck' in sp_gauges:         # Combined Deck Mx
##                    EUdata[i] = sp_gauges['Deck'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 934 and 'Deck' in sp_gauges:         # Combined Deck My
##                    EUdata[i] = sp_gauges['Deck'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 935 and 'Deck' in sp_gauges:         # Combined Deck Mz
##                    EUdata[i] = sp_gauges['Deck'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 940 and 'Deck' in sp_gauges:         # Fwd Deck Fx - No wt corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesa[0]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 941 and 'Deck' in sp_gauges:         # Fwd Deck Fy - No wt corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesa[1]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 942 and 'Deck' in sp_gauges:         # Fwd Deck Fz - No wt Corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesa[2]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 943 and 'Deck' in sp_gauges:         # Fwd Deck Mx - No wt Corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesa[3]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 944 and 'Deck' in sp_gauges:         # Fwd Deck My - No wt Corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesa[4]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 945 and 'Deck' in sp_gauges:         # Fwd Deck Mz - No wt Corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesa[5]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##                elif mrg_chans[i] == 950 and 'Deck' in sp_gauges:         # Aft Deck Fx - No wt corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesf[0]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 951 and 'Deck' in sp_gauges:         # Aft Deck Fy - No wt corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesf[1]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 952 and 'Deck' in sp_gauges:         # Aft Deck Fz - No wt Corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesf[2]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 953 and 'Deck' in sp_gauges:         # Aft Deck Mx - No wt Corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesf[3]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 954 and 'Deck' in sp_gauges:         # Aft Deck My - No wt Corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesf[4]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 955 and 'Deck' in sp_gauges:         # Aft Deck Mz - No wt Corr
##                    EUdata[i] = sp_gauges['Deck'].compForcesf[5]
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
## 
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
##                elif mrg_chans[i] == 970 and 'Kistler3' in sp_gauges:         # Computed Kistler Fx
##                    EUdata[i] = sp_gauges['Kistler3'].CFx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 971 and 'Kistler3' in sp_gauges:         # Computed Kistler Fy
##                    EUdata[i] = sp_gauges['Kistler3'].CFy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 972 and 'Kistler3' in sp_gauges:         # Computed Kistler Fz
##                    EUdata[i] = sp_gauges['Kistler3'].CFz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                elif mrg_chans[i] == 973 and 'Kistler3' in sp_gauges:         # Computed Kistler Mx
##                    EUdata[i] = sp_gauges['Kistler3'].CMx
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 974 and 'Kistler3' in sp_gauges:         # Computed Kistler My
##                    EUdata[i] = sp_gauges['Kistler3'].CMy
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##                elif mrg_chans[i] == 975 and 'Kistler3' in sp_gauges:         # Computed Kistler Mz
##                    EUdata[i] = sp_gauges['Kistler3'].CMz
##                    EUdata[i] *= pow(c_lambda, mrg_scale[i])
##                    EUdata[i] *= 1.0284
##                    EUdata[i] *= .083333
##
##
##            if (step % c_skip) == 0:         # Output only the records we want
##                for data in EUdata:
##                    stdfile.write(" %12.7e " % data)
##                stdfile.write('\n')
##

##    #obcfile.close()    
##    stdfile.close()

    logfile.close()

    # The following code is used to offset and rotate the x,y, positions so that
    # the position at execute is (0,0) and the initial track is along the x-axis
    # To do this we need to re-read the file to get the stats and then rewrite the 
    # new data back out.

    # At this point in the code the name of the std file is in stdfilename.  Us this 
    # in a call to the OBCFile class to read in the file and get the stats

    # Wrap it in a try clause in case we get an error
##    try:
##        stdrun = STDFile(stdfilename, 'known')
##        
##        stdrunxpos = stdrun.getEUData(20)
##        stdrunypos = stdrun.getEUData(21)
##        
##        t1 = stdrunypos[stdrun.execrec]
##        t2 = stdrunypos[stdrun.execrec-50]
##        t3 = stdrunxpos[stdrun.execrec]
##        t4 = stdrunxpos[stdrun.execrec-50]
##        if t3 - t4 != 0:
##            test = (stdrunypos[stdrun.execrec]-stdrunypos[stdrun.execrec-50])/(stdrunxpos[stdrun.execrec] - stdrunxpos[stdrun.execrec-50])
##            stdruntrack = math.arctan(test)
##        else:
##            stdruntrack = 0
##       
##        if stdruntrack <=0:
##            stdruntrack = stdruntrack + 2*math.pi
##        else:
##            stdruntrack = stdruntrack + math.pi
##    
##        stdrunxposzero = stdrunxpos[stdrun.execrec]*math.cos(stdruntrack) + stdrunypos[stdrun.execrec]*math.sin(stdruntrack)
##        stdrunyposzero = -stdrunxpos[stdrun.execrec]*math.sin(stdruntrack) + stdrunypos[stdrun.execrec]*math.cos(stdruntrack)
##        
##        # Got needed info, now process
##    
##        stdfile = open(stdfilename, 'r')
##        newfile = open(stdfilename+'new','w')
##    
##        new_x = 0.0
##        new_y = 0.0
##    
##        for x in range(5):
##            newfile.write(stdfile.readline())
##    
##        for line in stdfile:
##            line = line.rstrip()
##            data = []
##    
##            for channel in line.split():
##                data.append(float(channel))
##    
##            rot_x = data[20]*math.cos(stdruntrack) + data[21]*math.sin(stdruntrack)
##            rot_y = -data[20]*math.sin(stdruntrack) + data[21]*math.cos(stdruntrack)
##    
##            data[20] = rot_x - stdrunxposzero
##            data[21] = rot_y - stdrunyposzero
##    
##            for channel in data:
##                newfile.write(" %12.7e " % channel)
##            newfile.write('\n')
##        stdfile.close()
##        newfile.close()
##        os.remove(stdfilename)
##        os.rename(stdfilename+'new', stdfilename)
##    except:
##        pass

    return


if __name__ == "__main__":
    # Test for merge
    pass
