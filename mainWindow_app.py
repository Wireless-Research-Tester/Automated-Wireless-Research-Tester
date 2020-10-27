""""
=============
Main Window
=============
"""
import sys
import os
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5 import uic
from gui.transport_app import TransportWidget
from gui.meas_display_app import MeasurmentDisplayWindow
from gui.settingsWindow_app import SettingsWindow
from gui.progress_bar_app import ProgressBar
from gui.positioner_toolbar_app import PositionerToolBarWidget
from gui.graph_mode_toolbar_app import GraphModeToolBar
from data_processing.data_processing import DataProcessing
from measurement_ctrl.measurement_ctrl import MeasurementCtrl
from measurement_ctrl.data_storage import create_file
from measurement_ctrl.positioner import Positioner
from measurement_ctrl.integer import Coordinate
import json
from queue import Queue, Empty, Full
from time import sleep
from threading import Lock, Thread
import pyvisa as visa
from time import localtime, strftime
from measurement_ctrl.qpt_controller import *

baseUIClass, baseUIWidget = uic.loadUiType('gui/ui/main_window_ui.ui')


class MyMainWindow(baseUIWidget, baseUIClass):
    resized = qtc.pyqtSignal()

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(qtg.QIcon(':/images/gui/window_icon.png'))
        self.palette = qtg.QPalette()
        self.background_orig = qtg.QImage(':/images/gui/window_background.png')
        self.background = self.background_orig.scaledToWidth(self.width())
        self.palette.setBrush(qtg.QPalette.Window, qtg.QBrush(self.background))
        self.setPalette(self.palette)
        self.resized.connect(self.resize_window)

    # ------------------------- Initialize Gui Components ----------------------
        # Construct the necessary widgets for MainWindow
        self.transport = TransportWidget()
        self.meas_disp_window = MeasurmentDisplayWindow()
        self.settings = SettingsWindow()
        self.progress_bar = ProgressBar()
        self.pos_control = PositionerToolBarWidget()
        self.data_processing = DataProcessing()
        self.graph_mode = GraphModeToolBar()
        self.menu = self.menuBar()
        self.menu.setNativeMenuBar(False)
        self.help_menu_item = self.menu.addMenu("Help")
        self.help = self.help_menu_item.addAction("Turn Help On")
        self.docs = self.help_menu_item.addAction("Documentation")
        self.about = self.menu.addAction("About")


        # self.toolBar.setStyleSheet(
        #     "QToolButton#actionSettings:hover {background: qradialgradient(cx: 0.3, cy: -0.4, fx: 0.3, "
        #     "fy: -0.4,radius: 1.35, stop: 0 #fff, stop: 1 #bbb);}")
        # self.toolBar.setStyleSheet(
        #     "QToolButton#actionHelp:hover {background: qradialgradient(cx: 0.3, cy: -0.4, fx: 0.3, "
        #     "fy: -0.4,radius: 1.35, stop: 0 #fff, stop: 1 #bbb);}")

        # Add custom toolbars to MainWindow Widget
        self.transport_toolbar = self.addToolBar('Transport_ToolBar')
        self.meas_display_toolbar = self.addToolBar('Measurement_Display_ToolBar')
        self.progress_display_toolbar = self.addToolBar('Progress_Display_ToolBar')
        self.addToolBarBreak()
        self.graph_mode_toolbar = self.addToolBar('Graph_Mode_ToolBar')
        self.positioner_control_toolbar = self.addToolBar('Positioner_Control_ToolBar')
        self.addToolBarBreak()
        self.data_processing_toolbar = self.addToolBar('Data_Processing_ToolBar')


        # Add the custom widgets to the toolbars
        self.meas_display_toolbar.addWidget(self.meas_disp_window)
        self.transport_toolbar.addWidget(self.transport)
        self.progress_display_toolbar.addWidget(self.progress_bar)
        self.positioner_control_toolbar.addWidget(self.pos_control)
        self.data_processing_toolbar.addWidget(self.data_processing)
        self.graph_mode_toolbar.addWidget(self.graph_mode)
        self.data_processing_toolbar.hide()
    # --------------------------------------------------------------------------

    # ------------------- Initialize Gui Signal Connections --------------------
        # Create connections between Settings button on toolbar
        # and the settings window
        self.actionSettings.triggered.connect(self.toggle_settings)
        self.settings.storageSignals.settingsStored.connect(self.actionSettings.trigger)
        self.settings.storageSignals.settingsClosed.connect(self.actionSettings.trigger)

        # Create connection between button to open old data and plotting
        self.settings.open_data_Button.clicked.connect(self.open_prev_measurement)

        # Create connection between help button and help
        self.actionHelp.triggered.connect(self.toggle_help)
        self.help.triggered.connect(self.toggle_help)
        self.docs.triggered.connect(self.show_docs)
        self.about.triggered.connect(self.show_about)

        # Create connections between transport buttons and the functions
        # creating the Gui's control flow for MeasurementCtrl
        self.transport.playButton.clicked.connect(self.start_mc)
        self.transport.pauseButton.clicked.connect(self.pause_mc)
        self.transport.stopButton.clicked.connect(self.stop_mc)

        # Create connections between graph mode toolbar and data processing
        self.graph_mode.polar_rect_comboBox.currentTextChanged.connect(self.update_plot)
        self.graph_mode.s21_imp_comboBox.currentTextChanged.connect(self.update_plot)

        self.transport.pauseButton.setDisabled(True)
        self.transport.stopButton.setDisabled(True)
    # --------------------------------------------------------------------------

    # ----------------------------- Data Members -------------------------------
        self.is_settings_open = False  # Keeps track of settings window toggle
        self.is_help_on = False  # Keeps tracks of status of popups

        # MeasurementCtrl and its necessary synchronization variables
        self.mc = None  # Placeholder for MeasurementCtrl object
        self.mc_thread = None  # Placeholder for thread to run MeasurementCtrl in
        self.mc_state = 'NotRunning'  # Keeps track of current state for MeasurementCtrl

        self.qpt = None  # Placeholder for Positioner object
        self.qpt_q = Queue()  # Message queue for communication btwn Gui and qpt_thread

        self.qpt_thread = None # Placeholder for qpt_controller thread

        self.data_file = None
    # --------------------------------------------------------------------------

    # --------------- Initialize Positioner Signal Connections------------------
        rm = visa.ResourceManager()
        ports = rm.list_resources()
        for i in ports:
            if i[0:4] == 'ASRL':
                self.pos_control.portCombo_2.addItem(i)

        self.pos_control.connectStatus.setDisabled(True)

        self.pos_control.connectQPT.clicked.connect(self.connect_positioner)
        self.pos_control.disconnectQPT.clicked.connect(self.disconnect_positioner)
        self.pos_control.faultReset.clicked.connect(self.reset_positioner)

        self.pos_control.disconnectQPT.setDisabled(True)
        self.pos_control.faultReset.setDisabled(True)
    # --------------------------------------------------------------------------
        self.show()
    """End __init__() of MyMainWindow"""


    def resizeEvent(self, event):
        self.resized.emit()
        return super(MyMainWindow, self).resizeEvent(event)


    @qtc.pyqtSlot()
    def resize_window(self):
        self.background = self.background_orig.scaledToWidth(self.width())
        self.palette.setBrush(qtg.QPalette.Window, qtg.QBrush(self.background))
        self.setPalette(self.palette)


