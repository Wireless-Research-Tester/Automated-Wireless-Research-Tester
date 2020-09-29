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
import json


baseUIClass, baseUIWidget = uic.loadUiType('settings_ui.ui')


class StorageSignals(qtc.QObject):
    settingsStored   = qtc.pyqtSignal()
    settingsClosed   = qtc.pyqtSignal()
"""End StorageSignals Class"""


class SettingsWindow(baseUIWidget, baseUIClass):


    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)


        #--------------------------- Data Members -----------------------------        
        # Bookkeeping variables
        self.settingsEmpty = True
        self.storageSignals = StorageSignals()        
        #----------------------------------------------------------------------
        

        #------------------- Initialize Signal Connections --------------------
        # Create connections for the settings window button box from
        # the Ok button (accepted) and the Cancel button (rejected)
        self.buttonBox.accepted.connect(self.settings_accepted)
        self.buttonBox.rejected.connect(self.settings_rejected)
        #----------------------------------------------------------------------        


    @qtc.pyqtSlot()
    def settings_rejected(self):
        self.settingsEmpty = True


    @qtc.pyqtSlot()
    def settings_accepted(self):
        settings_dict = {
            "linear": {
                "start": None,
                "stop": None,
                "points": None
            },
            "list": None,
            "impedance": None,
            "calibration": None,
            "averaging": None,
            "positioner_mv": None,
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

        if len(str(self.lineEdit_start_4.text())) > 0:
            settings_dict["linear"]["start"] = int(self.lineEdit_start_4.text())

        if len((self.lineEdit_stop_4.text())) > 0:
            settings_dict["linear"]["stop"] = int(self.lineEdit_stop_4.text())

        settings_dict["linear"]["points"] = int(self.comboBox_4.currentText())

        if len(self.lineEdit_list_5.text()) > 0:
            settings_dict["list"] = str(self.lineEdit_list_5.text()).split(",")
            for i in range(0, len(settings_dict["list"])):
                settings_dict["list"][i] = int(settings_dict["list"][i])

        if self.Impedance_radioButton_y_7.isChecked():
            settings_dict["impedance"] = True
        else:
            settings_dict["impedance"] = False

        if self.Calibration_radioButton_y_7.isChecked():
            settings_dict["calibration"] = True
        else:

            settings_dict["calibration"] = False

        settings_dict["averaging"] = int(self.Averaging_comboBox_7.currentText())

        if self.cont_radioButton_7.isChecked():
            settings_dict["positioner_mv"] = "continuous"
        else:
            settings_dict["positioner_mv"] = "step"

        settings_dict["offset"]["pan"] = self.pan_lcdNumber_4.intValue()
        settings_dict["offset"]["tilt"] = self.tilt_lcdNumber_4.intValue()
        settings_dict["sweep_axis"] = "pan"
        settings_dict["fixed_angle"] = self.AngleOffdoubleSpinBox_2.value()
        settings_dict["resolution"] = self.res_doubleSpinBox_7.value()
        settings_dict["gpib_addr"] = int(self.GPIB_addr_comboBox_6.currentText())
        settings_dict["alias"] = int(self.pos_alias_lineEdit_6.text())
        settings_dict["baud_rate"] = int(self.BaudRate_comboBox_6.currentText())
        with open("pivot.json", "w") as file:
            json.dump(settings_dict, file)
        self.settingsEmpty = False
        self.storageSignals.settingsStored.emit()


    def closeEvent(self, event):
        event.accept()
        self.settingsEmpty = True
        self.storageSignals.settingsClosed.emit()
"""End SettingsWindow Class"""


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    sw = SettingsWindow()
    sys.exit(app.exec())
