""""
=============
Displays Groupbox toolbar with graph mode selection buttons
=============
"""
import sys
from PyQt5 import QtWidgets as qtw
from gui.graph_mode_form import Ui_Form


class GraphModeToolBar(qtw.QWidget, Ui_Form):

    def __init__(self):
        """MainWindow constructor"""
        super().__init__()
        self.setupUi(self)
        # Main UI code goes here


        # End main UI code
        # self.show()


if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    gmtb = GraphModeToolBar()
    sys.exit(app.exec())
