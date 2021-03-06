""""
=============
Settings Window
=============
"""
import sys
from PyQt5 import QtWidgets as qtw, uic
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc
from gui.settings_form import Ui_Form
from json import dump
import re

baseUIClass, baseUIWidget = uic.loadUiType('gui/settings_ui.ui')


class StorageSignals(qtc.QObject):
    settingsStored = qtc.pyqtSignal()
    settingsClosed = qtc.pyqtSignal()
"""End StorageSignals Class"""


# class SettingsWindow(qtw.QWidget, Ui_Form):
class SettingsWindow(baseUIWidget, baseUIClass):
    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(qtg.QIcon(':/images/gui/window_icon.png'))

        # --------------------------- Data Members -----------------------------
        # Bookkeeping variables
        self.settings_empty = True
        self.storageSignals = StorageSignals()
        self.project_dir = None
        self.pivot_file = None
        # ----------------------------------------------------------------------

        # ------------------- Initialize Signal Connections --------------------
        # Create connections for the settings window button box from
        # the Ok button (accepted) and the Cancel button (rejected)
        self.buttonBox.accepted.connect(self.settings_check)
        self.buttonBox.rejected.connect(self.settings_rejected)
        self.dir_Button.clicked.connect(self.get_project_dir)
        self.toolButton.clicked.connect(self.import_list)
        self.Impedance_radioButton_y_7.toggled.connect(self.toggle_cal)
        # ----------------------------------------------------------------------

        # -------------------Adding Popup Tips----------------------------------

        # ----------------------------------------------------------------------

    @qtc.pyqtSlot()
    def get_project_dir(self):
        """Saves the project directory path and settings file path.
        Also displays the selected directory."""
        temp = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if temp != '':
            self.project_dir = temp
            self.dir_label.setText(self.project_dir)
            self.pivot_file = self.project_dir + '/pivot.json'

    @qtc.pyqtSlot()
    def import_list(self):
        """Parses a .txt or .csv file where frequencies are separated
        by a comma or a newline (or both). Result is displayed in the text box."""
        filename = QFileDialog.getOpenFileName(self, 'Import list','C:\\',"Text Files (*.txt *.csv)")[0]
        if len(filename) > 0:
            with open(filename, 'r') as f:
                self.lineEdit_list_5.setText(f.read().replace(',\n', ',').replace('\n',','))

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
        msg.setWindowIcon(qtg.QIcon(':/images/gui/window_icon.png'))
        # msg.exec_() shows pop-up error

        # error checking for the inputs
        if self.project_dir is None:
            msg.setDetailedText("Please select a project directory.")
            msg.exec_()
        elif len(self.lineEdit_list_5.text()) == 0:
            if (len(self.lineEdit_stop_4.text()) > 0 and len(self.lineEdit_start_4.text()) > 0 and
                    self.lineEdit_stop_4.text().isnumeric() and self.lineEdit_start_4.text().isnumeric()):
                self.settings_accepted()
            else:
                msg.setDetailedText("Invalid start/stop frequency.")
                msg.exec_()
        # regular expression that reads the pattern "1,2,3" "1, 2, 3" "1 ,2 ,3"
        elif re.search("^((\s)*(([0-9]*\.([0-9]+))|[0-9]+)(\s)*)(,(\s)*(([0-9]*\.([0-9]+))|[0-9]+)(\s)*){0,29}$",
                       self.lineEdit_list_5.text()):
            temp_ar = str(self.lineEdit_list_5.text()).split(",")
            if len(self.lineEdit_stop_4.text()) == 0 and len(self.lineEdit_start_4.text()) == 0:
                # check if list array values are [0.03, 6000] MHz
                if self.traverse(temp_ar, 0.03, 6000): 
                    self.settings_accepted()
                else:
                    msg.setDetailedText("Some frequencies in the list are out of range.")
                    msg.exec_()
            else:
                msg.setDetailedText("Both linear and list frequency have inputs")
                msg.exec_()
        else:
            msg.setDetailedText("Please enter list frequencies as numerical values separated by commas.\n" + "Use format 1, 2, 3")
            msg.exec_()

    @qtc.pyqtSlot()
    # fill the json from the settings ui
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
            settings_dict["linear"]["start"] = float(self.lineEdit_start_4.text())
            settings_dict["linear"]["stop"] = float(self.lineEdit_stop_4.text())
            settings_dict["linear"]["points"] = int(self.comboBox_4.currentText())

        if len(self.lineEdit_list_5.text()) > 0:
            settings_dict["list"] = str(self.lineEdit_list_5.text()).split(",")
            for i in range(0, len(settings_dict["list"])):
                settings_dict["list"][i] = float(settings_dict["list"][i])
            settings_dict["list"].sort()
            
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
        with open(self.pivot_file, "w") as file:
            dump(settings_dict, file)
        self.settings_empty = False
        self.storageSignals.settingsStored.emit()

    def closeEvent(self, event):
        event.accept()
        self.settings_empty = True
        self.storageSignals.settingsClosed.emit()

    def traverse(self, temp_list, low, high):
        # change list to float
        for i in range(0, len(temp_list)):  
            temp_list[i] = float(temp_list[i])
        # traverse in the list and check bounds
        for x in temp_list:  
            if x < low or x > high: 
                return False
        return True

    def toggle_cal(self):
        """In the event when impedance is toggled to yes,
        calibration will automatically toggle to yes as well."""
        if self.Impedance_radioButton_y_7.isChecked():
            self.Calibration_radioButton_y_7.setChecked(True)


"""End SettingsWindow Class"""


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    sw = SettingsWindow()
    sys.exit(app.exec())
