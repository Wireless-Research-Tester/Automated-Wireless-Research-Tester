""""
=============
Settings Window
=============
"""""
import sys
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5 import uic
# from settingsWindow_form import Ui_SettingsWindow  # Import qtdesigner object

baseUIClass, baseUIWidget = uic.loadUiType('settings_ui.ui')


class SettingsWindow(baseUIWidget, baseUIClass):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        # Main UI code goes here

        # End main UI code
        self.show()


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    sw = SettingsWindow()
    sys.exit(app.exec())
