""""
=============
Positioner Toolbar widget
=============
Displays empty window
"""""
import sys

import pyvisa as visa
from PyQt5 import QtWidgets as qtw, uic
from PyQt5 import QtGui as qtg
from PyQt5 import QtCore as qtc

from positioner import Positioner

baseUIClass, baseUIWidget = uic.loadUiType('pos_controls_tb_ui.ui')


class PositionerToolBarWidget(baseUIWidget, baseUIClass):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        # Main UI code goes here
        # # --------------- Initialize Positioner Signal Connections------------------
        rm = visa.ResourceManager()
        ports = rm.list_resources()
        for i in ports:
            if i[0:4] == 'ASRL':
                self.portCombo.addItem(i)
        #
        self.connectStatus.setDisabled(True)
        #
        self.connectQPT.clicked.connect(self.connect_positioner)
        self.disconnectQPT.clicked.connect(self.disconnect_positioner)
        self.faultReset.clicked.connect(self.reset_positioner)
        #
        self.disconnectQPT.setDisabled(True)
        self.faultReset.setDisabled(True)
        #
        # self.timer = qtc.QTimer()
        # self.timer.setInterval(120)
        # self.timer.timeout.connect(self.recurring_qpt_command)
        # self.timer.start()
        # # --------------------------------------------------------------------------
        # End main UI code
        self.show()

    # ----------------- Positioner Connection Management Slots ---------------------
    @qtc.pyqtSlot()
    def connect_positioner(self):
        msg = qtw.QMessageBox()
        msg.setWindowTitle('Warning!')
        msg.setText('Positioner failed to connect!')
        msg.setIcon(qtw.QMessageBox.Critical)

        port = self.portCombo.currentText()
        baud = self.baudRateCombo.currentText()

        self.qpt = Positioner(port, int(baud))
        if self.qpt.comms.connected:
            self.connectStatus.setChecked(True)

            self.qpt.signals.currentPan.connect(self.meas_disp_window.az_lcdNumber.display)
            self.qpt.signals.currentPan.connect(self.s.pan_lcdNumber_4.display)
            self.qpt.signals.currentTilt.connect(self.meas_disp_window.el_lcdNumber.display)
            self.qpt.signals.currentTilt.connect(self.s.tilt_lcdNumber_4.display)

            self.s.right_toolButton_4.clicked.connect(self.q_jog_cw)
            self.s.left_toolButton_4.clicked.connect(self.q_jog_ccw)
            self.s.up_toolButton_4.clicked.connect(self.q_jog_up)
            self.s.down_toolButton_4.clicked.connect(self.q_jog_down)

            self.connectQPT.setDisabled(True)
            self.disconnectQPT.setEnabled(True)
            self.faultReset.setEnabled(True)
        else:
            del self.qpt
            self.qpt = None
            msg.setDetailedText(
                'Positioner timed out while trying to connect, ' +
                'verify power supply and USB are plugged in, ' +
                'and correct USB port alias and baud rate are selected.'
            )
            msg.exec_()

    @qtc.pyqtSlot()
    def disconnect_positioner(self):
        self.connectStatus.setChecked(False)
        self.connectQPT.setEnabled(True)
        self.disconnectQPT.setDisabled(True)
        self.faultReset.setDisabled(True)
        if self.qpt:
            del self.qpt
            self.qpt = None

    @qtc.pyqtSlot()
    def reset_positioner(self):
        pass

    # ------------------------------------------------------------------------------


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    ptbw = PositionerToolBarWidget()
    sys.exit(app.exec())