# ------------------- MeasurementCtrl Transport Model Slots --------------------
    @qtc.pyqtSlot()
    def start_mc(self):
        msg = qtw.QMessageBox()
        msg.setWindowIcon(qtg.QIcon(':/images/gui/window_icon.png'))
        msg.setIcon(qtw.QMessageBox.Warning)
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
                create_file(self.data_file)
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
                self.update_plot()

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


# ----------------- Positioner Connection Management Slots ---------------------
    @qtc.pyqtSlot()
    def connect_positioner(self):
        msg = qtw.QMessageBox()
        msg.setWindowTitle('Warning!')
        msg.setText('Positioner failed to connect!')
        msg.setIcon(qtw.QMessageBox.Critical)
        msg.setWindowIcon(qtg.QIcon(':/images/gui/window_icon.png'))

        port = self.pos_control.portCombo_2.currentText()
        baud = self.pos_control.baudRateCombo.currentText()

        self.qpt_thread = QPTMaster(self)
        self.qpt_thread.init_connection(port, baud)
        sleep(1)

        if self.qpt_thread.isRunning() and self.qpt_thread.m_connected:
            self.pos_control.connectStatus.setChecked(True)

            self.qpt_thread.signals.currentPan.connect(self.meas_disp_window.az_lcdNumber.display)
            self.qpt_thread.signals.currentPan.connect(self.settings.pan_lcdNumber_4.display)
            self.qpt_thread.signals.currentTilt.connect(self.meas_disp_window.el_lcdNumber.display)
            self.qpt_thread.signals.currentTilt.connect(self.settings.tilt_lcdNumber_4.display)

            self.settings.right_toolButton_4.clicked.connect(self.qpt_thread.Q.q_jog_cw)
            self.settings.left_toolButton_4.clicked.connect(self.qpt_thread.Q.q_jog_ccw)
            self.settings.up_toolButton_4.clicked.connect(self.qpt_thread.Q.q_jog_up)
            self.settings.down_toolButton_4.clicked.connect(self.qpt_thread.Q.q_jog_down)

            self.pos_control.connectQPT.setDisabled(True)
            self.pos_control.disconnectQPT.setEnabled(True)
            self.pos_control.faultReset.setEnabled(True)
        else:
            del self.qpt_thread
            self.qpt_thread = None
            msg.setDetailedText(
                'Positioner timed out while trying to connect, ' +
                'verify power supply and USB are plugged in, ' +
                'and correct USB port alias and baud rate are selected.'
            )
            msg.exec_()

    @qtc.pyqtSlot()
    def disconnect_positioner(self):
        self.qpt_thread.disconnect()
        self.pos_control.connectStatus.setChecked(False)
        self.pos_control.connectQPT.setEnabled(True)
        self.pos_control.disconnectQPT.setDisabled(True)
        self.pos_control.faultReset.setDisabled(True)
        if self.qpt_thread:
            del self.qpt_thread
            self.qpt_thread = None

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
            self.actionSettings.setChecked(False)
        else:
            self.settings.show()
            self.is_settings_open = True
            self.actionSettings.setChecked(True)
