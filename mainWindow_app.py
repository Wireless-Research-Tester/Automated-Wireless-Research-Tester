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
import settingsWindow_app
import measurement_ctrl as mc
import json

baseUIClass, baseUIWidget = uic.loadUiType('main_window_ui.ui')


class MyMainWindow(baseUIWidget, baseUIClass):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)

        # Main UI code goes here

        """Defining variables"""
        self.meas_in_progress = False

        """ Adding custom toolbars """
        transport_toolbar = self.addToolBar('Transport_ToolBar')
        meas_display_toolbar = self.addToolBar('Measurement_Display_ToolBar')

        """Add Instances of custom widgets"""
        self.transport = TransportWidget()
        self.meas_disp_window = MeasurmentDisplayWindow()

        """Add widgets to the toolbars"""
        meas_display_toolbar.addWidget(self.meas_disp_window)
        transport_toolbar.addWidget(self.transport)

        """Connecting settings button to settings window"""
        self.toolBar.actionTriggered.connect(self.show_settings)

        """Connecting transport buttons to meas_ctrl functions"""
        self.transport.playButton.clicked.connect(self.start_mc)
        self.transport.pauseButton.clicked.connect(self.pause_mc)
        self.transport.stopButton.clicked.connect(self.stop_mc)

        # End main UI code

        self.show()

    def show_settings(self):
        self.s = settingsWindow_app.SettingsWindow()
        self.s.show()

    def start_mc(self):
        if self.meas_in_progress:
            self.meas_ctrl.run()
        else:
            if self.s.settings_empty == False:
                with open('pivot.json') as file:
                    dict = json.load(file)
                self.meas_ctrl = mc.meas_ctrl(dict)
                self.meas_ctrl.signals.current_pan.connect(self.meas_disp_window.az_lcdNumber.display)
                self.meas_ctrl.signals.current_tilt.connect(self.meas_disp_window.el_lcdNumber.display)
                self.meas_ctrl.setup()
                self.meas_in_progress = True
                self.meas_ctrl.run()

    def stop_mc(self):
        self.meas_ctrl.halt()
        self.meas_in_progress = False

    def pause_mc(self):
        self.meas_ctrl.halt()
        self.meas_in_progress = False


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MyMainWindow()
    sys.exit(app.exec())
