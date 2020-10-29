################################################################################
# measurement_ctrl
# Description:
#  
#
# Status:
#
#
# Dependencies: 
#   PyVISA Version: 1.10.1
#   PyQt5  Version: ?
#
# Authors: Eric Li, Thomas Hoover
# Date: 20200806
# Built with Python Version: 3.8.5
# For any questions, contact Eric at eric.li.1999@gmail.com
#   or Thomas at tomhoover1@gmail.com
################################################################################
import measurement_ctrl.vna_comms as vna_comms
import measurement_ctrl.positioner as positioner
from measurement_ctrl.integer import Coordinate
import measurement_ctrl.data_storage as data_storage
from time import sleep
from threading import Lock, Thread, local
import pyvisa as visa
import sys
from PyQt5 import QtCore as qtc


class MeasurementCtrlSignals(qtc.QObject):
    setupComplete  = qtc.pyqtSignal()
    runComplete    = qtc.pyqtSignal()
    runPaused      = qtc.pyqtSignal()
    runStopped     = qtc.pyqtSignal()
    progress       = qtc.pyqtSignal(int  )
    currentPan     = qtc.pyqtSignal(float)
    currentTilt    = qtc.pyqtSignal(float)
    requestJogCW   = qtc.pyqtSignal(list)
    requestJogCCW  = qtc.pyqtSignal(list )
    requestJogUp   = qtc.pyqtSignal(list )
    requestJogDown = qtc.pyqtSignal(list )
    requestMoveTo  = qtc.pyqtSignal(list )
    startLockClock = qtc.pyqtSignal()
    calReady       = qtc.pyqtSignal()
    error          = qtc.pyqtSignal()
"""End MeasurementCtrlSignals Class"""