# ------------------------------------------------------------------------------


# ----------------------------- Help Button Toggle Slog ------------------------
    @qtc.pyqtSlot()
    def toggle_help(self):
        if self.is_help_on:
            # Turning off help, so disable tooltips
            self.actionHelp.setText('Help Off')
            self.actionHelp.setChecked(False)
            self.help.setText('Turn Help On')
            self.is_help_on = False

            self.settings.start_label_4.setToolTip('')
            self.settings.lineEdit_start_4.setToolTip('')
            self.settings.stop_label_4.setToolTip('')
            self.settings.lineEdit_stop_4.setToolTip('')
            self.settings.points_label_4.setToolTip('')
            self.settings.comboBox_4.setToolTip('')
            self.settings.list_label_5.setToolTip('')
            self.settings.lineEdit_list_5.setToolTip('')
            self.settings.Impedance_label_7.setToolTip('')
            self.settings.Impedance_radioButton_n_7.setToolTip('')
            self.settings.Impedance_radioButton_y_7.setToolTip('')
            self.settings.Calibration_label_7.setToolTip('')
            self.settings.Calibration_radioButton_y_7.setToolTip('')
            self.settings.Calibration_radioButton_n_7.setToolTip('')
            self.settings.Averaging_label_7.setToolTip('')
            self.settings.Averaging_comboBox_7.setToolTip('')
            self.settings.posMov_label_7.setToolTip('')
            self.settings.cont_radioButton_7.setToolTip('')
            self.settings.discrete_radioButton_7.setToolTip('')
            self.settings.res_label_7.setToolTip('')
            self.settings.res_doubleSpinBox_7.setToolTip('')
            self.settings.GPIB_addr_label_6.setToolTip('')
            self.settings.GPIB_addr_comboBox_6.setToolTip('')
            self.settings.sweep_elevation_label_6.setToolTip('')
            self.settings.sweep_elevation_spinBox.setToolTip('')
            self.settings.label.setToolTip('')
            self.settings.dir_label.setToolTip('')
            self.settings.dir_Button.setToolTip('')
            self.transport.playButton.setToolTip('')
            self.progress_bar.progressBar.setToolTip('')
            self.meas_disp_window.az_lcdNumber.setToolTip('')
            self.meas_disp_window.el_lcdNumber.setToolTip('')
            self.pos_control.portLabel_2.setToolTip('')
            self.pos_control.portCombo_2.setToolTip('')
            self.pos_control.label_2.setToolTip('')
            self.pos_control.lineEdit.setToolTip('')
            self.pos_control.faultReset.setToolTip('')
            self.data_processing.sc.setToolTip('')

        else:
            # Turning on help, so enable tooltips
            self.actionHelp.setText('Help On')
            self.actionHelp.setChecked(True)
            self.help.setText('Turn Help Off')
            self.is_help_on = True

            # settings_ui popups
            self.settings.start_label_4.setToolTip('Start frequency for sweep')
            self.settings.lineEdit_start_4.setToolTip('Start frequency for sweep')
            self.settings.stop_label_4.setToolTip('Stop frequency for sweep')
            self.settings.lineEdit_stop_4.setToolTip('Stop frequency for sweep')
            self.settings.points_label_4.setToolTip('Number of data points for frequency sweep')
            self.settings.comboBox_4.setToolTip('Number of data points for frequency sweep')
            self.settings.list_label_5.setToolTip('Frequency list of measurements')
            self.settings.lineEdit_list_5.setToolTip('Frequency list of measurements')
            self.settings.Impedance_label_7.setToolTip('Measure AUT impedance\n' + '(Requires calibration)')
            self.settings.Impedance_radioButton_n_7.setToolTip('Measure AUT impedance\n' + '(Requires calibration)')
            self.settings.Impedance_radioButton_y_7.setToolTip('Measure AUT impedance\n' + '(Requires calibration)')
            self.settings.Calibration_label_7.setToolTip('Perform S11 single port calibration')
            self.settings.Calibration_radioButton_y_7.setToolTip('Perform S11 single port calibration')
            self.settings.Calibration_radioButton_n_7.setToolTip('Perform S11 single port calibration')
            self.settings.Averaging_label_7.setToolTip('Number of measurements for VNA to average for each measurement')
            self.settings.Averaging_comboBox_7.setToolTip('Number of measurements for VNA to average for each measurement')
            self.settings.posMov_label_7.setToolTip('Hover over movement options for more details')
            self.settings.cont_radioButton_7.setToolTip('Measurements collected with positioner in continuous movement\n' +
                                               '(Requires slower rotation speed)')
            self.settings.discrete_radioButton_7.setToolTip('Measurements made with positioner stopped at each azimuth angle')
            self.settings.res_label_7.setToolTip('Azimuth spacing between measurement points')
            self.settings.res_doubleSpinBox_7.setToolTip('Azimuth spacing between measurement points')
            self.settings.GPIB_addr_label_6.setToolTip('GPIB address for VNA')
            self.settings.GPIB_addr_comboBox_6.setToolTip('GPIB address for VNA')
            self.settings.sweep_elevation_label_6.setToolTip('AUT elevation angle')
            self.settings.sweep_elevation_spinBox.setToolTip('AUT elevation angle')
            self.settings.label.setToolTip('Directory for project data files')
            self.settings.dir_label.setToolTip('Directory for project data files')
            self.settings.dir_Button.setToolTip('Directory for project data files')

            # transport_ui popups
            self.transport.playButton.setToolTip('Begin measurement')
            # meas_display_ui popups
            self.meas_disp_window.az_lcdNumber.setToolTip('Current positioner azimuth')
            self.meas_disp_window.el_lcdNumber.setToolTip('Current positioner elevation')
            # progress_ui popups
            self.progress_bar.progressBar.setToolTip('Measurement progress')
            # pos_control_ui popups
            self.pos_control.portLabel_2.setToolTip('Serial port for positioner')
            self.pos_control.portCombo_2.setToolTip('Serial port for positioner')
            self.pos_control.label_2.setToolTip('Current state of the measurement')
            self.pos_control.lineEdit.setToolTip('Current state of the measurement')
            self.pos_control.faultReset.setToolTip('Explain what this does')
            # data_processing popups
            self.data_processing.sc.setToolTip('Click on the check boxes in the legend\nto display/hide frequencies')
