""""
=============
Settings Window
=============
"""
import sys
from PyQt5 import QtWidgets as qtw
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from PyQt5 import uic
# from settingsWindow_form import Ui_SettingsWindow  # Import qtdesigner object
import json
import re

baseUIClass, baseUIWidget = uic.loadUiType('settings_ui.ui')


class StorageSignals(qtc.QObject):
    settingsStored = qtc.pyqtSignal()
    settingsClosed = qtc.pyqtSignal()
"""End StorageSignals Class"""


class SettingsWindow(baseUIWidget, baseUIClass):
    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)

        # --------------------------- Data Members -----------------------------
        # Bookkeeping variables
        self.settings_empty = True
        self.storageSignals = StorageSignals()
        # ----------------------------------------------------------------------

        # ------------------- Initialize Signal Connections --------------------
        # Create connections for the settings window button box from
        # the Ok button (accepted) and the Cancel button (rejected)
        self.buttonBox.accepted.connect(self.settings_check)
        self.buttonBox.rejected.connect(self.settings_rejected)
        # ----------------------------------------------------------------------


    @qtc.pyqtSlot()
    def settings_rejected(self):
        self.settings_empty = True


    @qtc.pyqtSlot()
    def settings_check(self):
        # properties of popup
        msg = QMessageBox()
        msg.setWindowTitle("Warning!")
        msg.setText("Input Error")
        msg.setIcon(QMessageBox.Critical)
        # msg.exec_() # shows pop-up error

        if len(self.lineEdit_list_5.text()) == 0:
            if (len(self.lineEdit_stop_4.text()) > 0 and len(self.lineEdit_start_4.text()) > 0 and
                    self.lineEdit_stop_4.text().isnumeric() and self.lineEdit_start_4.text().isnumeric()):
                self.settings_accepted()
            else:
                msg.setDetailedText("Invalid start/stop frequency.")
                msg.exec_()
        elif re.search("^(( )*(([0-9]*\.([0-9]+))|[0-9]+))(,( )*(([0-9]*\.([0-9]+))|[0-9]+)){0,29}$",
                       self.lineEdit_list_5.text()):
            temp_ar = str(self.lineEdit_list_5.text()).split(",")

            if self.traverse(temp_ar, 0.03, 6000):  # check if list array values are [0.03, 6000] MHz
                self.settings_accepted()
            else:
                msg.setDetailedText("Some frequencies in the list are out of range.")
                msg.exec_()
        else:
            msg.setDetailedText("Please enter list frequencies as numerical values separated by commas.")
            msg.exec_()


    @qtc.pyqtSlot()
    def settings_accepted(self):
        settings_dict = {
            "linear": {
                "start": None,
                "stop": None,
                "points": None
            },
            "list": None,
            "impedance": False,
            "calibration": False,
            "averaging": None,
            "positioner_mv": "step",
            "offset": {
                "pan": None,
                "tilt": None
            },
            "sweep_axis": None,
            "fixed_angle": None,
            "resolution": None,
            "gpib_addr": None,
            "alias": None,
            "baud_rate": None
        }

        if len(self.lineEdit_stop_4.text()) > 0 and len(self.lineEdit_start_4.text()) > 0:
            settings_dict["linear"]["start"] = int(self.lineEdit_start_4.text())
            settings_dict["linear"]["stop"] = int(self.lineEdit_stop_4.text())
            settings_dict["linear"]["points"] = int(self.comboBox_4.currentText())

        if len(self.lineEdit_list_5.text()) > 0:
            settings_dict["list"] = str(self.lineEdit_list_5.text()).split(",")
            for i in range(0, len(settings_dict["list"])):
                settings_dict["list"][i] = int(settings_dict["list"][i])

        if self.Impedance_radioButton_y_7.isChecked():
            settings_dict["impedance"] = True

        if self.Calibration_radioButton_y_7.isChecked():
            settings_dict["calibration"] = True

        settings_dict["averaging"] = int(self.Averaging_comboBox_7.currentText())

        if self.cont_radioButton_7.isChecked():
            settings_dict["positioner_mv"] = "continuous"

        settings_dict["offset"]["pan"] = 0 #self.pan_lcdNumber_4.intValue()
        settings_dict["offset"]["tilt"] = 0 #self.tilt_lcdNumber_4.intValue()
        settings_dict["sweep_axis"] = "pan"
        settings_dict["fixed_angle"] = self.sweep_elevation_spinBox.value()
        settings_dict["resolution"] = self.res_doubleSpinBox_7.value()
        settings_dict["gpib_addr"] = int(self.GPIB_addr_comboBox_6.currentText())
        with open("pivot.json", "w") as file:
            json.dump(settings_dict, file)
        self.settings_empty = False
        self.storageSignals.settingsStored.emit()


    def closeEvent(self, event):
        event.accept()
        self.settings_empty = True
        self.storageSignals.settingsClosed.emit()


    def traverse(self, temp_list, low, high):
        for i in range(0, len(temp_list)):  # change list to integer
            temp_list[i] = float(temp_list[i])
        for x in temp_list:  # traverse in the list
            if x < low or x > high:  # condition check
                return False
        return True
"""End SettingsWindow Class"""


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    sw = SettingsWindow()
    sys.exit(app.exec())