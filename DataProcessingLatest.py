"""
Data Processing Widget v10.0
10/17/2020
Author: Stephen Wood
"""

import sys
import matplotlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import AxesWidget, RadioButtons
import os
import json
from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import pyqtSlot

matplotlib.use('Qt5Agg')


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=12, height=8, dpi=80):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)


class DataProcessing(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(DataProcessing, self).__init__(*args, **kwargs)

        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        self.sc = MplCanvas(self, width=9, height=6, dpi=80)

        self.Resolution = None
        self.Polar = None
        self.ReqFreq = None  # Values in MHz
        self.data_file = None
        self.Live = None
        self.plot_lines = []
        self.plot_labels = []
        self.alt_labels = []
        self.num_of_frequencies = 0
        self.radio = MyRadioButtons
        self.ani = None

        # Create toolbar, passing canvas as first parament, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(self.sc, self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.sc)

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.show()

    def begin_measurement(self, data_file, pivot_file=None):
        if pivot_file is not None:
            with open(pivot_file) as file:
                args = json.load(file)
            self.Resolution = args['resolution']
        self.Polar = True
        # self.ReqFreq = args['freq']  # Values in MHz
        self.data_file = data_file
        self.Live = self.is_live()

        if self.Live:
            self.ani = animation.FuncAnimation(self.sc.figure, self.animate, interval=1000)
        else:
            self.start_graphing()

    def animate(self, i):
        self.sc.figure.clf()
        self.start_graphing()
        if not self.Live:
            self.ani.event_source.stop()

    def set_visible(self, label):
        index = self.radio.circles.index(label.artist)
        # print(index)
        # print(self.plot_lines[index].get_visible())
        self.plot_lines[index].set_visible(not self.plot_lines[index].get_visible())
        # print(self.plot_lines[index].get_visible())
        self.sc.ax.figure.canvas.draw()

    def graph_all_rect(self, df):
        """
        This function graphs all frequencies from a list or linear sweep
        Polar plot - azimuth vs. amplitude
        Assumes frequencies are in MHz

        :param df: Sorted DataFrame
        :return: None
        """
        self.alt_labels = []
        type_of_marker = 'D'  # Can be added to MyRadioButtons function as Kwarg

        # Starting point in data frame
        index = 0

        # Number of rows
        number_of_rows = len(df.index)

        # Number of points per freq
        if self.Live:
            points_per_freq = number_of_rows // self.num_of_frequencies
        else:
            points_per_freq = (number_of_rows - 1) // self.num_of_frequencies

        # Define the number of rows per frequency
        rows_per_freq = points_per_freq // self.Resolution

        # Isolate phi column and convert to radians
        phi_val_set = df.iloc[index:rows_per_freq, [3]]

        # Isolate magnitude column and convert to relative zero
        # max_magnitude is the largest magnitude in the file
        max_magnitude = df['magnitude'].max()
        magnitude_val_set = df.iloc[index:rows_per_freq, [4]]
        if max_magnitude > 0:
            magnitude_val_set = magnitude_val_set['magnitude'] + max_magnitude
        else:
            magnitude_val_set = magnitude_val_set['magnitude'] - max_magnitude

        # Create a string of requested frequency for legend
        current_freq = (df['freq'].values[index])
        if self.Live:
            current_freq_string = str(current_freq / 1000)
        else:
            current_freq_string = str(float(current_freq / 1000))

        # Create plot
        self.sc.ax = self.sc.figure.add_subplot(64, 1, (1, 50))

        # Add frequencies to plot
        self.sc.ax.plot(phi_val_set, magnitude_val_set,  # Plots first line
                        label=current_freq_string,
                        color='C0')
        self.alt_labels.append(current_freq_string)  # Allows for push buttons
        for x in range(1, self.num_of_frequencies):
            index += rows_per_freq
            phi_val_set = df.iloc[index:index + rows_per_freq, [3]]
            magnitude_val_set = df.iloc[index:index + rows_per_freq, [4]]
            if max_magnitude > 0:
                magnitude_val_set = magnitude_val_set['magnitude'] + max_magnitude
            else:
                magnitude_val_set = magnitude_val_set['magnitude'] - max_magnitude
            current_freq = (df['freq'].values[index])
            if self.Live:
                current_freq_string = str(current_freq / 1000)
            else:
                current_freq_string = str(float(current_freq / 1000))
            self.sc.ax.plot(phi_val_set, magnitude_val_set,
                            label=current_freq_string,
                            color='C' + str(x % 10))
            self.alt_labels.append(current_freq_string)

        # Customize Plot
        self.sc.ax.grid(True)
        self.sc.ax.set_xlim(left=0,  # x min 0, x max 360
                            right=360)
        self.sc.ax.set_ylim(top=0,  # y min 0 dB, y max -40 dB
                            bottom=-40)
        self.sc.ax.set_xlabel('Degrees')
        self.sc.ax.set_ylabel('S11 Amplitude (dB)')
        self.sc.ax.set_xticks(range(0, 360, 30))  # Ticks increase every 30 degrees

        self.sc.figure.subplots_adjust(left=0.05,
                                       right=0.95)
        self.sc.figure.suptitle('Normalized Far-field Pattern of xy-plane',
                                fontweight="bold",
                                fontsize=15)

        # Set up legend
        self.sc.bx = self.sc.figure.add_subplot(64, 1, (57, 64))
        self.sc.bx.set_xlabel('Frequency (GHz)')
        self.sc.bx.spines["top"].set_visible(False)
        self.sc.bx.spines["bottom"].set_visible(False)
        self.sc.bx.spines["right"].set_visible(False)
        self.sc.bx.spines["left"].set_visible(False)
        self.plot_lines, self.plot_labels = self.sc.ax.get_legend_handles_labels()

        # Create buttons (On/Off)
        self.radio = MyRadioButtons(self.sc.bx, self.alt_labels,
                                    marker=type_of_marker,  # string choose from matplotlib markers
                                    keep_color=self.Live,  # Bool whether button pushes change color
                                    size=100,  # if diamond type_of_marker size(100) default: (100)
                                    ncol=10)  # Number of columns
        if not self.Live:
            self.sc.figure.canvas.mpl_connect('pick_event', self.set_visible)

    def graph_all_polar(self, df):
        """
        This function graphs all frequencies from a list or linear sweep
        Polar plot - azimuth vs. amplitude
        Assumes frequencies are in MHz

        :param df: Sorted DataFrame
        :return: None
        """
        self.alt_labels = []
        type_of_marker = 'D'  # Can be added to MyRadioButtons function as Kwarg

        # Starting point in data frame
        index = 0

        # Number of rows
        number_of_rows = len(df.index)

        # Number of points per freq
        if self.Live:
            points_per_freq = number_of_rows // self.num_of_frequencies
        else:
            points_per_freq = (number_of_rows - 1) // self.num_of_frequencies

        # Define the number of rows per frequency
        rows_per_freq = points_per_freq  # (points_per_freq // self.Resolution)

        # Isolate phi column and convert to radians
        phi_val_set = np.radians(df.iloc[index:rows_per_freq, [3]])

        # Isolate magnitude column and convert to relative zero
        max_magnitude = df['magnitude'].max()
        magnitude_val_set = df.iloc[index:rows_per_freq, [4]]
        if max_magnitude > 0:
            magnitude_val_set = magnitude_val_set['magnitude'] + max_magnitude
        else:
            magnitude_val_set = magnitude_val_set['magnitude'] - max_magnitude

        # Create a string of requested frequency for legend
        current_freq = (df['freq'].values[index])
        if self.Live:
            current_freq_string = str(current_freq / 1000)
        else:
            current_freq_string = str(float(current_freq / 1000))

        # Create polar plot
        self.sc.ax = self.sc.figure.add_subplot(1, 64, (13, 64),
                                                projection='polar')

        # Add frequencies to plot
        self.sc.ax.plot(phi_val_set, magnitude_val_set,  # Plots first line
                        label=current_freq_string,
                        color='C0')
        self.alt_labels.append(current_freq_string)  # Allows for push buttons
        for x in range(1, self.num_of_frequencies):
            index += rows_per_freq
            phi_val_set = np.radians(df.iloc[index:index + rows_per_freq, [3]])
            magnitude_val_set = df.iloc[index:index + rows_per_freq, [4]]
            if max_magnitude > 0:
                magnitude_val_set = magnitude_val_set['magnitude'] + max_magnitude
            else:
                magnitude_val_set = magnitude_val_set['magnitude'] - max_magnitude
            current_freq = (df['freq'].values[index])
            if self.Live:
                current_freq_string = str(current_freq / 1000)
            else:
                current_freq_string = str(float(current_freq / 1000))
            self.sc.ax.plot(phi_val_set, magnitude_val_set,
                            label=current_freq_string,
                            color='C' + str(x % 10))
            self.alt_labels.append(current_freq_string)

        # Customize Plot
        self.sc.ax.set_xlabel('Frequency (GHz)')
        self.sc.ax.set_rlabel_position(0)  # r max is 0 dB
        self.sc.ax.set_theta_zero_location("N")  # 0 degrees at 12 o'clock
        self.sc.ax.set_theta_direction(-1)  # Degrees increase clockwise
        self.sc.ax.set_rmin(-40)  # r min is -40 dB
        self.sc.ax.grid(True)
        self.sc.ax.set_thetagrids(range(0, 360, 15))  # Ticks increase every 15 degrees

        self.sc.figure.subplots_adjust(left=0.05,
                                       right=0.80)
        self.sc.figure.suptitle('Normalized Far-field Pattern of xy-plane',
                                fontweight="bold",
                                fontsize=15)

        self.sc.bx = self.sc.figure.add_subplot(1, 64, (1, 9))
        self.sc.bx.spines["top"].set_visible(False)
        self.sc.bx.spines["bottom"].set_visible(False)
        self.sc.bx.spines["right"].set_visible(False)
        self.sc.bx.spines["left"].set_visible(False)
        self.plot_lines, self.plot_labels = self.sc.ax.get_legend_handles_labels()

        # Create buttons (On/Off)
        self.radio = MyRadioButtons(self.sc.bx, self.alt_labels,
                                    marker=type_of_marker,
                                    keep_color=self.Live,  # Bool whether button pushes change color
                                    size=100,  # if diamond type_of_marker size(100) default: (100)
                                    ncol=2)  # Number of columns
        if not self.Live:
            self.sc.figure.canvas.mpl_connect('pick_event', self.set_visible)

    def graph_one_rect(self, df):
        """
        This function graphs one frequency from a list or linear sweep
        Rectangular plot - azimuth vs. amplitude
        Assumes frequencies are in MHz

        :param df: Sorted DataFrame
        :return: None
        """
        self.alt_labels = []
        type_of_marker = 'D'  # Can be added to MyRadioButtons function as Kwarg

        # Number of rows
        number_of_rows = len(df.index)

        # Number of points per freq
        if self.Live:
            points_per_freq = number_of_rows // self.num_of_frequencies
        else:
            points_per_freq = (number_of_rows - 1) // self.num_of_frequencies

        # Define the number of rows per frequency
        rows_per_freq = points_per_freq // self.Resolution

        # Find the requested frequency index in data frame
        index = self.freq_index(df)

        # Isolate phi column
        phi_val_set = df.iloc[index:rows_per_freq, [3]]

        # Isolate magnitude column and convert to relative zero
        # max_magnitude is the largest magnitude in the set
        magnitude_val_set = df.iloc[index:index + rows_per_freq, [4]]
        max_magnitude = int(magnitude_val_set.max())
        if max_magnitude > 0:
            magnitude_val_set = magnitude_val_set['magnitude'] + max_magnitude
        else:
            magnitude_val_set = magnitude_val_set['magnitude'] - max_magnitude

        # Create a string of requested frequency for legend
        req_freq_string = str(self.ReqFreq)
        self.alt_labels.append(req_freq_string)  # Allows for push buttons

        # Create polar plot
        self.sc.ax = self.sc.figure.add_subplot(64, 1, (1, 50))

        # Plot data set
        self.sc.ax.plot(phi_val_set, magnitude_val_set,  # Plots line
                        label=req_freq_string)

        # Customize Plot
        self.sc.ax.grid(True)
        self.sc.ax.set_xlim(left=0,  # x min 0, x max 360
                            right=360)
        self.sc.ax.set_ylim(top=0,  # y min 0 dB, y max -40 dB
                            bottom=-40)
        self.sc.ax.set_xlabel('Degrees')
        self.sc.ax.set_ylabel('S11 Amplitude (dB)')
        self.sc.ax.set_xticks(range(0, 360, 30))  # Ticks increase every 30 degrees

        self.sc.figure.subplots_adjust(left=0.05,
                                       right=0.95)
        self.sc.figure.suptitle('Normalized Far-field Pattern of xy-plane',
                                fontweight="bold",
                                fontsize=25)

        # Set up legend
        self.sc.bx = self.sc.figure.add_subplot(64, 1, (57, 64))
        self.sc.bx.set_xlabel('Frequency (GHz)')
        self.sc.bx.spines["top"].set_visible(False)
        self.sc.bx.spines["bottom"].set_visible(False)
        self.sc.bx.spines["right"].set_visible(False)
        self.sc.bx.spines["left"].set_visible(False)
        self.plot_lines, self.plot_labels = self.sc.ax.get_legend_handles_labels()

        # Create buttons (On/Off)
        self.radio = MyRadioButtons(self.sc.bx, self.alt_labels,
                                    marker=type_of_marker,  # string choose from matplotlib markers
                                    keep_color=True,  # Bool whether button pushes change color
                                    size=100,  # if diamond type_of_marker size(100) default: (100)
                                    ncol=10)  # Number of columns

    def graph_one_polar(self, df):
        """
        This function graphs one frequency from a list or linear sweep
        Polar plot - azimuth vs. amplitude
        Assumes frequencies are in MHz

        :param df: Sorted DataFrame
        :return: None
        """
        self.alt_labels = []
        type_of_marker = 'D'  # Can be added to MyRadioButtons function as Kwarg

        # Number of rows
        number_of_rows = len(df.index)

        # Number of points per freq
        if self.Live:
            points_per_freq = number_of_rows // self.num_of_frequencies
        else:
            points_per_freq = (number_of_rows - 1) // self.num_of_frequencies

        # Define the number of rows per frequency
        rows_per_freq = points_per_freq // self.Resolution

        # Find the requested frequency index in data frame
        index = self.freq_index(df)

        # Isolate phi column and convert to radians
        phi_val_set = np.radians(df.iloc[index:index + rows_per_freq, [3]])

        # Isolate magnitude column and convert to relative zero
        # max_magnitude is the largest magnitude in the set
        magnitude_val_set = df.iloc[index:index + rows_per_freq, [4]]
        max_magnitude = int(magnitude_val_set.max())
        if max_magnitude > 0:
            magnitude_val_set = magnitude_val_set['magnitude'] + max_magnitude
        else:
            magnitude_val_set = magnitude_val_set['magnitude'] - max_magnitude

        # Create a string of requested frequency for legend
        req_freq_string = str(self.ReqFreq)
        self.alt_labels.append(req_freq_string)  # Allows for push buttons

        # Create polar plot
        self.sc.ax = self.sc.figure.add_subplot(1, 64, (13, 64),
                                                projection='polar')

        # Plot data set
        self.sc.ax.plot(phi_val_set, magnitude_val_set,  # Plots line
                        label=req_freq_string)

        # Customize Plot
        self.sc.ax.set_xlabel('Frequency (GHz)')
        self.sc.ax.set_rlabel_position(0)  # r max is 0 dB
        self.sc.ax.set_theta_zero_location("N")  # 0 degrees at 12 o'clock
        self.sc.ax.set_theta_direction(-1)  # Degrees increase clockwise
        self.sc.ax.set_rmin(-40)  # r min is -40 dB
        self.sc.ax.grid(True)
        self.sc.ax.set_thetagrids(range(0, 360, 15))  # Ticks increase every 15 degrees

        self.sc.figure.subplots_adjust(left=0.05,
                                       right=0.80)
        self.sc.figure.suptitle('Normalized Far-field Pattern of xy-plane',
                                fontweight="bold",
                                fontsize=25)

        # Set up legend
        self.sc.bx = self.sc.figure.add_subplot(1, 64, (1, 9))
        self.sc.bx.spines["top"].set_visible(False)
        self.sc.bx.spines["bottom"].set_visible(False)
        self.sc.bx.spines["right"].set_visible(False)
        self.sc.bx.spines["left"].set_visible(False)
        self.plot_lines, self.plot_labels = self.sc.ax.get_legend_handles_labels()

        # Create buttons (On/Off)
        self.radio = MyRadioButtons(self.sc.bx, self.alt_labels,
                                    marker=type_of_marker,
                                    keep_color=self.Live,  # Bool whether button pushes change color
                                    size=100,  # if diamond type_of_marker size(100) default: (100)
                                    ncol=2)  # Number of columns

    def is_file_empty(self):
        """
        This function reads a file into a Pandas DataFrame

        :return: Bool True if and only if file exists and is its size is 0 bytes
        """
        return os.path.exists(self.data_file) and os.path.getsize(self.data_file) == 0

    def read_file(self):
        """
        This function reads a file into a Pandas DataFrame

        :return: if not empty returns DataFrame
        """
        df = pd.read_csv(self.data_file)
        return df

    def is_live(self):
        """
        This function looks for 'null' at the end of data frame

        :return: Bool True if null not found else False
        """
        with open(self.data_file, 'r') as f:
            lines = f.read().splitlines()
            last_line = lines[-1]
        compare = 'null,null,null,null,null,null'
        if last_line == compare:
            return False
        else:
            return True

    @staticmethod
    def sort_file(df):
        """
        This function sorts the DataFrame rows in ascending order
        by frequency, phi, and theta; in that order

        :param df: Unsorted DataFrame
        :return: Sorted DataFrame
        """
        # Sort the data by frequency, phi, and theta
        df = df.sort_values(by=['freq', 'phi'])
        return df

    def tot_num_frequencies(self, df):
        """
        This function determines how many frequencies were included in the sweep or list

        :param df: Unsorted DataFrame
        :return: Number of different frequencies in DataFrame
        """
        if df.empty:
            return False
        start_freq = (df['freq'].values[0])
        self.num_of_frequencies = 1
        for x in range(1, len(df.index)):
            if start_freq == df['freq'].values[x]:
                return
            elif start_freq != df['freq'].values[x]:
                self.num_of_frequencies += 1
        return

    def freq_index(self, df):
        """
        This function finds the starting index of a specific frequency within the DataFrame

        :param df: Sorted DataFrame
        :return: if freq is in DataFrame return index
        """
        data_points = (360 // self.Resolution)
        index = 0
        for x in range(0, self.num_of_frequencies):
            if self.ReqFreq == (df['freq'].values[index]):
                return index
            else:
                index += data_points
        return False

    def start_graphing(self):
        """
        This function takes the arguments passed by JSON and calls initial functions

        :return: None
        """
        self.Live = self.is_live()
        # check if file exist and not empty
        is_empty = self.is_file_empty()
        if is_empty:
            print('File is empty')
            return
        df = self.read_file()
        if df.empty:
            print('File only contains column headers')
            return
        self.tot_num_frequencies(df)
        if self.num_of_frequencies:
            df = self.sort_file(df)
            if self.Polar:
                if self.ReqFreq:
                    self.graph_one_polar(df)
                else:
                    self.graph_all_polar(df)
            else:
                if self.ReqFreq:
                    self.graph_one_rect(df)
                else:
                    self.graph_all_rect(df)
        return


class MyRadioButtons(RadioButtons):
    """
    !!!Class overrides RadioButtons!!!
    """

    def __init__(self, ax, labels, marker='$-$', keep_color=False, size=49,
                 orientation="vertical", **kwargs):
        """
        Add radio buttons to an `~.axes.Axes`.
        Parameters
        ----------
        ax : `~matplotlib.axes.Axes`
            The axes to add the buttons to.
        labels : list of str
            The button labels...
        marker : str
            Changes can be made according to matplotlib.markers selection
        keep_color : Bool
            if True button press does nothing else button color turns on/off
        size : float
            Size of the radio buttons
        orientation : str
            The orientation of the buttons: 'vertical' (default), or 'horizontal'.
        Further parameters are passed on to `Legend`.
        """
        AxesWidget.__init__(self, ax)
        self.value_selected = None
        self.keep_color = keep_color

        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_navigate(False)

        self.circles = []
        for i, label in enumerate(labels):
            if i:
                self.value_selected = label
                facecolor = 'C' + str(i % 10)
            else:
                facecolor = 'C' + str(i % 10)
            p = ax.scatter([], [],
                           s=size,
                           marker=marker,
                           edgecolor='black',
                           facecolor=facecolor)
            self.circles.append(p)
        if orientation == "horizontal":
            kwargs.update(ncol=len(labels),
                          mode="expand")
        kwargs.setdefault("frameon", False)
        self.box = ax.legend(self.circles, labels,
                             loc="center",
                             **kwargs)
        self.labels = self.box.texts
        self.circles = self.box.legendHandles
        for c in self.circles:
            c.set_picker(5)
        self.cnt = 0
        self.observers = {}

        self.connect_event('pick_event', self._clicked)

    def _clicked(self, event):
        if (self.ignore(event) or event.mouseevent.button != 1 or
                event.mouseevent.inaxes != self.ax):
            return
        if event.artist in self.circles:
            self.set_active(self.circles.index(event.artist))

    def set_active(self, index):
        """
        Select button with number *index*.

        Callbacks will be triggered if :attr:`eventson` is True.
        """
        if self.keep_color:
            return

        if 0 > index >= len(self.labels):
            raise ValueError("Invalid RadioButton index: %d" % index)

        self.value_selected = self.labels[index].get_text()

        for i, p in enumerate(self.circles):
            if i == index:
                if (p.get_facecolor() == self.ax.get_facecolor()).all():
                    color = 'C' + str(i % 10)
                else:
                    color = self.ax.get_facecolor()
            else:
                color = p.get_facecolor()
            p.set_facecolor(color)

        if self.drawon:
            self.ax.figure.canvas.draw()

        if not self.eventson:
            return
        for cid, func in self.observers.items():
            func(self.labels[index].get_text())

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    w = DataProcessing()
    sys.exit(app.exec())
