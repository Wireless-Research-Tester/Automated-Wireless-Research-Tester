import vna.vna_comms as comms
import time

sess = comms.session('GPIB0::16::INSTR')
sess.reset_all()
sess.setup(comms.lin_freq(5, 6000, 401), 8, 3700)
# sess.calibrate()
input('wait for it...')
start = time.time()
temp = sess.get_data(180, 45, 'S11')
print('get_data execution time: {} seconds\n'.format(time.time()-start))
for i in range(0, len(temp)):
    print("Measurement Type: {}, Frequency: {} MHz, Magnitude: {} dB, Phase: {} degrees".format(temp[i].measurement_type
                                                                                                , temp[i].freq,
                                                                                                temp[i].value_mag,
                                                                                                temp[i].value_phase))