class MeasurementCtrl(qtc.QObject):
    def __init__(self, args, data_file='data\\data0.csv'):
        super().__init__()
        self.impedance = args['impedance']  # if true, S11 and S21 will be measured. Else, only S21
        if args['list'] is not None:          # list or vna_comms.lin_freq obj
            self.freq = args['list']
        else:
            self.freq = vna_comms.LinFreq(args['linear']['start'], args['linear']['stop'], args['linear']['points'])
        self.cal = args['calibration'] # true or false
        self.avg = args['averaging'] # e.g. 8, 16, etc.
        self.sweep_mode = args['positioner_mv'] # either 'continuous' or 'step'
        self.offset = args['offset']['pan']       
        self.exe_mode = args['sweep_axis'] # 'pan' for pan sweep or 'tilt' for tilt sweep
        self.const_angle = args['fixed_angle'] # angle at which non-changing coordinate is set to
        self.resolution = args['resolution']
        self.vna = vna_comms.Session('GPIB0::' + str(args['gpib_addr']) + '::INSTR')
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

        # Jog speed limits
        self.MAX_PAN_TIME = 1240
        self.MIN_PAN_SPEED = 8
        self.MAX_PAN_SPEED = 127
        self.MAX_TILT_TIME = 700
        self.MIN_TILT_SPEED = 17
        self.MAX_TILT_SPEED = 127

        self.resume          = False # measurement is resuming from paused state flag
        self.pause_move      = False # movement needs paused flag (discrete case)
        self.pause_jog       = False # jog thread needs paused (continuous case)
        self.stop            = False # stop measurement flag
        self.finished        = False # measurement finished flag
        self.paused_loop_idx = 0     # saved loop index to enable measurement to be resumed
        self.open_proceed    = False # flags for proceeding in calibration
        self.short_proceed   = False # flags for proceeding in calibration
        self.load_proceed    = False # flags for proceeding in calibration
        self.cal_finished    = False # flag for completing calibration

        self.signals = MeasurementCtrlSignals()
        self.error_message = None


    def setup(self):
        """Initializes the positioner and vna to perform a measurement sweep.

        Init steps are performed as follows:
            1. Emit signal indicating setup is complete
            2. Reset the vna
            3. Create the data storage file
            4. Perform calibration of vna if necessary
            5. Configure the vna, and calculate the vna delays
            6. Calculate the positioner speed needed in relation to the vna delays,
               if necessary, and configure the positioner speed settings
            7. Move the positioner to the starting location and update position data 
        """
        try:
            # Reset vna and create data storage file
            if self.cal is True:
                self.vna.reset_all()
            else:
                self.vna.reset()

            # Calibrate vna if needed
            if self.cal is True:
                self.signals.calReady.emit()
                while True:
                    if self.open_proceed is True:
                        self.vna.calibrate_open()
                        break
                self.signals.calReady.emit()
                while True:
                    if self.short_proceed is True:
                        self.vna.calibrate_short()
                        break
                self.signals.calReady.emit()
                while True:
                    if self.load_proceed is True:
                        self.vna.calibrate_load()
                        break
                self.signals.calReady.emit()
                while True:
                    if self.cal_finished is True:
                        break

            # Configure the vna and calculate vna delays
            self.vna.setup(self.freq, self.avg, 3700)
            if self.impedance is True:
                self.vna.using_correction = True
            [self.vna_avg_delay, self.vna_S11_delay, self.vna_S21_delay] = self.compute_vna_delay()

            # Calculate positioner speed needed based on vna delays, if needed
            if self.sweep_mode == 'continuous': # check if a continuous sweep is possible
                if self.exe_mode == 'pan':
                    total_time = (self.vna_avg_delay + self.vna_S21_delay) * 360 / self.resolution
                    if total_time > self.MAX_PAN_TIME:
                        self.sweep_mode = 'step'
                        self.pan_speed = 0
                    else:
                        self.pan_speed = self.compute_pan_speed(total_time)
                else:
                    total_time = (self.vna_avg_delay + self.vna_S21_delay) * 180 / self.resolution
                    if total_time > self.MAX_TILT_TIME:
                        self.sweep_mode = 'step'
                        self.tilt_speed = 0
                    else:
                        self.tilt_speed = self.compute_tilt_speed(total_time)

            # Move to starting location and update position data
            if self.exe_mode == 'pan':
                self.signals.requestMoveTo.emit([-180+self.offset, self.const_angle, 'abs'])
                self.wait_on_pan_setup(-180+self.offset)
 
        except Exception as e:
            self.error_message = str(e)
            self.signals.error.emit()

        

    def run(self):
        try:
            if not self.resume:
            # If run is not resuming from paused state of transport model setup
            # MeasurementCtrl and conditionally perform impedance measurement,
            # otherwise, skip performing those steps
                self.setup()
                if self.impedance is True:
                    self.vna.rst_avg('S11')
                    sleep(self.vna_avg_delay)
                    self.record_data('S11', self.file)    # need to create_file prior

            if self.pause_move:
            # Catch instance of pause button being pressed while self.setup() or
            # impedance measurement being performed, that is the only system condition
            # in which self.pause_move would be true at this point of execution
            # for the run() function. If the pause button was pressed, clear the
            # pause_move flag, then return from the run to stop the thread of execution
                self.signals.runPaused.emit()
                self.pause_move = False
                return None

            #------------------------------ Step Case -----------------------------
            elif self.sweep_mode == 'step':
                # Emit setupComplete to change mc_state in transport control model
                # to 'Running' signaling to the gui that measurement system setup
                # is complete and the measurement sweep is starting execution
                self.signals.setupComplete.emit()

                #------------------------ Pan Step Case ---------------------------
                if self.exe_mode == 'pan':
                    # Load loop index from class member storage before entering the
                    # loop. If the execution isn't being resumed, this value will
                    # be zero, otherwise it will reperesent the state of a previously
                    # paused measurement sweep, allowing that sweep to be resumed
                    i = self.paused_loop_idx
                    while i <= int(360/self.resolution):
                    # Core execution loop of the measurement sweep. Continues until
                    # either the full sweep has been performed, or until a flag
                    # variable set by the transport control model causes it to
                    # break out of the loop.
                        if self.resume is True:
                        # If the sweep is being resumed, then the measurement at this
                        # position has already been performed, so calculate the next
                        # azimuth angle to be measured, and then move positioner there
                            self.resume = False
                            target = (i * self.resolution) - 180
                            self.signals.requestMoveTo.emit(
                                [target, self.const_angle, 'abs']
                            )
                            self.wait_on_pan_cw(target)
                        # Delay for vna reset, take measurement, then update progress
                        self.step_delay()
                        self.record_data('S21', self.file)
                        self.progress = int(i * self.resolution / 360 * 100)
                        if self.progress > 100:
                            self.progress = 100
                        self.signals.progress.emit(self.progress)
                        # Check if the sweep should be paused, stopped, or if it is complete
                        if self.is_step_pan_complete() is True:
                        # The sweep is finished, so set the finished flag so that
                        # nulls are written to the end of the data file and the
                        # runComplete signal gets emitted, then break out of the loop
                            self.finished = True
                            break
                        elif self.stop is True:
                        # The transport control model is attempting to stop the sweep
                        # so clear the progress, emit the runStopped signal, and
                        # then break out of the loop
                            self.progress = 0
                            self.signals.runStopped.emit()
                            break
                        elif self.pause_move is True:
                        # The transport control model is attempting to pause the sweep
                        # so store the current value of the loop counter after adding
                        # one to it to prevent overlapping measurements, clear the
                        # pause_move flag that was set by the transport control model,
                        # emit the runPaused signal, and the break out of the loop
                            self.paused_loop_idx = i + 1
                            self.pause_move = False
                            self.signals.runPaused.emit()
                            break
                        else:
                        # Continue sweep execution, increment loop counter, calculate
                        # the next azimuth angle based on new loop counter, then
                        # move the positioner to that location
                            i = i + 1
                            target = (i * self.resolution) - 180
                            self.signals.requestMoveTo.emit(
                                [target, self.const_angle, 'abs'] 
                            )
                            self.wait_on_pan_cw(target)
                #------------------------------------------------------------------
            #----------------------------------------------------------------------

            #--------------------------- Continuous Case --------------------------
            else:
                # Emit setupComplete to change mc_state in transport control model
                # to 'Running' signaling to the gui that measurement system setup
                # is complete and the measurement sweep is starting execution
                self.signals.setupComplete.emit()
                if self.resume is True:
                # If sweep is resuming, clear resume flag since it is not needed
                # inside of the main execution loop to get the positioner to the
                # correct starting position
                    self.resume = False

                #--------------------- Pan Continuous Case ------------------------
                if self.exe_mode == 'pan':
                    # Since sweep is starting from a standstill, both for a new sweep
                    # and resuming a paused sweep, use init_cont_sweep to reset the
                    # vna, enforce the wait for the reset delay, then take the initial
                    # sweep measurement. Once this is complete, start up thread of
                    # execution for timing the transmission of jog requests to the
                    # positioner, and the load the loop index from class member storage.
                    # If sweep is being resumed it will represent the state of a
                    # previously paused measurement sweep, allowing that sweep to be
                    # resumed, otherwise its value will be zero representing a new sweep.
                    self.init_cont_sweep()
                    Thread_Jog = Thread(target=self.send_pan_jog, args=(), daemon=True)
                    Thread_Jog.start()
                    i = self.paused_loop_idx
                    while i <= int(360/self.resolution):
                    # Core execution loop of the measurement sweep. Continues until
                    # either the full sweep has been performed, or until a flag variable
                    # set by the transport control model causes it to break out of loop.
                        # Change i to index MeasurementCtrl was paused at if resuming
                        # if self.resume is True:
                        #     self.resume = False
                        #     self.pause = False

                        # Delay for vna reset, take measurement, then update progress
                        # lock is a Lock that is acquired by a thread started in the
                        # init_cont_lock function that forces the thread to wait for
                        # the vna_avg_reset time in a non blocking manner. Calculate
                        # the target angle so that the inner while loop can ensure the
                        # next measurement is not taken too early, while the outer
                        # while loop forces the thread to wait on the lock to be released
                        lock = self.init_cont_lock()
                        target = (i * self.resolution) - 180
                        # self.update_position()
                        while lock.acquire(blocking=False) is not True:
                            sleep(.2)
                            # self.update_position()
                            while self.pan < target:
                                sleep(.2)
                                # self.update_position()
                        self.record_data('S21', self.file)
                        self.progress = int((target + 180) / 360 * 100)
                        if self.progress > 100:
                            self.progress = 100
                        self.signals.progress.emit(self.progress)
                        # Check if sweep should be paused, stopped, or if it is completed
                        if self.is_continuous_pan_complete() is True:
                        # The sweep is finished
                            # Set the finished flag so nulls are written to the end
                            # end of the data file and the runComplete signal gets
                            # emitted, stop the positioner, break out of loop
                            self.pause_jog = True
                            if Thread_Jog.is_alive():
                                Thread_Jog.join()
                            self.finished = True
                            break
                        elif self.pause_move is True:
                        # The transport control model is attempting to pause the sweep
                            # Store current loop counter + 1 to prevent overlapping
                            # measurements, clear the pause_move flag for transport
                            # control model
                            self.pause_move = False
                            self.paused_loop_idx = i + 1
                            self.pause_jog = True
                            if Thread_Jog.is_alive():
                                Thread_Jog.join()
                            self.signals.runPaused.emit()
                            break
                        elif self.stop is True:
                            self.pause_jog = True
                            if Thread_Jog.is_alive():
                                Thread_Jog.join()
                            self.signals.runStopped.emit()
                            self.progress = 0
                            break
                        else:
                        # Continue sweep execution
                            # Increment the loop index
                            i = i + 1
                #------------------------------------------------------------------
            #----------------------------------------------------------------------

            if self.finished is True:
                with open(self.file, 'a') as file:
                    file.write("null,null,null,null,null,null\n")
                self.signals.runComplete.emit()
        except Exception as e:
            self.error_message = str(e)
            self.signals.error.emit()


    def step_delay(self):
        self.vna.rst_avg('S21')
        sleep(self.vna_avg_delay)


    def continuous_delay(self, lock):
        with lock:
            sleep(self.vna_avg_delay)


    def send_pan_jog(self):
        while self.pan < 180:
            if self.pause_jog is True:
                self.pause_jog = False
                break
            self.signals.requestJogCW.emit(['mc', self.pan_speed, Coordinate(180,0)])
            sleep(0.12)


    def send_tilt_jog(self):
        while self.tilt < 90:
            if self.pause_jog is True:
                self.pause_jog = False
                break
            self.signals.requestJogUp.emit(['mc', self.tilt_speed, Coordinate(0,90)])
            sleep(0.12)


    def is_step_pan_complete(self):
        if self.progress >= 100:
            return True
        return False


    def is_step_tilt_complete(self):
        if self.progress >= 100:
            return True
        return False


    def init_cont_sweep(self):
        lock = Lock()
        self.vna.rst_avg('S21')
        t1 = Thread(target=self.continuous_delay, args=(lock,), daemon=True)
        t1.start()                
        t1.join()
        self.record_data('S21', self.file)


    def init_cont_lock(self):
        lock = Lock()
        self.vna.rst_avg('S21')
        t2 = Thread(target=self.continuous_delay, args=(lock,), daemon=True)
        t2.start()
        return lock


    @qtc.pyqtSlot()
    def pause_measurement(self):
        self.paused = True


    @qtc.pyqtSlot()
    def resume_measurement(self):
        self.resume = True


    def halt(self):
        self.qpt.move_to(0, 0, 'stop')


    @qtc.pyqtSlot(float)
    def update_pan(self, pan):
        self.pan = pan

    @qtc.pyqtSlot(float)
    def update_tilt(self, tilt):
        self.tilt = tilt


    def record_data(self, s, file):
        if s == 'S21':
            data_storage.append_data(file, self.vna.get_data(self.tilt, self.pan, s))
        else:
            data_storage.append_data(file, self.vna.get_data(0, 0, s))


    def is_continuous_pan_complete(self):
        if self.progress >= 100:
            return True
        return False


    def is_continuous_tilt_complete(self):
        if self.progress >= 100:
            return True
        return False


    def wait_on_pan_cw(self, target):
        count = 0
        while self.pan <= target:
            sleep(0.2)
            count = count + 1
            if count >= 25:
                break


    def wait_on_pan_ccw(self, target):
        count = 0
        while self.pan >= target:
            sleep(0.2)
            count = count + 1
            if count >= 25:
                break


    def wait_on_pan_setup(self, target):
        count = 0
        while self.pan > (target+1) and self.stop is not True:
            sleep(0.2)
            count = count + 1
            if count > 300:
                break


    def wait_on_tilt_setup(self, target):
        count = 0
        while self.tilt < (target+1):
            sleep(0.2)
            count = count + 1
            if count > 300:
                break


    def wait_on_tilt_up(self, target):
        count = 0
        while self.tilt <= target or count <= 25:
            sleep(0.2)
            count = count + 1


    def wait_on_tilt_down(self, target):
        count = 0
        while self.tilt >= target or count <= 25:
            sleep(0.2)
            count = count + 1


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
        if pan_speed <= self.MIN_PAN_SPEED:
            return self.MIN_PAN_SPEED
        elif pan_speed >= self.MAX_PAN_SPEED:
            return self.MAX_PAN_SPEED
        return int(pan_speed)


    def compute_tilt_speed(self, total_time):
        tilt_speed = int((39.3701*(180.0 / total_time) + 6.8228))
        if tilt_speed <= self.MIN_TILT_SPEED:
            return self.MIN_TILT_SPEED
        elif tilt_speed >= self.MAX_TILT_SPEED:
            return self.MAX_TILT_SPEED
        return int(tilt_speed)
"""End meas_ctrl Class"""

