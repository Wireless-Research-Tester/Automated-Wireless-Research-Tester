""""
=============
Transport
=============
Displays empty window
"""
import sys
from PyQt5 import QtWidgets as qtw
from gui.transport_form import Ui_Form


class TransportWidget(qtw.QWidget, Ui_Form):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        # Main UI code goes here

        # End main UI code
        # self.show()


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    tw = TransportWidget()
    sys.exit(app.exec())
