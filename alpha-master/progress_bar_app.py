""""
=============
Progress Bar
=============
"""""
import sys
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5 import uic

baseUIClass, baseUIWidget = uic.loadUiType('progress_ui.ui')


class ProgressBar(baseUIWidget, baseUIClass):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)

        # Main UI code goes here

        # ----------------------- Initialize Gui Components --------------------
        # Construct the necessary widgets for MainWindow



        # End main UI code
        self.show()


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    pb = ProgressBar()
    sys.exit(app.exec())
