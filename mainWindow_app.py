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
# from settingsWindow_form import Ui_SettingsWindow  # Import qtdesigner object

baseUIClass, baseUIWidget = uic.loadUiType('main_window_ui.ui')


class MyMainWindow(baseUIWidget, baseUIClass):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)

        # Main UI code goes here

        """ Adding custom toolbars """
        transport_toolbar = self.addToolBar('Transport_ToolBar')
        meas_display_toolbar = self.addToolBar('Measurement_Display_ToolBar')

        """Add Instances of custom widgets"""
        self.transport = TransportWidget()
        self.meas_disp_window = MeasurmentDisplayWindow()

        """Add widgets to the toolbars"""
        meas_display_toolbar.addWidget(self.meas_disp_window)
        transport_toolbar.addWidget(self.transport)

        # End main UI code

        self.show()


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mw = MyMainWindow()
    sys.exit(app.exec())
