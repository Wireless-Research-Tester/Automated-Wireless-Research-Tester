""""
=============
Positioner Toolbar widget
=============
Displays empty window
"""""
import sys
from PyQt5 import QtWidgets as qtw, uic


baseUIClass, baseUIWidget = uic.loadUiType('gui/pos_control_ui.ui')


class PositionerToolBarWidget(baseUIWidget, baseUIClass):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        # Main UI code goes here

        # End main UI code
        self.show()

 
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    ptbw = PositionerToolBarWidget()
    sys.exit(app.exec())
