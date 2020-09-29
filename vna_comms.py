import pyvisa as visa
import math
from struct import unpack
from syntaxes import find_command, Action, check_model


class data:
    def __init__(self, measurement_type, freq, theta, phi, value_mag, value_phase):
        self.measurement_type = measurement_type
        self.freq = freq
        self.theta = theta
        self.phi = phi
        self.value_mag = value_mag
        self.value_phase = value_phase


class lin_freq:
    def __init__(self, start, end, points):
        self.start = start
        self.end = end
        self.points = points


class session:
    def __init__(self, resource):
        self.rm = visa.ResourceManager()
        self.vna = self.rm.open_resource(resource)
        self.vna.read_termination = '\n'
        del self.vna.timeout
        self.model = check_model(self.vna.query('*IDN?'))
        self.vna.write(find_command(self.model, Action.FORM2))
        self.freq = None
        self.using_correction = False

    def reset_all(self):  # resets the entire machine to factory presets
        self.vna.write(find_command(self.model, Action.RESET))
        self.using_correction = False
        return 0

    def reset(self):  # resets only measurement parameters changed in setup (do not wipe calibration data!)
        self.vna.write(find_command(self.model, Action.EDIT_LIST))
        self.vna.write(find_command(self.model, Action.CLEAR_LIST))

    def setup(self, freq, avg, bw):
        self.freq = freq

        if isinstance(self.freq, list):
            if len(self.freq) > 30:  # if sweep type is frequency list, only take a max of 30 frequencies
                raise Exception('The number of frequencies in the frequency list exceeded 30.')
            for i in range(0, len(self.freq)):
                freq_temp = self.freq[i]
                self.vna.write(find_command(self.model, Action.EDIT_LIST))
                self.vna.write(find_command(self.model, Action.ADD_LIST_FREQ, int(freq_temp * 1000)))
            self.vna.write(find_command(self.model, Action.LIST_FREQ_MODE))
        else:
            self.vna.write(find_command(self.model, Action.LIN_FREQ_START, int(self.freq.start * 1000)))
            self.vna.write(find_command(self.model, Action.LIN_FREQ_END, int(self.freq.end * 1000)))
            self.vna.write(find_command(self.model, Action.LIN_FREQ_POINTS, self.freq.points))
            self.vna.write(find_command(self.model, Action.LIN_FREQ_MODE))

        self.vna.write(find_command(self.model, Action.AVG_FACTOR, avg))
        self.vna.write(find_command(self.model, Action.AVG_ON))
        self.vna.write(find_command(self.model, Action.AVG_RESET))
        self.vna.write(find_command(self.model, Action.IF_BW, bw))
        if self.using_correction:
            self.vna.write(find_command(self.model, Action.CORRECTION_ON))
        return 0

    def get_data(self, theta, phi, data_type):
        temp_data_set = []
        output_real = []
        output_imag = []

        self.vna.write(find_command(self.model, Action.DISPLAY_DATA_AND_MEM))
        self.vna.write(find_command(self.model, Action.POLAR))
        self.vna.write(find_command(self.model, Action.POLAR_LOG_MARKER))
        self.vna.write(find_command(self.model, Action.AUTO_SCALE))
        self.vna.write(find_command(self.model, Action.DATA_TO_MEM))
        self.vna.write(find_command(self.model, Action.OUTPUT_FORMATTED_DATA))

        if isinstance(self.freq, list):
            output = self.vna.read_bytes(4 + 8 * len(self.freq))
            x = 0
            while x < 2 * len(self.freq):
                output_real.append(unpack('>f', output[4 * (x + 1):4 * (x + 2)])[0])
                x = x + 1
                output_imag.append(unpack('>f', output[4 * (x + 1):4 * (x + 2)])[0])
                x = x + 1
        else:
            output = self.vna.read_bytes(4 + 8 * self.freq.points)
            x = 0
            while x < 2 * self.freq.points:
                output_real.append(unpack('>f', output[4 * (x + 1):4 * (x + 2)])[0])
                x = x + 1
                output_imag.append(unpack('>f', output[4 * (x + 1):4 * (x + 2)])[0])
                x = x + 1

        if isinstance(self.freq, list):
            length = len(self.freq)
            for i in range(0, length):
                rect_temp = [output_real[i], output_imag[i]]
                mag_temp = 20 * math.log(math.sqrt(rect_temp[0] * rect_temp[0] + rect_temp[1] * rect_temp[1]) + 1e-60,
                                         10)
                phase_temp = phase(rect_temp)
                if data_type == 'S21':
                    temp_data_set.append(data('S21', self.freq[i], theta, phi, mag_temp, phase_temp))
                else:
                    temp_data_set.append(data('S11', self.freq[i], theta, phi, mag_temp, phase_temp))
        else:
            span = self.freq.end - self.freq.start
            for i in range(0, self.freq.points):
                freq = self.freq.start + i * span / (self.freq.points - 1)
                rect_temp = [output_real[i], output_imag[i]]
                mag_temp = 20 * math.log(math.sqrt(rect_temp[0] * rect_temp[0] + rect_temp[1] * rect_temp[1]) + 1e-60,
                                         10)
                phase_temp = phase(rect_temp)
                if data_type == 'S21':
                    temp_data_set.append(data('S21', freq, theta, phi, mag_temp, phase_temp))
                else:
                    temp_data_set.append(data('S11', freq, theta, phi, mag_temp, phase_temp))
        return temp_data_set

    def calibrate(self):
        self.vna.write(find_command(self.model, Action.CAL_S11_1_PORT))
        input('Connect OPEN circuit to PORT 1. Press enter when ready...')
        self.vna.write(find_command(self.model, Action.CAL_S11_1_PORT_OPEN))
        input('Connect SHORT circuit to PORT 1. Press enter when ready...')
        self.vna.write(find_command(self.model, Action.CAL_S11_1_PORT_SHORT))
        input('Connect matched LOAD to PORT 1. Press enter when ready...')
        self.vna.write(find_command(self.model, Action.CAL_S11_1_PORT_LOAD))
        self.vna.write(find_command(self.model, Action.SAVE_1_PORT_CAL))
        print('Calibration is complete!')
        self.using_correction = True

    def rst_avg(self, data_type):  # the S11 and S21 commands automatically trigger an averaging reset in the VNA
        if data_type == 'S11':
            self.vna.write(find_command(self.model, Action.S11))
        elif data_type == 'S21':
            self.vna.write(find_command(self.model, Action.S21))


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
