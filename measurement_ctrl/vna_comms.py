################################################################################
# vna_comms
# Description: 
#   Powered by PyVISA, vna_comms contains methods to perform the
#   actions needed to take measurements from a vector network
#   analyzer. These methods include: setting up the VNA, collecting
#   data from the VNA, and calibrating the VNA.
#
#  Dependencies:    
#   PyVISA   Version: 10.0.1
#   NI-488.2 Version: 19.5
#   NI-VISA  Version: 19.5
#
#  Author(s): Eric Li
#  Date: 2020/09/30
#  Built with Python Version: 3.8.5
#  For any questions, contact Eric at eric.li.1999@gmail.com
################################################################################
import pyvisa as visa
import math
from struct import unpack
from measurement_ctrl.vna_syntaxes import *


class Data:
    def __init__(self, measurement_type, freq, theta, phi, value_mag, value_phase):
        self.measurement_type = measurement_type
        self.freq = freq
        self.theta = theta
        self.phi = phi
        self.value_mag = value_mag
        self.value_phase = value_phase


class LinFreq:
    """Class to describe the information needed for a linear frequency sweep"""
    def __init__(self, start, end, points):
        self.start = start
        self.end = end
        self.points = points


class Session:
    def __init__(self, resource):
        self.rm = visa.ResourceManager()
        self.vna = self.rm.open_resource(resource)
        self.vna.read_termination = '\n'
        del self.vna.timeout
        self.model = check_model(self.vna.query('*IDN?'))
        self.vna.write(form2(self.model))
        self.freq = None
        self.using_correction = False

    def reset_all(self):
        """Resets the entire machine to factory presets"""
        self.vna.write(reset(self.model))
        self.using_correction = False
        return 0

    def reset(self):
        """Resets ONLY measurement parameters changed in setup, nothing else"""
        self.vna.write(edit_list(self.model))
        self.vna.write(clear_list(self.model))

    def setup(self, freq, avg, bw):
        self.freq = freq

        # Setup procedure for a list frequency sweep:
        # 1. Adding each frequency as a separate segment on the VNA
        # 2. Changing frequency sweep mode to a list sweep
        if isinstance(self.freq, list):
            # if sweep type is frequency list, only take a max of 30 frequencies
            if len(self.freq) > 30:
                raise Exception('The number of frequencies in the frequency list exceeded 30.')
            for i in range(0, len(self.freq)):
                freq_temp = self.freq[i]
                self.vna.write(edit_list(self.model))
                self.vna.write(add_list_freq(self.model, int(freq_temp * 1000)))
            self.vna.write(list_freq_mode(self.model))

        # Setup procedure for a linear frequency sweep
        # 1. Indicate start frequency (in kHz b/c pyvisa does not deal well with decimals, for reasons unknown)
        # 2. Indicate stop frequency
        # 3. Indicate number of points
        # 4. Changing frequency sweep mode to a linear sweep
        else:
            self.vna.write(lin_freq_start(self.model, int(self.freq.start * 1000)))
            self.vna.write(lin_freq_end(self.model, int(self.freq.end * 1000)))
            self.vna.write(lin_freq_points(self.model, self.freq.points))
            self.vna.write(lin_freq_mode(self.model))

        # Remaining steps are shared among linear and list sweeps:
        # 1. Set the averaging factor
        # 2. Turn on averaging
        # 3. Reset the averaging
        # 4. Set the IF bandwidth (in Hz)
        # 5. Turn on error correction if needed
        self.vna.write(avg_factor(self.model, avg))
        self.vna.write(avg_on(self.model))
        self.vna.write(avg_reset(self.model))
        self.vna.write(if_bw(self.model, bw))
        # if self.using_correction:
        #     self.vna.write(correction_on(self.model))
        return 0


    def get_data(self, theta, phi, data_type):
        """Returns one data point for every frequency specified in setup.
        Each data point contains the data type (S11 vs S21), positioner coordinates,
        and magnitude (dB) and phase (degrees) of the data"""
        temp_data_set = []
        output_real = []
        output_im = []

        # Action to perform on the VNA
        # 1. Display both data (current, live trace) and memory (saved snapshot) on the VNA
        # 2. Display in polar format
        # 3. Set markers to record in polar logarithmic format
        # 4. Auto scale the data
        # 5. Save data to memory
        # 6. Send data back
        self.vna.write(display_data_and_mem(self.model))
        self.vna.write(polar(self.model))
        self.vna.write(polar_log_marker(self.model))
        self.vna.write(auto_scale(self.model))
        self.vna.write(data_to_mem(self.model))
        self.vna.write(output_formatted_data(self.model))

        # Data is sent back in the following format:
        # data header | real component | imaginary component | real component | imaginary component......
        #  (4 bytes)  |   (4 bytes)    |     (4 bytes)       |   (4 bytes)    |     (4 bytes)....
        #             |   Value for 1st frequency            |         Value for 2nd frequency .......
        #
        # Data is sorted into two lists: one for real component, and one for imaginary component
        # Once all data is sorted, it is converted from rectangular to polar form then returned
        if isinstance(self.freq, list):
            output = self.vna.read_bytes(4 + 8 * len(self.freq))
            x = 0
            while x < 2 * len(self.freq):
                output_real.append(unpack('>f', output[4 * (x + 1):4 * (x + 2)])[0])
                x = x + 1
                output_im.append(unpack('>f', output[4 * (x + 1):4 * (x + 2)])[0])
                x = x + 1
        else:
            output = self.vna.read_bytes(4 + 8 * self.freq.points)
            x = 0
            while x < 2 * self.freq.points:
                output_real.append(unpack('>f', output[4 * (x + 1):4 * (x + 2)])[0])
                x = x + 1
                output_im.append(unpack('>f', output[4 * (x + 1):4 * (x + 2)])[0])
                x = x + 1

        if isinstance(self.freq, list):
            length = len(self.freq)
            for i in range(0, length):
                rect_temp = [output_real[i], output_im[i]]
                mag_temp = 20 * math.log(math.sqrt(rect_temp[0] * rect_temp[0] + rect_temp[1] * rect_temp[1]) + 1e-60,
                                         10)
                phase_temp = phase(rect_temp)
                if data_type == 'S21':
                    temp_data_set.append(Data('S21', self.freq[i], theta, phi, mag_temp, phase_temp))
                else:
                    temp_data_set.append(Data('S11', self.freq[i], theta, phi, mag_temp, phase_temp))
        else:
            span = self.freq.end - self.freq.start
            for i in range(0, self.freq.points):
                freq = self.freq.start + i * span / (self.freq.points - 1)
                rect_temp = [output_real[i], output_im[i]]
                mag_temp = 20 * math.log(math.sqrt(rect_temp[0] * rect_temp[0] + rect_temp[1] * rect_temp[1]) + 1e-60,
                                         10)
                phase_temp = phase(rect_temp)
                if data_type == 'S21':
                    temp_data_set.append(Data('S21', freq, theta, phi, mag_temp, phase_temp))
                else:
                    temp_data_set.append(Data('S11', freq, theta, phi, mag_temp, phase_temp))
        return temp_data_set

    def calibrate_open(self):
        self.vna.write(cal_s11_1_port(self.model))
        self.vna.write(cal_s11_1_port_open(self.model))
        self.using_correction = True

    def calibrate_short(self):
        self.vna.write(cal_s11_1_port_short(self.model))

    def calibrate_load(self):
        self.vna.write(cal_s11_1_port_load(self.model))
        self.vna.write(save_1_port_cal(self.model))
        self.vna.write(correction_on(self.model))

    def rst_avg(self, data_type):  # the S11 and S21 commands automatically trigger an averaging reset in the VNA
        if data_type == 'S11':
            self.vna.write(s11(self.model))
        elif data_type == 'S21':
            self.vna.write(s21(self.model))


def phase(rect_coord):
    if rect_coord[0] == 0:
        if rect_coord[1] > 0:
            p = 90
        else:
            p = -90
    elif rect_coord[1] == 0:
        if rect_coord[0] > 0:
            p = 0
        else:
            p = 180
    else:
        p = math.degrees(math.atan(rect_coord[1] / rect_coord[0]))

    if rect_coord[0] < 0:
        if rect_coord[1] > 0:
            p = p + 180
        elif rect_coord[1] < 0:
            p = p - 180
    return p