# ------------------------------------------------------------------------------

# ----------------------------- Show Documentation Slot ------------------------
    @qtc.pyqtSlot()
    def show_docs(self):
        if os.path.exists('README.md'):
            os.startfile('README.md')
        else:
            msg = qtw.QMessageBox()
            msg.setIcon(qtw.QMessageBox.Critical)
            msg.setWindowIcon(qtg.QIcon(':/images/gui/window_icon.png'))
            msg.setStandardButtons(qtw.QMessageBox.Ok)
            msg.setText('User Manual.pdf was not found within program directory')
            msg.setWindowTitle('Error')
            msg.exec_()
# ------------------------------------------------------------------------------


# ----------------------------- Calibration Prompt Slot ------------------------
    @qtc.pyqtSlot()
    def cal_prompt(self):
        cal_msg = qtw.QMessageBox()
        cal_msg.setIcon(qtw.QMessageBox.Warning)
        cal_msg.setWindowIcon(qtg.QIcon(':/images/gui/window_icon.png'))
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


# ----------------------------- Open Previous Measurement-----------------------
    def open_prev_measurement(self):
        filename = qtw.QFileDialog.getOpenFileName(self, 'Open Previous Measurement Data',
                                                   'C:/', "CSV File (*.csv)")[0]
        if len(filename) > 0:
            self.data_file = filename
            self.update_plot()
            self.toggle_settings()
