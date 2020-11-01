# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'transport_ui.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(172, 81)
        Form.setMinimumSize(QtCore.QSize(172, 81))
        Form.setMaximumSize(QtCore.QSize(200, 16777215))
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame = QtWidgets.QFrame(Form)
        self.frame.setMinimumSize(QtCore.QSize(148, 0))
        self.frame.setMaximumSize(QtCore.QSize(250, 16777215))
        self.frame.setFrameShape(QtWidgets.QFrame.Box)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.frame)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pauseButton = QtWidgets.QPushButton(self.frame)
        self.pauseButton.setMinimumSize(QtCore.QSize(20, 20))
        self.pauseButton.setMaximumSize(QtCore.QSize(40, 40))
        self.pauseButton.setStyleSheet("QPushButton {\n"
"     qproperty-icon: url(:/images/gui/pngegg.png);\n"
"}\n"
"\n"
"QPushButton {\n"
"    color: #333;\n"
"    border: 2px solid #555;\n"
"    border-radius: 20px;\n"
"    border-style: outset;\n"
"    background: qradialgradient(\n"
"        cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,\n"
"        radius: 1.35, stop: 0 #fff, stop: 1 #888\n"
"        );\n"
"    padding: 5px;\n"
"    }\n"
"\n"
"QPushButton:hover {\n"
"    background: qradialgradient(\n"
"        cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,\n"
"        radius: 1.35, stop: 0 #fff, stop: 1 #bbb\n"
"        );\n"
"    }\n"
"\n"
"QPushButton:pressed {\n"
"    border-style: inset;\n"
"    background: qradialgradient(\n"
"        cx: 0.4, cy: -0.1, fx: 0.4, fy: -0.1,\n"
"        radius: 1.35, stop: 0 #fff, stop: 1 #ddd\n"
"        );\n"
"    }")
        self.pauseButton.setText("")
        self.pauseButton.setObjectName("pauseButton")
        self.transportBtnGroup = QtWidgets.QButtonGroup(Form)
        self.transportBtnGroup.setObjectName("transportBtnGroup")
        self.transportBtnGroup.addButton(self.pauseButton)
        self.horizontalLayout_2.addWidget(self.pauseButton)
        self.playButton = QtWidgets.QPushButton(self.frame)
        self.playButton.setMinimumSize(QtCore.QSize(20, 20))
        self.playButton.setMaximumSize(QtCore.QSize(40, 40))
        self.playButton.setStyleSheet("QPushButton {\n"
"     qproperty-icon: url(:/images/gui/play.png);\n"
"}\n"
"QPushButton {\n"
"    color: #333;\n"
"    border: 2px solid #555;\n"
"    border-radius: 20px;\n"
"    border-style: outset;\n"
"    background: qradialgradient(\n"
"        cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,\n"
"        radius: 1.35, stop: 0 #fff, stop: 1 #888\n"
"        );\n"
"    padding: 5px;\n"
"    }\n"
"\n"
"QPushButton:hover {\n"
"    background: qradialgradient(\n"
"        cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,\n"
"        radius: 1.35, stop: 0 #fff, stop: 1 #bbb\n"
"        );\n"
"    }\n"
"\n"
"QPushButton:pressed {\n"
"    border-style: inset;\n"
"    background: qradialgradient(\n"
"        cx: 0.4, cy: -0.1, fx: 0.4, fy: -0.1,\n"
"        radius: 1.35, stop: 0 #fff, stop: 1 #ddd\n"
"        );\n"
"    }")
        self.playButton.setText("")
        self.playButton.setShortcut("")
        self.playButton.setCheckable(True)
        self.playButton.setChecked(False)
        self.playButton.setAutoExclusive(False)
        self.playButton.setFlat(False)
        self.playButton.setObjectName("playButton")
        self.transportBtnGroup.addButton(self.playButton)
        self.horizontalLayout_2.addWidget(self.playButton)
        self.stopButton = QtWidgets.QPushButton(self.frame)
        self.stopButton.setMinimumSize(QtCore.QSize(20, 20))
        self.stopButton.setMaximumSize(QtCore.QSize(40, 40))
        self.stopButton.setStyleSheet("QPushButton {\n"
"     qproperty-icon: url(:/images/gui/Media-Controls-Stop-icon.png);\n"
"}\n"
"\n"
"QPushButton {\n"
"    color: #333;\n"
"    border: 2px solid #555;\n"
"    border-radius: 20px;\n"
"    border-style: outset;\n"
"    background: qradialgradient(\n"
"        cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,\n"
"        radius: 1.35, stop: 0 #d90000, stop: 1 #d90000\n"
"        );\n"
"    padding: 5px;\n"
"    }\n"
"\n"
"QPushButton:hover {\n"
"    background: qradialgradient(\n"
"        cx: 0.3, cy: -0.4, fx: 0.3, fy: -0.4,\n"
"        radius: 1.35, stop: 0 #e60000, stop: 1 #e60000\n"
"        );\n"
"    }\n"
"\n"
"QPushButton:pressed {\n"
"    border-style: inset;\n"
"    background: qradialgradient(\n"
"        cx: 0.4, cy: -0.1, fx: 0.4, fy: -0.1,\n"
"        radius: 1.35, stop: 0 #ff0000, stop: 1 #ff0000\n"
"        );\n"
"    }")
        self.stopButton.setText("")
        self.stopButton.setObjectName("stopButton")
        self.transportBtnGroup.addButton(self.stopButton)
        self.horizontalLayout_2.addWidget(self.stopButton)
        self.horizontalLayout.addWidget(self.frame)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pauseButton.setShortcut(_translate("Form", "1"))
        self.stopButton.setShortcut(_translate("Form", "3"))
import resources_rc