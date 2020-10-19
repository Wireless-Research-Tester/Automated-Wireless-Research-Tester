################################################################################
#  data_storage
#
#  Description: Contains functions used to store the data collected from the
#               positioner and VNA into a csv file.
#  Dependencies: None
#
#  Author(s): Eric Li
#  Date: 2020/10/17
#  Built with Python Version: 3.8.5
################################################################################

def append_data(filename, data):
    file = open(filename, 'a')
    for i in range(0, len(data)):
        file.write('%s,%d,%f,%f,%f,%f\n' % (
            data[i].measurement_type, 
            data[i].freq, 
            data[i].theta, 
            data[i].phi, 
            data[i].value_mag, 
            data[i].value_phase))
    file.close()


def create_file(filename):
    file = open(filename, 'w')
    file.write('measurement_type,freq,theta,phi,magnitude,phase,\n')
    file.close()
