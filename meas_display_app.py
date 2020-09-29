""""
=============
Measurment Display Widget
=============
Displays empty window
"""""
import sys
from PyQt5 import QtWidgets as qtw, uic
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

baseUIClass, baseUIWidget = uic.loadUiType('meas_display_ui.ui')


class MeasurmentDisplayWindow(baseUIWidget, baseUIClass):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        # Main UI code goes here

        # End main UI code
        self.show()


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mdw = MeasurmentDisplayWindow()
    sys.exit(app.exec())