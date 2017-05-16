
"""
Created on Wed Oct 12 08:05:05 2016

@author: FRM
"""

run_file = open('c:\\TDMS_Data\\SSGN\\tdms_to_obc.run', 'r').read()

typ_index_beg = run_file.find('#RUNTYPE') + 10
typ_index_end = run_file.find('#TIMERS')-1

mopt_index = run_file.find('#MOPT2') + 34

#run_file_list = list(run_file)
#
#run_file_list[mopt_index] = '3'
#
#run_file_new = "".join(run_file_list)

run_file_new = run_file[0:typ_index_beg] + 'FST Correlation' + run_file[typ_index_end:mopt_index] + str(20) + run_file[mopt_index+1:]

new_run_file = open('c:\\TDMS_Data\\SSGN\\tdms_to_obc_2.run', 'w')

new_run_file.write(run_file_new)

new_run_file.close()



