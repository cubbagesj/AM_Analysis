#Program to convert tdms files to obc files for merge capability 

#2016/02/18  Woody Pfitsch NSWCCD Code 8633

from nptdms import TdmsFile  #package for importing tdms file data into python using numpy arrays
import math as m
import os.path, time
import numpy as np
import ConfigParser
from scipy.interpolate import interp1d
import wx
import os
from shutil import copyfile

# Function Definitions
def write_cal_section(cal, chan_num, name, gain, zero, pkt_loc, rawu, eu, cal_date):
    '''
    Writes a single section of the cal config.
    Inputs:
        cal - ConfigParse configuration object
        chan_num - integer channel number for the section name of the cal config
        name - string channel name
        gain - float cal gain
        zero - float cal zero
        pkt_loc - integer data packet location
        rawu - string raw units
        eu - string engineering units
        cal_date - string calibration date
    Returns:
        None
    '''
    section = 'CHAN' + str(chan_num)
    cal.add_section(section)
    cal.set(section, 'sys_name', name)
    cal.set(section, 'alt_name', name)
    cal.set(section, 'gain', str(gain))
    cal.set(section, 'zero', str(zero))
    cal.set(section, 'data_pkt_loc', str(pkt_loc))
    cal.set(section, 'raw_units', rawu)
    cal.set(section, 'eng_units', eu)
    cal.set(section, 'cal_date', cal_date)

