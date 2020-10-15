""""
=============
Main Window
=============
"""
import sys
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5 import uic
from transport_app import TransportWidget
from meas_display_app import MeasurmentDisplayWindow
from settingsWindow_app import SettingsWindow
from progress_bar_app import ProgressBar
from positioner_toolbar_app import PositionerToolBarWidget
from measurement_ctrl import MeasurementCtrl
from positioner import Positioner
from integer import Coordinate
import json
from queue import Queue, Empty, Full
from time import time, sleep
from threading import Lock, Thread
import pyvisa as visa
from time import localtime, strftime

baseUIClass, baseUIWidget = uic.loadUiType('main_window_ui.ui')


class MyMainWindow(baseUIWidget, baseUIClass):
    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(qtg.QIcon('icon_transparent.png'))

        # ------------------------- Initialize Gui Components ----------------------
        # Construct the necessary widgets for MainWindow
        self.transport = TransportWidget()
        self.meas_disp_window = MeasurmentDisplayWindow()
        self.settings = SettingsWindow()
        self.progress_bar = ProgressBar()
        self.pos_control = PositionerToolBarWidget()

        # self.toolBar.setStyleSheet(
        #     "QToolButton#actionSettings:hover {background: qradialgradient(cx: 0.3, cy: -0.4, fx: 0.3, "
        #     "fy: -0.4,radius: 1.35, stop: 0 #fff, stop: 1 #bbb);}")
        # self.toolBar.setStyleSheet(
        #     "QToolButton#actionHelp:hover {background: qradialgradient(cx: 0.3, cy: -0.4, fx: 0.3, "
        #     "fy: -0.4,radius: 1.35, stop: 0 #fff, stop: 1 #bbb);}")

        # Add custom toolbars to MainWindow Widget
        transport_toolbar = self.addToolBar('Transport_ToolBar')
        meas_display_toolbar = self.addToolBar('Measurement_Display_ToolBar')
        progress_display_toolbar = self.addToolBar('Progress_Display_ToolBar')
        positioner_control_toolbar = self.addToolBar('Positioner_Control_ToolBar')

        # Add the custom widgets to the toolbars
        meas_display_toolbar.addWidget(self.meas_disp_window)
        transport_toolbar.addWidget(self.transport)
        progress_display_toolbar.addWidget(self.progress_bar)
        positioner_control_toolbar.addWidget(self.pos_control)
        # --------------------------------------------------------------------------

        # ------------------- Initialize Gui Signal Connections --------------------
        # Create connections between Settings button on toolbar
        # and the settings window
        self.actionSettings.triggered.connect(self.toggle_settings)
        self.settings.storageSignals.settingsStored.connect(self.actionSettings.trigger)
        self.settings.storageSignals.settingsClosed.connect(self.actionSettings.trigger)

        # Create connections between transport buttons and the functions
        # creating the Gui's control flow for MeasurementCtrl
        self.transport.playButton.clicked.connect(self.start_mc)
        self.transport.pauseButton.clicked.connect(self.pause_mc)
        self.transport.stopButton.clicked.connect(self.stop_mc)

        self.transport.pauseButton.setDisabled(True)
        self.transport.stopButton.setDisabled(True)
        # --------------------------------------------------------------------------

        # ----------------------------- Data Members -------------------------------
        self.is_settings_open = False  # Keeps track of settings window toggle

        # MeasurementCtrl and its necessary synchronization variables
        self.mc = None  # Placeholder for MeasurementCtrl object
        self.mc_thread = None  # Placeholder for thread to run MeasurementCtrl in
        self.mc_state = 'NotRunning'  # Keeps track of current state for MeasurementCtrl

        self.qpt = None  # Placeholder for Positioner object
        self.qpt_q = Queue()  # Message queue for communication btwn Gui and qpt_thread

        self.data_file = None
        # --------------------------------------------------------------------------

        # --------------- Initialize Positioner Signal Connections------------------
        rm = visa.ResourceManager()
        ports = rm.list_resources()
        for i in ports:
            if i[0:4] == 'ASRL':
                self.pos_control.portCombo.addItem(i)

        self.pos_control.connectStatus.setDisabled(True)

        self.pos_control.connectQPT.clicked.connect(self.connect_positioner)
        self.pos_control.disconnectQPT.clicked.connect(self.disconnect_positioner)
        self.pos_control.faultReset.clicked.connect(self.reset_positioner)
        
        self.pos_control.disconnectQPT.setDisabled(True)
        self.pos_control.faultReset.setDisabled(True)

        self.pos_control.timer = qtc.QTimer()
        self.pos_control.timer.setInterval(120)
        self.pos_control.timer.timeout.connect(self.recurring_qpt_command)
        self.pos_control.timer.start()
        # --------------------------------------------------------------------------
        self.show()

    """End __init__() of MyMainWindow"""

    # ------------------- MeasurementCtrl Transport Model Slots --------------------
    @qtc.pyqtSlot()
    def start_mc(self):
        msg = qtw.QMessageBox()
        msg.setWindowTitle('Warning!')
        msg.setText('Unable to start measurement')

        if self.mc_state == 'Paused':
            # Resumes an existing measurement that is in progress
            # Update the state of MeasurementCtrl and its flag variables to prepare
            # to resume measurement
            self.mc_state = 'SetupRunning'
            self.mc.resume = True
            self.mc.pause_move = False
            self.mc.pause_jog = False
            # Create and start thread for MeasurementCtrl.run() to execute in
            self.mc_thread = Thread(target=self.mc.run, args=(), daemon=True)
            self.mc_thread.start()
            self.pos_control.lineEdit.setText('SetupRunning')
            # Toggle enabled for relevant transport buttons
            self.transport.playButton.setDisabled(True)
            self.transport.pauseButton.setEnabled(True)
        elif self.mc_state == 'NotRunning':
            # Attempts to start a new measurement
            if self.settings.settings_empty:
                # If settings_empty, then the user has not gone into SettingsWindow
                # and configured the settings for a measurement to be performed, which
                # means pivot.json is empty, display window telling user know they need
                # to accept the measurement settings in the SettingsWindow before any
                # measurement can be started
                self.pos_control.lineEdit.setText('NotRunning')
                msg.setDetailedText(
                    'Need to submit settings before the measurement can begin'
                )
                msg.exec_()
            elif self.qpt is None:
                # If qpt is None, then the positioner is not connected, display window
                # telling user the positioner needs to be connected to perform a measurement
                msg.setDetailedText(
                    'Need to connect the positioner before the measurement can begin'
                )
                msg.exec_()
            else:
                # Starts a new measurement
                # Open the pivot file to retrieve the settings selected by user in
                # SettingsWindow, parse them into a dictonary, then initialize
                # MeasurementCtrl object
                with open(self.settings.pivot_file) as file:
                    dict = json.load(file)
                self.data_file = '/' + strftime("%b%d_%H%M_%S", localtime()) + '.csv'
                self.data_file = self.settings.project_dir + self.data_file
                self.mc = MeasurementCtrl(dict, self.qpt, self.data_file)
                # Connect signals and slots between MeasurementCtrl object,
                # transport model handlers, positioner queue, and gui
                self.mc.signals.progress.connect(self.progress_bar.progressBar.setValue)
                self.mc.signals.setupComplete.connect(self.run_mc)
                self.mc.signals.runComplete.connect(self.run_completed)
                self.mc.signals.runPaused.connect(self.enable_play)
                self.mc.signals.runStopped.connect(self.run_completed)
                self.mc.signals.requestMoveTo.connect(self.q_move_to)
                self.mc.signals.requestJogCW.connect(self.q_jog_cw_list)
                self.mc.signals.requestJogUp.connect(self.q_jog_up_list)
                self.mc.signals.calReady.connect(self.cal_prompt)
                # Toggle enabled for relevant transport buttons
                self.transport.playButton.setDisabled(True)
                self.transport.pauseButton.setEnabled(True)
                self.transport.stopButton.setEnabled(True)
                # Update the state of MeasurementCtrl, then create and start
                # thread for MeasurementCtrl.run() to run in
                # self.mc.progress = 0
                self.mc_state = 'SetupRunning'
                self.mc_thread = Thread(target=self.mc.run, args=(), daemon=True)
                self.mc_thread.start()
                self.pos_control.lineEdit.setText('SetupRunning')

    @qtc.pyqtSlot()
    def stop_mc(self):
        """Forces MeasurementCtrl.run() to reach a state where the thread that is
        executing it can safely exit without leaving the models of the measurement
        equipment, or the equipment itself, in an unstable or uncontrolled state.
        Leaves the system in a state such that the stopped measurement cannot be
        resumed, but a new measurement can be configured via the SettingsWindow
        and then started in a stable way.
        """

        # # Flag the thread transmitting jog requests to the positioner to stop 
        # # executing, only relevent if sweep style being used is continuous
        # self.mc.pause_jog = True
        # Flag the current run execution thread to emit the runStopped signal
        # and then break out of the execution loop 
        self.mc.stop = True
        # Wait for measurement state to be changed in the run_completed() slot
        # when the runStopped signal gets emitted
        self.transport.pauseButton.setEnabled(False)
        self.transport.stopButton.setEnabled(False)
        print('stop_mc')

    @qtc.pyqtSlot()
    def pause_mc(self):
        """Pauses MeasurementCtrl.run() in whatever step of the measurement it is
        currently in. To simplify the control of the hardware, however, if the 
        pause button is pressed while MeasurementCtrl.setup() is being run, or 
        while MeasurementCtrl is awaiting the positioner to reach a target pan
        or tilt angle after a call to Positioner.move_to(), the transport control
        model will wait until the hardware completes those actions.  This is to
        allow the hardware to reach a known and stable state, in particular a
        state that it will be able to resume from without losing any data, before
        stopping the thread of execution which they are occuring in.
        """

        # Update the state of MeasurementCtrl and toggle relevant transport buttons
        self.mc_state = 'Paused'
        self.transport.pauseButton.setDisabled(True)
        # Flag the current run execution thread to pause the current move and then
        # break out of the execution loop. Let the run thread handle terminating the
        # execution of the thread transmitting jog requests to the positioner rather
        # than setting up flag here to prevent missing data at a needed position
        # due to timing considerations.
        self.mc.pause_move = True
        self.pos_control.lineEdit.setText('Paused')

    @qtc.pyqtSlot()
    def run_mc(self):
        """Updates the transport control model to reflect that the execution of
        MeasurementCtrl.run() has reached the main execution loop for the given
        measurement type.
        """

        # Update the state of MeasurementCtrl and toggle relevant transport buttons
        self.mc_state = 'Running'
        self.transport.playButton.setEnabled(False)
        self.pos_control.lineEdit.setText('Running')

    @qtc.pyqtSlot()
    def run_completed(self):
        """Finishes out either a completed measurement or a stopped measurement
        gracefully, ensuring that it is closed out in a way that does not break
        the transport control model. Leaves the system in a stable state where so
        that a new measurement can be configured and started without conflict, and
        without leaving previously acquired resources in an uncontrolled state to
        bog the system down.
        """

        # Update the state of MeasurementCtrl and toggle relevant transport buttons
        self.mc_state = 'NotRunning'
        self.transport.playButton.setEnabled(True)
        self.transport.pauseButton.setDisabled(True)
        self.transport.stopButton.setDisabled(True)
        # Check if thread executing MeasurementCtrl.run() is still alive, if so
        # wait for it to close out before finishing out the measurement to 
        # guarentee no conflict or resource leak
        while self.mc_thread.is_alive():
            print('Thread still alive')
            sleep(0.2)
        print('Thread dead')
        # Clear the progress bar and then delete the MeasurementCtrl object
        # to finish closing out the completed or stopped measurement
        self.progress_bar.progressBar.setValue(0)
        if self.mc is not None:
            del self.mc
            self.mc = None
            print('Measurement ended, destroying MeasurementCtrl')
        self.pos_control.lineEdit.setText('NotRunning')

    def enable_play(self):
        """Re-enables the play transport button if the system gets paused"""
        self.transport.playButton.setEnabled(True)

    # ------------------------------------------------------------------------------

    # ------------------------- Positioner Control SLots ---------------------------
    # Slots for controlling the QPT Positioner via the recurring timer started
    # in the __init__() function of MyMainWindow.
    #
    # The control scheme is as follows:
    #   1. The recurring timer overflows every 120 ms, and triggers the
    #      recurring_qpt_command slot to run
    #   2. recurring_qpt_command checks a message queue to synchronize command
    #      issue requests to the QPT Positioner
    #   3. Based on the message queue contents, issues the given command to the
    #      QPT Positioner
    #
    # The message queue is a member of MyMainWindow, and is interacted with by
    # slots of MyMainWindow that can be triggered by signals, both external
    # and internal to MyMainWindow, that put a message into the message queue
    # to be handled when the recurring timer triggers recurring_qpt_command
    @qtc.pyqtSlot()
    def recurring_qpt_command(self):
        # If the positioner has not been connected, don't attempt to query
        if not self.qpt:
            return None

        # Check if message queue has any items in it, if not, catch the
        # Empty exception and send a query to get the current status of
        # the positioner
        try:
            msg = self.qpt_q.get_nowait()
        except Empty as e:
            msg = ['GetStatus']

        # Decode the message to send to the positioner
        # then trigger the packet transmission
        if msg[0] == 'Stop':
            self.qpt.move_to(0, 0, 'stop')
        elif msg[0] == 'GetStatus':
            self.qpt.get_status()

        # For jog messages, a value of 'sw' at index 1 of the list
        # indicates that the message originated from the settings window
        # so jog at full speed, otherwise msg[1] contains the speed at which to
        # jog at, and msg[2] contains the intended end coordinate of the jog
        elif msg[0] == 'JogCW':
            if msg[1] == 'sw':
                self.qpt.jog_cw(127, Coordinate(180, 0))
            else:
                self.qpt.jog_cw(msg[1], msg[2])
        elif msg[0] == 'JogCCW':
            if msg[1] == 'sw':
                self.qpt.jog_ccw(127, Coordinate(-180, 0))
            else:
                self.qpt.jog_ccw(msg[1], msg[2])
        elif msg[0] == 'JogUp':
            if msg[1] == 'sw':
                self.qpt.jog_up(127, Coordinate(0, 90))
            else:
                self.qpt.jog_up(msg[1], msg[2])
        elif msg[0] == 'JogDown':
            if msg[1] == 'sw':
                self.qpt.jog_down(127, Coordinate(0, -90))
            else:
                self.qpt.jog_down(msg[1], msg[2])

    # @qtc.pyqtSlot()
    # def q_fault_reset(self, things):
    #     if not self.qpt_q.full():
    #         self.qpt_q.put_nowait(things)

    @qtc.pyqtSlot(list)
    def q_jog_cw_list(self, source):
        if not self.qpt_q.full():
            self.qpt_q.put_nowait(['JogCW', source[1], source[2]])

    @qtc.pyqtSlot()
    def q_jog_cw(self):
        if not self.qpt_q.full():
            self.qpt_q.put_nowait(['JogCW', 'sw'])

    @qtc.pyqtSlot()
    def q_jog_ccw(self, source=['sw']):
        if not self.qpt_q.full():
            if source[0] == 'sw':
                self.qpt_q.put_nowait(['JogCCW', 'sw'])
            else:
                self.qpt_q.put_nowait(['JogCCW', source[1], source[2]])

    @qtc.pyqtSlot(list)
    def q_jog_up_list(self, source):
        if not self.qpt_q.full():
            self.qpt_q.put_nowait(['JogUp', source[1], source[2]])

    @qtc.pyqtSlot()
    def q_jog_up(self):
        if not self.qpt_q.full():
            self.qpt_q.put_nowait(['JogUp', 'sw'])

    @qtc.pyqtSlot()
    def q_jog_down(self, source=['sw']):
        if not self.qpt_q.full():
            if source[0] == 'sw':
                self.qpt_q.put_nowait(['JogDown', 'sw'])
            else:
                self.qpt_q.put_nowait(['JogDown', source[1], source[2]])

    @qtc.pyqtSlot()
    def q_move_to(self, move_cmd):
        if not self.qpt_q.full():
            self.qpt_q.put_nowait(['MoveTo'])
        # ------------------------------------------------------------------------------

    # ----------------- Positioner Connection Management Slots ---------------------
    @qtc.pyqtSlot()
    def connect_positioner(self):
        msg = qtw.QMessageBox()
        msg.setWindowTitle('Warning!')
        msg.setText('Positioner failed to connect!')
        msg.setIcon(qtw.QMessageBox.Critical)
    
        port = self.pos_control.portCombo.currentText()
        baud = self.pos_control.baudRateCombo.currentText()
    
        self.qpt = Positioner(port, int(baud))
        if self.qpt.comms.connected:
            self.pos_control.connectStatus.setChecked(True)
    
            self.qpt.signals.currentPan.connect(self.meas_disp_window.az_lcdNumber.display)
            self.qpt.signals.currentPan.connect(self.settings.pan_lcdNumber_4.display)
            self.qpt.signals.currentTilt.connect(self.meas_disp_window.el_lcdNumber.display)
            self.qpt.signals.currentTilt.connect(self.settings.tilt_lcdNumber_4.display)
    
            self.settings.right_toolButton_4.clicked.connect(self.q_jog_cw)
            self.settings.left_toolButton_4.clicked.connect(self.q_jog_ccw)
            self.settings.up_toolButton_4.clicked.connect(self.q_jog_up)
            self.settings.down_toolButton_4.clicked.connect(self.q_jog_down)
    
            self.pos_control.connectQPT.setDisabled(True)
            self.pos_control.disconnectQPT.setEnabled(True)
            self.pos_control.faultReset.setEnabled(True)
        else:
            del self.qpt
            self.qpt = None
            msg.setDetailedText(
                'Positioner timed out while trying to connect, ' +
                'verify power supply and USB are plugged in, ' +
                'and correct USB port alias and baud rate are selected.'
            )
            msg.exec_()
    
    @qtc.pyqtSlot()
    def disconnect_positioner(self):
        self.pos_control.connectStatus.setChecked(False)
        self.pos_control.connectQPT.setEnabled(True)
        self.pos_control.disconnectQPT.setDisabled(True)
        self.pos_control.faultReset.setDisabled(True)
        if self.qpt:
            del self.qpt
            self.qpt = None
    
    @qtc.pyqtSlot()
    def reset_positioner(self):
        pass
    
    # ------------------------------------------------------------------------------

    # ----------------------------- Settings Button Slot ---------------------------
    @qtc.pyqtSlot()
    def toggle_settings(self):
        if self.is_settings_open:
            self.settings.hide()
            self.is_settings_open = False
        else:
            self.settings.show()
            self.is_settings_open = True

    # ------------------------------------------------------------------------------

    # ----------------------------- Calibration Prompt Slot ---------------------------
    @qtc.pyqtSlot()
    def cal_prompt(self):
        cal_msg = qtw.QMessageBox()
        cal_msg.setIcon(qtw.QMessageBox.Warning)
        cal_msg.setStandardButtons(qtw.QMessageBox.Ok)
        cal_msg.setInformativeText("Press Ok when ready to proceed.")
        cal_msg.setWindowTitle("Calibration Instructions")
        if self.mc.open_proceed is False:
            cal_msg.setText("Please connect the OPEN calibration standard to port 1 on the VNA.")
            cal_msg.exec_()
            self.mc.open_proceed = True
        elif self.mc.short_proceed is False:
            cal_msg.setText("Please connect the SHORT calibration standard to port 1 on the VNA.")
            cal_msg.exec_()
            self.mc.short_proceed = True
        elif self.mc.load_proceed is False:
            cal_msg.setText("Please connect the LOAD calibration standard to port 1 on the VNA.")
            cal_msg.exec_()
            self.mc.load_proceed = True
        else:
            cal_msg.setText("Calibration is now complete. Please reconnect the antenna to port 1 on the VNA.")
            cal_msg.exec_()
            self.mc.cal_finished = True

    # ------------------------------------------------------------------------------

    # ----------------------------- Window CLose Event -----------------------------
    # Deal with window being closed via the 'X' button
    def closeEvent(self, event):
        event.accept()
        if self.qpt:
            self.qpt.move_to(0, 0, 'stop')
            del self.qpt
            self.qpt = None
        if self.mc:
            del self.mc
            self.mc = None


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MyMainWindow()
    sys.exit(app.exec())
