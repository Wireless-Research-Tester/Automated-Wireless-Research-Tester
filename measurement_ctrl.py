################################################################################
#
#  Description:
#  
#
#  Status:
#
#
#  Dependencies:
#      PyVISA Version: 1.10.1
#
#  Authors: Eric Li, Thomas Hoover
#  Date: 20200806
#  Built with Python Version: 3.8.5
#
################################################################################
import vna_comms
import positioner
from integer import Coordinate
import data_storage
from time import sleep
from threading import Lock, Thread
import sys
from PyQt5 import QtCore as qtc


class MeasurementCtrlSignals(qtc.QObject):
    setupComplete = qtc.pyqtSignal()
    runComplete   = qtc.pyqtSignal()
    runPaused     = qtc.pyqtSignal()
    runStopped    = qtc.pyqtSignal()
    progress      = qtc.pyqtSignal(int)
    currentPan    = qtc.pyqtSignal(float)
    currentTilt   = qtc.pyqtSignal(float)
"""End MeasurementCtrlSignals Class"""


class MeasurementCtrl:
    def __init__(
            self,
            args,
            data_file='data\\data0.csv'):

        self.impedance = args['impedance']  # if true, S11 and S21 will be measured. Else, only S21
        if len(args['list']) != 0:          # list or vna_comms.lin_freq obj
            self.freq = args['list']
        else:
            self.freq = vna_comms.LinFreq(args['linear']['start'], args['linear']['end'], args['linear']['points'])
        self.cal = args['calibration'] # true or false
        self.avg = args['averaging'] # e.g. 8, 16, etc.
        self.sweep_mode = args['positioner_mv'] # either 'continuous' or 'step'
        self.offset = args['offset']['pan']       
        self.exe_mode = args['sweep_axis'] # 'pan' for pan sweep or 'tilt' for tilt sweep
        self.const_angle = args['fixed_angle'] # angle at which non-changing coordinate is set to
        self.resolution = args['resolution']
        self.vna = vna_comms.Session('GPIB0::' + str(args['gpib_addr']) + '::INSTR')
        self.qpt = positioner.Positioner('ASRL' + str(args['alias']) + '::INSTR', args['baud_rate'])
        self.progress = 0 # percentage, e.g. 11 for 11%
        self.vna_avg_delay = 0
        self.vna_S11_delay = 0
        self.vna_S21_delay = 0
        self.pan_speed = 0
        self.tilt_speed = 0
        self.vna_lock = Lock()
        self.file = data_file
        self.pan = -1
        self.tilt = -1
        self.signals = MeasurementCtrlSignals()
        self.update_position()


    def setup(self):
        """Initializes the positioner and vna to perform a measurement sweep.

        Init steps are performed as follows:
            1. Move the positioner to the starting location and update position data
            2. Reset the vna
            3. Create the data storage file
            4. Perform calibration of vna if necessary
            5. Configure the vna, and calculate the vna delays
            6. Calculate the positioner speed needed in relation to the vna delays,
               if necessary, and configure the positioner speed settings
            7. Emit signal indicating setup is complete
        """
        # Move to starting location and update position data
        if self.exe_mode == 'pan':
            self.qpt.move_to(-180+self.offset, self.const_angle, 'abs')
        else:
            self.qpt.move_to(self.offset+self.const_angle, -90, 'abs')
        self.update_position()

        # Reset vna and create data storage file
        self.vna.reset()
        data_storage.create_file(self.file)
        
        # Calibrate vna if needed
        if self.cal is True:
            self.vna.calibrate() # cal prompts have to be changed for GUI integration
        
        # Configure the vna and calculate vna delays
        self.vna.setup(self.freq, self.avg, 3700)
        [self.vna_avg_delay, self.vna_S11_delay, self.vna_S21_delay] = self.compute_vna_delay()
        
        # Calculate positioner speed needed based on vna delays, if needed
        if self.sweep_mode == 'continuous': # check if a continuous sweep is possible
            if self.exe_mode == 'pan':
                total_time = (self.vna_avg_delay + self.vna_S21_delay) * 360 / self.resolution
                if total_time > self.qpt.MAX_PAN_TIME:
                    self.sweep_mode = 'step'
                    self.pan_speed = 0
                else:
                    self.pan_speed = self.compute_pan_speed(total_time)
            else:
                total_time = (self.vna_avg_delay + self.vna_S21_delay) * 180 / self.resolution
                if total_time > self.qpt.MAX_TILT_TIME:
                    self.sweep_mode = 'step'
                    self.tilt_speed = 0
                else:
                    self.tilt_speed = self.compute_tilt_speed(total_time)

        # Signal Gui that setup of meas_ctrl is complete and sweep is ready to commence
        self.signals.setupComplete.emit()


    def run(self):
        if self.impedance is True:
            self.vna.rst_avg('S11')
            sleep(self.vna_avg_delay)
            self.record_data('S11', self.file)    # need to create_file prior

        # Step Case
        if self.sweep_mode == 'step':
            # Pan Case
            if self.exe_mode == 'pan':
                for i in range(0, int(360/self.resolution)):
                    self.step_delay()
                    self.record_data('S21', self.file)
                    self.progress = int((i+1) * self.resolution / 360 * 100)
                    if self.progress > 100:
                        self.progress = 100
                    self.signals.progress.emit(self.progress)
                    if self.is_step_pan_complete() is True:
                        break
                    else:
                        target = ((i+1) * self.resolution) - 180
                        self.qpt.move_to(target, self.const_angle, 'abs')
            # Tilt Case
            else:
                for i in range(0, int(180/self.resolution)):
                    self.step_delay()
                    self.record_data('S21', self.file)
                    self.progress = int((i+1) * self.resolution / 180 * 100)
                    if self.progress > 100:
                        self.progress = 100
                    self.signals.progress.emit(self.progress)
                    if self.is_step_tilt_complete() is True:
                        break
                    else:
                        target = ((i+1) * self.resolution) - 90
                        self.qpt.move_to(self.const_angle, target, 'abs')

        # Continuous Case
        else:
            # Pan Case
            if self.exe_mode == 'pan':
                self.init_continuous_sweep()
                for i in range(0, int(360/self.resolution)):
                    lock = self.init_continuous_lock()
                    target = ((i+1) * self.resolution) - 180
                    self.update_position()
                    while lock.acquire(blocking=False) is not True:
                        while self.pan < target:
                            sleep(.08)
                            self.qpt.jog_cw(self.pan_speed, Coordinate(180, 0))
                            self.update_position()
                    self.record_data('S21', self.file)
                    self.progress = int((target + 180) / 360 * 100)
                    if self.progress > 100:
                        self.progress = 100
                    self.signals.progress.emit(self.progress)
                    if self.is_continuous_pan_complete() is True:
                        self.halt()
                        break
                    else:
                        self.qpt.jog_cw(self.pan_speed, Coordinate(180, 0))
            # Tilt Case
            else:
                self.init_continuous_sweep()
                for i in range(0, int(180/self.resolution)):
                    lock = self.init_continuous_lock()
                    target = ((i+1) * self.resolution) - 90
                    self.update_position()
                    while lock.acquire(blocking=False) is not True:
                        while self.tilt < target:
                            sleep(.08)
                            self.qpt.jog_up(self.tilt_speed, Coordinate(0, 90))
                            self.update_position()
                    self.record_data('S21', self.file)
                    self.progress = int((target + 90) / 180 * 100)
                    if self.progress > 100:
                        self.progress = 100
                    self.signals.progress.emit(self.progress)
                    if self.is_continuous_tilt_complete() is True:
                        self.halt()
                        break
                    else:
                        self.qpt.jog_up(self.tilt_speed, Coordinate(0, 90))
        
        with open(self.file, 'a') as file:
            file.write("null,null,null,null,null,null\n")

        self.signals.runComplete.emit()


    def halt(self):
        self.qpt.move_to(0, 0, 'stop')


    def update_position(self):
        curr = self.qpt.get_position()
        self.pan = curr.pan_angle()
        self.tilt = curr.tilt_angle()


    def record_data(self, s, file):
        if s == 'S21':
            self.update_position()
            data_storage.append_data(file, self.vna.get_data(self.tilt, self.pan, s))
        else:
            data_storage.append_data(file, self.vna.get_data(0, 0, s))


    def step_delay(self):
        self.vna.rst_avg('S21')
        sleep(self.vna_avg_delay)


    def continuous_delay(self, lock):
        with lock:
            sleep(self.vna_avg_delay)


    def is_step_pan_complete(self):
        if self.progress >= 100:
            return True
        return False


    def is_step_tilt_complete(self):
        if self.progress >= 100:
            return True
        return False


    def init_continuous_sweep(self):
        lock = Lock()
        self.vna.rst_avg('S21')
        t1 = Thread(target=self.continuous_delay, args=(lock,))
        t1.start()                
        t1.join()
        self.record_data('S21', self.file)


    def init_continuous_lock(self):
        lock = Lock()
        self.vna.rst_avg('S21')
        t2 = Thread(target=self.continuous_delay, args=(lock,))
        t2.start()
        return lock


    def is_continuous_pan_complete(self):
        if self.progress >= 100:
            return True
        return False


    def is_continuous_tilt_complete(self):
        if self.progress >= 100:
            return True
        return False


    # returns list w/ 3 numbers in seconds, [averaging delay, get_data delay (S11), get_data delay (S21)]
    def compute_vna_delay(self):        
        if isinstance(self.freq, list):
            if len(self.freq) <= 5:
                if self.avg <= 8:
                    return [2.19, 1.202, 1.26]
                return [3.98, 1.202, 1.26]
            elif len(self.freq) <= 10:
                if self.avg <= 8:
                    return [3.02, 1.296, 1.35]
                return [5.80, 1.296, 1.35]
            elif len(self.freq) <= 15:
                if self.avg <= 8:
                    return [3.11, 1.36, 1.42]
                return [5.95, 1.36, 1.42]
            elif len(self.freq) <= 20:
                if self.avg <= 8:
                    return [3.36, 1.417, 1.489]
                return [6.48, 1.417, 1.489]
            elif len(self.freq) <= 25:
                if self.avg <= 8:
                    return [3.26, 1.477, 1.547]
                return [6.35, 1.477, 1.547]
            else:
                if self.avg <= 8:
                    return [3.58, 1.52, 1.61]
                return [6.76, 1.52, 1.61]
        else:
            if self.freq.points <= 201:
                if self.avg <= 8:
                    return [3.79, 1.71, 2.03]
                return [7.30, 1.71, 2.03]
            elif self.freq.points <= 401:
                if self.avg <= 8:
                    return [4.23, 2.15, 2.73]
                return [7.99, 2.15, 2.73]
            elif self.freq.points <= 801:
                if self.avg <= 8:
                    return [5.49, 3.01, 4.09]
                return [10.39, 3.01, 4.09]
            elif self.freq.points <= 1601:
                if self.avg <= 8:
                    return [8.51, 4.72, 6.74]
                return [16.06, 4.72, 6.74]


    def compute_pan_speed(self, total_time):
        pan_speed = int((12.8866*(360.0 / total_time) + 3.1546))
        if pan_speed <= self.qpt.MIN_PAN_SPEED:
            return self.qpt.MIN_PAN_SPEED
        elif pan_speed >= self.qpt.MAX_PAN_SPEED:
            return self.qpt.MAX_PAN_SPEED
        return int(pan_speed)


    def compute_tilt_speed(self, total_time):
        tilt_speed = int((39.3701*(180.0 / total_time) + 6.8228))
        if tilt_speed <= self.qpt.MIN_TILT_SPEED:
            return self.qpt.MIN_TILT_SPEED
        elif tilt_speed >= self.qpt.MAX_TILT_SPEED:
            return self.qpt.MAX_TILT_SPEED
        return int(tilt_speed)
"""End meas_ctrl Class"""