def tdmsToOBC(tdmsfile, obcDirectory):
    '''
    function to create OBC files and all complimentary files (.cal, .gps, .run, and MERGE.INP)
    needed to run a merge to full scale data from tdms data files
    '''
    # Initialize variables that will be needed throughout the code
    cal_date = '02/26/2016'
    
    if os.path.isfile(tdmsfile):
        tdmsfile_name = tdmsfile
    else:
        #simple GUI to prompt user to browse for a tdms file
        app = wx.PySimpleApp()
        wildcard = "All files (*.*)|*.*"
        dialog = wx.FileDialog(None, "Choose a TDMS file to convert to OBC", os.getcwd(), "", wildcard, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            tdmsfile_name = dialog.GetPath()  #tdms file containing the run data
        dialog.Destroy()
    
    if not os.path.exists(obcDirectory):
        obcDirectory = 'C:\\OBC_Data'
    
    tdmsDir, tdmsf = os.path.split(tdmsfile_name)
    
    if os.path.isfile(os.path.join(tdmsDir,'tdms_to_obc.txt')):
        configfile_name = os.path.join(tdmsDir, 'tdms_to_obc.txt')
    else:
        #simple GUI to prompt user to browse for config file
        app2 = wx.PySimpleApp()
        wildcard2 = "All files (*.*)|*.*"
        dialog2 = wx.FileDialog(None, "Choose a CSV file that maps TDMS channel names to OBC column numbers", os.getcwd(), "", wildcard2, wx.OPEN)
        if dialog2.ShowModal() == wx.ID_OK:
            configfile_name = dialog2.GetPath()  #comma delimited setup file containing a column of tdms channel names and a column of thier respective obc column numbers
        dialog2.Destroy()
    

    head, tail = os.path.split(tdmsfile_name)
    run_name, ext = os.path.splitext(tail)
    dummy,run_num = run_name.split('_')
    run_num = run_num.strip()
    
    # Write obc and cal file to same directory as tdms file
    obcfile_name = head + '/run-' + run_num + '.obc' #file name for new obc file
    calfile_name = head + '/run-' + run_num + '.cal' #file name for new cal file
    
    # Write obc and cal file to the obc directory
    #obcfile_name = obcDirectory + '/run-' + run_num + '.obc' #file name for new obc file
    #calfile_name = obcDirectory + '/run-' + run_num + '.cal' #file name for new cal file
    
    # Open files that will be needed
    tdms_file_obj = TdmsFile(tdmsfile_name)  #open the tdms file using nptdms package
    configfile_data = open(configfile_name)  #open the config file
    #channel = tdms_file_obj.object('DATA', 'phins_roll')
    #data = channel.data
    leng = 0
    for i in configfile_data:
        leng +=1
    
    prgbar = wx.ProgressDialog("Conversion Progress",
                               tdmsfile_name, leng + 363,
                               style=wx.PD_ELAPSED_TIME|
                               wx.PD_AUTO_HIDE|
                               wx.PD_REMAINING_TIME)
    
    # Define dictionaries that will hold the important data from the tdms file
    obc_data = {}  #dictionary that will contain the data from the tdms file with the key being the obc column to put it into
    cals = {}  #dictionary that will contain the cal functions for each of the channels needed
    chan_name = {} #dictionary that will contain the channel names from the tdms file
    eng_units = {} #dictionary to contain the engineering units of each channel
    cal_gain = {} #dictionary to contain the channel cal gains
    cal_zero = {} #dictionary to contain the channel cal zeros
    
    configfile_data.seek(0)
    #Main body of Code
    progress = 0
    #Go through the setup file to get all the channels and get the data and properities from the tdms file
    for line in configfile_data:
        obc_col = int(line.split(',')[1].rstrip())
        chan_name[obc_col] = line.split(',')[0] #get the channel name from the config file
        scale = float(line.split(',')[2])
        offset = float(line.split(',')[3])
        tdms_chan_obj = tdms_file_obj.object('DATA', chan_name[obc_col])  #unpack the tdms channel object from the tdms file object
        try:
            eng_units[obc_col] = tdms_chan_obj.properties['eng_units']
        except:
            eng_units[obc_col] = 'NA'
        try:
            scaletype = str(tdms_chan_obj.properties['NI_Scale[0]_Scale_Type'])
            #Linear calibration scaling,  set cal gain and zero and read raw obc data
            if scaletype == 'Linear': 
                cal_gain[obc_col] = scale * tdms_chan_obj.properties[u'NI_Scale[0]_Linear_Slope'] #get cal gains for cal file
                cal_zero[obc_col] = offset - (tdms_chan_obj.properties[u'NI_Scale[0]_Linear_Y_Intercept']/tdms_chan_obj.properties[u'NI_Scale[0]_Linear_Slope'])  #get cal zeros for cal file
                obc_data[obc_col] = tdms_chan_obj.data  #get tdms raw data for obc file
            #Linear interpolation scaling between point in Table, define a scipy interpolation function and scale the data, set cal gain = 1 and zero = 0 
            elif scaletype == 'Table':
                #import scaled values from the tdms file properties
                scaled = []
                i = 0
                while True:
                    try:
                        scaled.append(tdms_chan_obj.properties['NI_Scale[0]_Table_Scaled_Values[' + str(i) + ']'])
                    except:
                        break
                    else:
                        i += 1
                #import pre-scaled values from the tmds file properties
                prescaled = []
                i = 0
                while True:
                    try:
                        prescaled.append(tdms_chan_obj.properties['NI_Scale[0]_Table_Pre_Scaled_Values[' + str(i) + ']'])
                    except:
                        break
                    else:
                        i += 1
                scalingFn = interp1d(prescaled, scaled, bounds_error=False)
                cal_gain[obc_col] = scale #Set the gain to 1.0 for the cal file
                cal_zero[obc_col] = offset  #Set the zero to 0.0 for the cal file
                obc_data[obc_col] = scalingFn(tdms_chan_obj.data)  #get tdms raw data for obc file and scale it using the scaling function
            #No scaling is applied if no valid scaling type is found
            else: 
                cal_gain[obc_col] = scale #set the gain to the scaling factor from the config file for the cal file
                cal_zero[obc_col] = offset #set the zero to the offset from the config file for the cal file
                obc_data[obc_col] = tdms_chan_obj.data  #get tdms raw data for obc file
        except:
            raise
            cal_gain[obc_col] = scale #set the gain to 1.0 for the cal file
            cal_zero[obc_col] = offset #set the zero to 0.0 for the cal file
            obc_data[obc_col] = tdms_chan_obj.data  #get tdms raw data for obc file 
        progress += 1
        prgbar.Update(progress)   
                    
    data_length = len(obc_data[obc_data.keys()[0]]) #the length of the data arrays
    
    cal = ConfigParser.SafeConfigParser()  #configuration instance for the cal ini file
    
    #If 0 is one of the columns in the obc_data dictionary use that as the column 0 of the obc file array
    if 0 in obc_data.keys():
        obc_array = obc_data[0]
        write_cal_section(cal, 0, chan_name[0], cal_gain[0], cal_zero[0], 0, 'ad_cnts', eng_units[0], cal_date)
    #otherwise use a zero array of the correct data length
    else:
        obc_array = np.zeros(data_length, dtype=float)
        write_cal_section(cal, 0, 'name', 1.0, 0.0, 0, 'ad_cnts', 'NA', cal_date)
    
    #Now add the rest of the obc file columns, tdms data if in config file, zeros if not         
    for i in range(1, 364):
        if i in obc_data.keys():
            obc_array = np.column_stack((obc_array, obc_data[i]))
            write_cal_section(cal, i, chan_name[i], cal_gain[i], cal_zero[i], 0, 'ad_cnts', eng_units[i], cal_date)
        else:
            obc_array = np.column_stack((obc_array, np.zeros(data_length, dtype=float)))
            write_cal_section(cal, i, 'name', 1.0, 0.0, 0, 'ad_cnts', 'NA', cal_date)
        progress += 1
        prgbar.Update(progress)
            
    # Write the obc data to the new obc file
    np.savetxt(obcfile_name, obc_array, fmt = '%10.9f', delimiter=' ')
    
    # open the new cal file for writing
    calfile = open(calfile_name, 'w')
    
    # get the cal file header and footer formats from files in the same directory as the config file
    confhead, conftail = os.path.split(configfile_name)
    cal_head_file = open(confhead + '/tdms_to_obc_calheader.txt', 'r')
    cal_foot_file = open(confhead + '/tdms_to_obc_calfooter.txt', 'r')
    
    #Create new run file with the correct #RUNTYPE and #MOPT2 settings for tdms runtype
    run_file = open(confhead + '/tdms_to_obc.run', 'r').read()
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
                'Rudder Perturbation',
                'No Run Type']
     
    run_type = tdms_file_obj.object().property('script_run_type') #get runtype from tdms file object          
    try:
        type_number = mantypes.index(run_type)  #find the correct runtype number to put in the .run file #MOPT2 settings
    except:
        type_number = 26
    
    #insert the runtype string and #MOPT2 number into the run file text
    type_index_beg = run_file.find('#RUNTYPE') + 10
    type_index_end = run_file.find('#TIMERS')-1
    mopt_index = run_file.find('#MOPT2') + 34
    run_file_new = run_file[0:type_index_beg] + run_type + run_file[type_index_end:mopt_index] + str(type_number) + run_file[mopt_index+1:]
    
    #write the new run file with the new text
    runfile_name = head + '/run-' + run_num + '.run' #file name for new .run file
    newrunfile = open(runfile_name, 'w')
    newrunfile.write(run_file_new)
    newrunfile.close()
    
    #create new .gps and MERGE.INP files in the OBC data directory 
    gpsfile_name = head + '/run-' + run_num + '.gps' #file name for new gps file
    INPfile_name = head + '/run-' + run_num + '_MERGE.INP' #file name for new MERGE.INP file
    copyfile(confhead + '/tdms_to_obc.gps', gpsfile_name)
    copyfile(confhead + '/tdms_to_obc_MERGE.INP', INPfile_name)
    
    cal_head = cal_head_file.read()
    cal_foot = cal_foot_file.read()
    
    # close the header and footer files
    cal_head_file.close()
    cal_foot_file.close()
    
    # Write the header, cal config, and footer to the cal file
    calfile.write(cal_head)
    cal.write(calfile)
    calfile.write(cal_foot)
    
    # Will eventually insert code here to read back in the cal config and set the sections and keys in the header
    # and footer to match custom properties in the tdms file (for interaction matrices and other settings)
    
    # Close the cal file
    calfile.close()
    prgbar.Update(leng+363)
    prgbar.Destroy()
    return




        
