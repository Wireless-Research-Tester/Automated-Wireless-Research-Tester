""""
=============
Measurement Display Widget
=============
Displays empty window
"""
import sys
from PyQt5 import QtWidgets as qtw
from gui.meas_display_form import Ui_Form

# baseUIClass, baseUIWidget = uic.loadUiType('gui/meas_display_ui.ui')


class MeasurementDisplayWindow(qtw.QWidget, Ui_Form):
# class MeasurementDisplayWindow(baseUIWidget, baseUIClass):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        # Main UI code goes here

        # End main UI code
        # self.show()


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    mdw = MeasurementDisplayWindow()
    sys.exit(app.exec())
