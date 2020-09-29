""""
=============
Main Window
=============
"""""
import sys
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5 import uic
from transport_app import TransportWidget
from meas_display_app import MeasurmentDisplayWindow
from settingsWindow_app import SettingsWindow
from progress_bar_app import ProgressBar
from measurement_ctrl import MeasurementCtrl
import json
from queue import Queue, Empty, Full
from time import time, sleep
from threading import Lock, Thread

baseUIClass, baseUIWidget = uic.loadUiType('main_window_ui.ui')


class MyMainWindow(baseUIWidget, baseUIClass):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)

        # --------------------------- Data Members -----------------------------
        # Bookkeeping variables
        self.meas_in_progress = False  # Indicates if measurement is in progress (could be actively running or paused)
        self.meas_running = False  # Indicates if measurement is actively running
        self.is_settings_open = False  # Keeps track of settings window toggle

        # MeasurementCtrl and its necessary synchronization variables
        self.mc = None  # Placeholder for MeasurementCtrl object
        self.mc_q = Queue()  # Message queue for communication btwn Gui and mc_thread
        self.mc_lock = Lock()  # Lock for synchronizing start/pause/resume
        self.mc_thread = None  # Placeholder for thread to run MeasurementCtrl in
        # ----------------------------------------------------------------------

        # ----------------------- Initialize Gui Components --------------------
        # Construct the necessary widgets for MainWindow
        self.transport = TransportWidget()
        self.meas_disp_window = MeasurmentDisplayWindow()
        self.s = SettingsWindow()
        self.progress_bar = ProgressBar()

        # Add custom toolbars to MainWindow Widget
        transport_toolbar = self.addToolBar('Transport_ToolBar')
        meas_display_toolbar = self.addToolBar('Measurement_Display_ToolBar')
        progress_display_toolbar = self.addToolBar('Progress_Display_ToolBar')

        # Add the custom widgets to the toolbars
        meas_display_toolbar.addWidget(self.meas_disp_window)
        transport_toolbar.addWidget(self.transport)
        progress_display_toolbar.addWidget(self.progress_bar)
        # ----------------------------------------------------------------------

        # ------------------- Initialize Signal Connections --------------------
        # Create connections between Settings button on toolbar
        # and the s
        self.actionSettings.triggered.connect(self.toggle_settings)
        self.s.storageSignals.settingsStored.connect(self.actionSettings.trigger)
        self.s.storageSignals.settingsClosed.connect(self.actionSettings.trigger)

        # Create connections between transport buttons and the functions
        # creating the Gui's control flow for MeasurementCtrl
        self.transport.playButton.clicked.connect(self.start_mc)
        self.transport.pauseButton.clicked.connect(self.pause_mc)
        self.transport.stopButton.clicked.connect(self.stop_mc)
        # ----------------------------------------------------------------------
        self.show()

    @qtc.pyqtSlot()
    def toggle_settings(self):
        if self.is_settings_open:
            self.s.hide()
            self.is_settings_open = False
        else:
            self.s.show()
            self.is_settings_open = True

    @qtc.pyqtSlot()
    def start_mc(self):
        # Resumes an existing in progress measurement
        if self.meas_in_progress and ~self.meas_running:
            self.meas_running = True
            self.mc.run()

        # Start a new measurement
        elif ~self.meas_in_progress and ~self.meas_running:
            if ~self.s.settingsEmpty:
                with open('pivot.json') as file:
                    dict = json.load(file)
                self.mc = MeasurementCtrl(dict)
                self.meas_in_progress = True
                self.meas_running = True

                self.mc.qpt.signals.currentPan.connect(self.meas_disp_window.az_lcdNumber.display)
                self.mc.qpt.signals.currentTilt.connect(self.meas_disp_window.el_lcdNumber.display)
                self.mc.signals.setupComplete.connect(self.run_mc)
                self.mc.signals.runComplete.connect(self.run_completed)

                self.setup_mc()
            else:
                print("Need to submit settings first before starting measurements")

    @qtc.pyqtSlot()
    def stop_mc(self):
        # Quiescent state, nothing to do, call run_completed guarentee system
        # that system enters known state regardless, acts as user triggered reset
        # of the system
        if ~self.meas_in_progress and ~self.meas_running:
            self.run_completed()
        # else if  self.meas_in_progress and ~self.meas_running:

        # self.mc.halt()
        self.meas_in_progress = False
        self.meas_running = False

    @qtc.pyqtSlot()
    def pause_mc(self):
        """Pauses current measurement in whatever step of the measurement it is
        currently in. As a simplification, however, it will not allow the user
        to pause during the setup of MeasurementCtrl, but instead will allow
        setup() to run to completion, but will """

        self.mc.halt()
        self.meas_in_progress = True
        self.meas_running = False

    def setup_mc(self):
        s_thread = Thread(target=self.mc.setup, args=(), daemon=True)
        s_thread.start()
        return s_thread

    @qtc.pyqtSlot()
    def run_mc(self):
        r_thread = Thread(target=self.mc.run, args=(), daemon=True)
        r_thread.start()
        return r_thread

    @qtc.pyqtSlot()
    def run_completed(self):
        print('Measurement has been successfully completed')
        if self.mc is not None:
            del self.mc
            self.mc = None
        self.meas_in_progress = False
        self.meas_running = False


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MyMainWindow()
    sys.exit(app.exec())