# ------------------------------------------------------------------------------


# -------------------- Change displayed data and format of plot-----------------
    def update_plot(self):
        if self.data_file is not None:
            if self.graph_mode.polar_rect_comboBox.currentText() == 'Polar':
                if self.graph_mode.s21_imp_comboBox.currentText() == 'S21':
                    self.data_processing_toolbar.clear()
                    del self.data_processing
                    self.data_processing = DataProcessing()
                    self.data_processing_toolbar.addWidget(self.data_processing)
                    self.data_processing.begin_measurement(self.data_file, polar=True, s11=False)
                else:
                    self.data_processing_toolbar.clear()
                    del self.data_processing
                    self.data_processing = DataProcessing()
                    self.data_processing_toolbar.addWidget(self.data_processing)
                    self.data_processing.begin_measurement(self.data_file, polar=False, s11=True)
                    self.graph_mode.polar_rect_comboBox.setCurrentIndex(1)
            else:
                if self.graph_mode.s21_imp_comboBox.currentText() == 'S21':
                    self.data_processing_toolbar.clear()
                    del self.data_processing
                    self.data_processing = DataProcessing()
                    self.data_processing_toolbar.addWidget(self.data_processing)
                    self.data_processing.begin_measurement(self.data_file, polar=False, s11=False)
                else:
                    self.data_processing_toolbar.clear()
                    del self.data_processing
                    self.data_processing = DataProcessing()
                    self.data_processing_toolbar.addWidget(self.data_processing)
                    self.data_processing.begin_measurement(self.data_file, polar=False, s11=True)
            if self.is_help_on:
                self.data_processing.sc.setToolTip(
                    'Click on the check boxes in the legend\nto display/hide frequencies')
            self.data_processing_toolbar.show()
# ------------------------------------------------------------------------------


# -------------------------------- About window --------------------------------
    @qtc.pyqtSlot()
    def show_about(self):
        msg = qtw.QMessageBox()
        msg.setWindowTitle('About')
        msg.setText('This software was created by NC State University students as part of their senior design project.'
                    '\n\nTeam members:\n    Thomas Hoover\n    Austin Langebeck-Fissinger\n    Eric Li'
                    '\n    Maria Samia\n    Stephen Wood')
        msg.setWindowIcon(qtg.QIcon(':/images/gui/window_icon.png'))
        msg.exec_()
#-------------------------------------------------------------------------------


# ----------------------------- Window Close Event -----------------------------
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
