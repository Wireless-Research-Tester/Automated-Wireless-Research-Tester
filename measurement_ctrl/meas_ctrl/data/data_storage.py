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
