###################################################################################
#  Data Processing
#
#  Description:     Data Processing focuses on reading and graphing data points
#                   from a .csv file written in Measurement Control. This includes
#                   S21 measurements plotted in rectangular or polar form that
#                   represent azimuth vs. amplitude and S11 measurements plotted
#                   in rectangular form representing impedance. Additionally, Data
#                   Processing uses MatPlotLib and PyQt5 to display the data and
#                   Pandas and Numpy to make necessary calculations on the data.
#                   Lastly, while Measurement Control adds additional data points
#                   to the .csv Data Processing has added functionality to update
#                   plots in real-time.
#
#  Dependencies:    MatPlotLib Version: 3.3.0
#                   Pandas Version:
#                   Numpy Version:
#                   PyQt5
#
#  Author(s): Stephen Wood
#  Date: 2020/10/28
#  Built with Python Version: 3.8.5
###################################################################################

import sys
import matplotlib
import numpy as np
import pandas as pd
import matplotlib.animation as animation
from matplotlib.widgets import AxesWidget, RadioButtons
import os
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

matplotlib.use('Qt5Agg')


class Signals(QtCore.QObject):
    s11_present = QtCore.pyqtSignal()
    s11_absent = QtCore.pyqtSignal()


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=9, height=6, dpi=80):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(MplCanvas, self).__init__(self.fig)


class DataProcessing(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(DataProcessing, self).__init__(*args, **kwargs)

        # Create the maptlotlib FigureCanvas object,
        self.sc = MplCanvas(self, width=9, height=6, dpi=80)

        self.polar = None  # Bool value will be true if we need polar graph else rectangular graph
        self.s11 = None  # Bool value will be true if s11 measurements are present in data_file
        self.data_file = None  # File containing data recorded from measurement control
        self.live = None  # Bool True if live measurements are being made
        self.plot_lines = []  # Array holding the callbacks values of lines on graphs
        self.plot_labels = []  # Array holding the label names of lines on graphs
        self.alt_labels = []  # Array holding the names of lines on graphs; used for radio buttons
        self.max_freq = None  # Value of the max frequency in the data_file
        self.num_of_frequencies = None  # Total number of frequencies present in the data_file
        self.radio = None  # Variable used for RadioButtons
        self.ani = None  # Variable used for animation method
        self.signals = Signals()  # Variable used to send signals back to the GUI

        # Create toolbar, passing canvas as first parameter, parent (self, the MainWindow) as second.
        toolbar = NavigationToolbar(self.sc, self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.sc)

        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.show()

    def begin_measurement(self, data_file, polar=True, s11=False, is_live=None):
        """
        This method will is called from the GUI when graphing needs to begin
        :param data_file: File location where data from measurement control is held
        :param polar: Bool value determining whether to graph polar or rectangular form
        :param s11: Bool value determining whether to graph s11 values or not
        :param is_live: Bool value determining whether plots are live updating
        :return: None
        """
        self.polar = polar
        self.s11 = s11
        self.data_file = data_file

        if is_live is None:
            self.live = self.is_live()
        else:
            self.live = is_live

        if self.live:
            self.ani = animation.FuncAnimation(self.sc.figure, self.animate, interval=1000)
        else:
            self.start_graphing(is_live)

    def animate(self, i):
        """
        This method is used for updating graphs in real time
        :param i: integer value in milliseconds; determines how fast plots will update
        :return: None
        """
        self.sc.figure.clf()  # Clears figure before graphing new data; prevents memory leaks
        self.start_graphing()  # Starts the graphing process
        # If all data points are captured, live updating will stop
        if not self.live:
            self.ani.event_source.stop()

    def set_visible(self, label):
        """
        This method will show and hide lines on the graph
        :param label: Refers to the label of the line
        :return: None
        """
        index = self.radio.circles.index(label.artist)
        self.plot_lines[index].set_visible(not self.plot_lines[index].get_visible())
        self.sc.ax.figure.canvas.draw()

    def graph_all_rect(self, df):
        """
        This method graphs all frequencies from a list or linear sweep
        Rectangular plot - Azimuth vs. Amplitude
        :param df: Sorted S21 DataFrame
        :return: None
        """
        self.alt_labels = []
        mhz = self.mhz_or_ghz()  # Determines if lines should be represented in MHz or GHz
        type_of_marker = 'D'  # Kwarg for MyRadioButtons class to change the shape of button

        # Starting point in data frame
        index = 0

        # Number of rows
        number_of_rows = len(df.index)

        # Number of points per freq and freq limit
        if self.num_of_frequencies > 10:
            points_per_freq = number_of_rows // 10
            freq_limit = 10
        else:
            points_per_freq = number_of_rows // self.num_of_frequencies
            freq_limit = self.num_of_frequencies

        # Isolate phi column
        phi_val_set = df.iloc[index:points_per_freq, [3]]

        # Isolate magnitude column and convert to relative zero
        # max_magnitude is the largest magnitude in the sorted data frame
        max_magnitude = df['magnitude'].max()
        magnitude_val_set = df.iloc[index:points_per_freq, [4]]
        if max_magnitude > 0:
            magnitude_val_set = magnitude_val_set['magnitude'] + max_magnitude
        else:
            magnitude_val_set = magnitude_val_set['magnitude'] - max_magnitude

        # find smallest value in data frame; this helps to set visible points
        min_magnitude = magnitude_val_set.min()
        if min_magnitude < -40:
            numpy_magnitude_set = np.array(magnitude_val_set.values.tolist())
            magnitude_val_set = np.where(numpy_magnitude_set < -40, -40, numpy_magnitude_set).tolist()

        # Create a string of current frequency for legend
        current_freq = df['freq'].values[index]
        if mhz:
            current_freq_string = str(float(current_freq))
        else:
            if current_freq < 1:
                current_freq_string = str(round(current_freq / 1000, 5))
            else:
                current_freq_string = str(float(current_freq / 1000))

        # Create subplot for graph window
        self.sc.ax = self.sc.figure.add_subplot(64, 1, (1, 50))

        # Add first frequency line to subplot
        self.sc.ax.plot(phi_val_set, magnitude_val_set,  # Plots first line
                        label=current_freq_string,
                        color='C0')
        self.alt_labels.append(current_freq_string)  # Used in MyRadioButtons to create legend
        for x in range(1, freq_limit):
            index += points_per_freq
            phi_val_set = df.iloc[index:index + points_per_freq, [3]]
            magnitude_val_set = df.iloc[index:index + points_per_freq, [4]]
            if max_magnitude > 0:
                magnitude_val_set = magnitude_val_set['magnitude'] + max_magnitude
            else:
                magnitude_val_set = magnitude_val_set['magnitude'] - max_magnitude
            min_magnitude = magnitude_val_set.min()
            if min_magnitude < -40:
                numpy_magnitude_set = np.array(magnitude_val_set.values.tolist())
                magnitude_val_set = np.where(numpy_magnitude_set < -40, -40, numpy_magnitude_set).tolist()
            current_freq = df['freq'].values[index]
            if mhz:
                current_freq_string = str(float(current_freq))
            else:
                if current_freq < 1:
                    current_freq_string = str(round(current_freq / 1000, 5))
                else:
                    current_freq_string = str(float(current_freq / 1000))
            self.sc.ax.plot(phi_val_set, magnitude_val_set,
                            label=current_freq_string,
                            color='C' + str(x % 10))
            self.alt_labels.append(current_freq_string)

        # Customize Plot
        self.sc.ax.grid(True)
        self.sc.ax.set_xlim(left=-180,  # x min -180, x max 180
                            right=180)
        self.sc.ax.set_ylim(top=0,  # y min 0 dB, y max -40 dB
                            bottom=-40)
        self.sc.ax.set_xlabel('Degrees')
        self.sc.ax.set_ylabel('S21 Amplitude (dB)')
        self.sc.ax.set_xticks(range(-180, 180, 30))  # Ticks increase every 30 degrees

        self.sc.figure.subplots_adjust(left=0.05,
                                       right=0.95)
        self.sc.figure.suptitle('Normalized Far-field Pattern',
                                fontweight="bold",
                                fontsize=15)

        # Create subplot to house the legend
        self.sc.bx = self.sc.figure.add_subplot(64, 1, (57, 64))
        if mhz:
            self.sc.bx.set_xlabel('Frequency (MHz)')
        else:
            self.sc.bx.set_xlabel('Frequency (GHz)')
        self.sc.bx.spines["top"].set_visible(False)
        self.sc.bx.spines["bottom"].set_visible(False)
        self.sc.bx.spines["right"].set_visible(False)
        self.sc.bx.spines["left"].set_visible(False)
        self.plot_lines, self.plot_labels = self.sc.ax.get_legend_handles_labels()

        # Create buttons (On/Off)
        self.radio = MyRadioButtons(self.sc.bx, self.alt_labels,
                                    marker=type_of_marker,  # String chosen from matplotlib markers
                                    keep_color=self.live,  # Bool whether button pushes have changing color effect
                                    size=100,  # If diamond type_of_marker size=100
                                    ncol=10)

        # If not updating in real time lines can be turned on and off
        if not self.live:
            self.sc.figure.canvas.mpl_connect('pick_event', self.set_visible)

    def graph_all_polar(self, df):
        """
        This method graphs all frequencies from a list or linear sweep
        Polar plot - Azimuth vs. Amplitude
        :param df: Sorted S21 DataFrame
        :return: None
        """
        self.alt_labels = []
        mhz = self.mhz_or_ghz()  # Determines if lines should be represented in MHz or GHz
        type_of_marker = 'o'  # Kwarg for MyRadioButtons class to change the shape of button

        # Starting point in data frame
        index = 0

        # Number of rows
        number_of_rows = len(df.index)

        # Number of points per freq and freq limit
        if self.num_of_frequencies > 10:
            points_per_freq = number_of_rows // 10
            freq_limit = 10
        else:
            points_per_freq = number_of_rows // self.num_of_frequencies
            freq_limit = self.num_of_frequencies

        # Isolate phi column and convert to radians
        phi_val_set = np.radians(df.iloc[index:points_per_freq, [3]])

        # Isolate magnitude column and convert to relative zero
        # max_magnitude is the largest magnitude in the sorted data frame
        max_magnitude = df['magnitude'].max()
        magnitude_val_set = df.iloc[index:points_per_freq, [4]]
        if max_magnitude > 0:
            magnitude_val_set = magnitude_val_set['magnitude'] + max_magnitude
        else:
            magnitude_val_set = magnitude_val_set['magnitude'] - max_magnitude

        # find smallest value in data frame; this helps to set visible points
        min_magnitude = magnitude_val_set.min()
        if min_magnitude < -40:
            numpy_magnitude_set = np.array(magnitude_val_set.values.tolist())
            magnitude_val_set = np.where(numpy_magnitude_set < -40, -40, numpy_magnitude_set).tolist()

        # Create a string of current frequency for legend
        current_freq = df['freq'].values[index]
        if mhz:
            current_freq_string = str(float(current_freq))
        else:
            if current_freq < 1:
                current_freq_string = str(round(current_freq / 1000, 5))
            else:
                current_freq_string = str(float(current_freq / 1000))

        # Create subplot for graph window
        self.sc.ax = self.sc.figure.add_subplot(1, 64, (13, 64),
                                                projection='polar')

        # Add first frequency line to subplot
        self.sc.ax.plot(phi_val_set, magnitude_val_set,  # Plots first line
                        label=current_freq_string,
                        color='C0')
        self.alt_labels.append(current_freq_string)  # Used in MyRadioButtons to create legend
        for x in range(1, freq_limit):
            index += points_per_freq
            phi_val_set = np.radians(df.iloc[index:index + points_per_freq, [3]])
            magnitude_val_set = df.iloc[index:index + points_per_freq, [4]]
            if max_magnitude > 0:
                magnitude_val_set = magnitude_val_set['magnitude'] + max_magnitude
            else:
                magnitude_val_set = magnitude_val_set['magnitude'] - max_magnitude
            min_magnitude = magnitude_val_set.min()
            if min_magnitude < -40:
                numpy_magnitude_set = np.array(magnitude_val_set.values.tolist())
                magnitude_val_set = np.where(numpy_magnitude_set < -40, -40, numpy_magnitude_set).tolist()
            current_freq = df['freq'].values[index]
            if mhz:
                current_freq_string = str(float(current_freq))
            else:
                if current_freq < 1:
                    current_freq_string = str(round(current_freq / 1000, 5))
                else:
                    current_freq_string = str(float(current_freq / 1000))
            self.sc.ax.plot(phi_val_set, magnitude_val_set,
                            label=current_freq_string,
                            color='C' + str(x % 10))
            self.alt_labels.append(current_freq_string)

        # Customize Plot
        if mhz:
            self.sc.ax.set_xlabel('Frequency (MHz)')
        else:
            self.sc.ax.set_xlabel('Frequency (GHz)')
        self.sc.ax.set_rlabel_position(0)  # r max is 0 dB
        self.sc.ax.set_theta_zero_location("N")  # 0 degrees at 12 o'clock
        self.sc.ax.set_theta_direction(-1)  # Degrees increase clockwise
        self.sc.ax.set_rmin(-40)  # r min is -40 dB
        self.sc.ax.grid(True)
        self.sc.ax.set_thetagrids(range(0, 360, 15))  # Ticks increase every 15 degrees

        self.sc.figure.subplots_adjust(left=0.05,
                                       right=0.80)
        self.sc.figure.suptitle('Normalized Far-field Pattern',
                                fontweight="bold",
                                fontsize=15)

        # Create subplot to house the legend
        self.sc.bx = self.sc.figure.add_subplot(1, 64, (1, 9))
        self.sc.bx.spines["top"].set_visible(False)
        self.sc.bx.spines["bottom"].set_visible(False)
        self.sc.bx.spines["right"].set_visible(False)
        self.sc.bx.spines["left"].set_visible(False)
        self.plot_lines, self.plot_labels = self.sc.ax.get_legend_handles_labels()

        # Create buttons (On/Off)
        self.radio = MyRadioButtons(self.sc.bx, self.alt_labels,
                                    marker=type_of_marker,  # String chosen from matplotlib markers
                                    keep_color=self.live,  # Bool whether button pushes have changing color effect
                                    size=90,  # If diamond type_of_marker size=100
                                    ncol=1)  # Number of columns

        # If not updating in real time lines can be turned on and off
        if not self.live:
            self.sc.figure.canvas.mpl_connect('pick_event', self.set_visible)

    def s11_rectangular_graph(self, df):
        """
        This method graphs all frequencies from a list or linear sweep
        Rectangular plot - Frequency vs. Impedance
        :param df: Sorted S11 DataFrame
        :return: None
        """
        self.alt_labels = []
        mhz = self.mhz_or_ghz()  # Determines if lines should be represented in MHz or GHz
        type_of_marker = 'D'  # Kwarg for MyRadioButtons class to change the shape of button

        # Starting point in data frame
        index = 0

        # Number of rows
        number_of_rows = len(df.index)

        # Calculations to find impedance values
        mag_set = df[['magnitude', 'phase']]
        r_set = mag_set['magnitude'] / 20
        r_set = 10 ** r_set
        mag_set = mag_set.assign(r_set=r_set)
        cos_phase = np.cos(mag_set['phase'])
        sin_phase = np.sin(mag_set['phase'])
        mag_set = mag_set.assign(cos_phase=cos_phase)
        mag_set = mag_set.assign(sin_phase=sin_phase)
        x_set = mag_set['r_set'] * mag_set['cos_phase']
        y_set = mag_set['r_set'] * mag_set['sin_phase']
        impedance_x_set = x_set * 50
        impedance_y_set = y_set * 50

        # First real and imaginary impedance values in data frame
        impedance_real_val = impedance_x_set.values[index]
        impedance_imag_val = impedance_y_set.values[index]

        # Create a string of current frequency for legend
        current_freq = df['freq'].values[index]
        if mhz:
            current_freq_string = str(float(current_freq))
        else:
            if current_freq < 1:
                current_freq_string = str(round(current_freq / 1000, 5))
            else:
                current_freq_string = str(float(current_freq / 1000))

        # Create subplot for graph window
        self.sc.ax = self.sc.figure.add_subplot(64, 1, (1, 50))

        # Add first frequency dot to subplot
        self.sc.ax.plot(impedance_real_val, impedance_imag_val,  # Plots first line
                        marker=".",
                        markersize=10,
                        label=current_freq_string,
                        color='C0')
        self.alt_labels.append(current_freq_string)  # Used in MyRadioButtons to create legend
        for x in range(1, number_of_rows):
            index += 1
            impedance_real_val = impedance_x_set.values[index]
            impedance_imag_val = impedance_y_set.values[index]
            current_freq = df['freq'].values[index]
            if mhz:
                current_freq_string = str(float(current_freq))
            else:
                if current_freq < 1:
                    current_freq_string = str(round(current_freq / 1000, 5))
                else:
                    current_freq_string = str(float(current_freq / 1000))
            self.sc.ax.plot(impedance_real_val, impedance_imag_val,
                            marker=".",
                            markersize=10,
                            label=current_freq_string,
                            color='C' + str(x % 10))
            self.alt_labels.append(current_freq_string)

        # Customize Plot
        self.sc.ax.grid(True)
        self.sc.ax.set_xlabel('Real')
        self.sc.ax.set_ylabel('Imaginary')

        self.sc.figure.subplots_adjust(left=0.05,
                                       right=0.95)
        self.sc.figure.suptitle('Impedance (Ohms)',
                                fontweight="bold",
                                fontsize=15)

        # Create subplot to house the legend
        self.sc.bx = self.sc.figure.add_subplot(64, 1, (57, 64))
        if mhz:
            self.sc.bx.set_xlabel('Frequency (MHz)')
        else:
            self.sc.bx.set_xlabel('Frequency (GHz)')
        self.sc.bx.spines["top"].set_visible(False)
        self.sc.bx.spines["bottom"].set_visible(False)
        self.sc.bx.spines["right"].set_visible(False)
        self.sc.bx.spines["left"].set_visible(False)
        self.plot_lines, self.plot_labels = self.sc.ax.get_legend_handles_labels()

        # Create buttons (On/Off)
        self.radio = MyRadioButtons(self.sc.bx, self.alt_labels,
                                    marker=type_of_marker,  # String chosen from matplotlib markers
                                    keep_color=self.live,  # Bool whether button pushes have changing color effect
                                    size=100,  # If diamond type_of_marker size=100
                                    ncol=10)

        # If not updating in real time lines can be turned on and off
        if not self.live:
            self.sc.figure.canvas.mpl_connect('pick_event', self.set_visible)

        return

    def is_file_empty(self):
        """
        This method determines if a file exists in location and contains anything
        :return: Bool True if and only if file exists and its size is 0 bytes
        """
        return os.path.exists(self.data_file) and os.path.getsize(self.data_file) == 0

    def read_file(self):
        """
        This method reads a file into a Pandas DataFrame
        :return: If not empty returns DataFrame
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
        First by frequency then phi
        :param df: Unsorted DataFrame
        :return: Sorted DataFrame
        """
        # Sort the data by frequency then phi; If using theta to create 3D plots, theta should be sorted last
        df = df.sort_values(by=['freq', 'phi'])
        return df

    @staticmethod
    def dataframe_for_s21(df):
        """
        Creates a dataframe containing all S21 measurements
        :param df: Unsorted DataFrame
        :return: S21 DataFrame
        """
        # Sort the data by frequency, phi, and theta
        df_s21 = df[df['measurement_type'].notnull()]
        df_s21 = df_s21[df_s21['measurement_type'].str.contains('S21')]
        return df_s21

    @staticmethod
    def dataframe_for_s11(df):
        """
        Creates a dataframe containing all S11 measurements
        :param df: Unsorted DataFrame
        :return: S11 DataFrame
        """
        # Sort the data by frequency, phi, and theta
        df_s11 = df[df['measurement_type'].notnull()]
        df_s11 = df_s11[df_s11['measurement_type'].str.contains('S11')]
        return df_s11

    def max_frequency(self, df):
        """
        This function finds the max freq
        :param df: Unsorted DataFrame
        :return: None
        """
        if self.num_of_frequencies > 10:
            self.max_freq = df.freq.iloc[9]
        else:
            self.max_freq = df.freq.iloc[self.num_of_frequencies - 1]
        return

    def mhz_or_ghz(self):
        """
        This function finds whether largest frequency should be represented in MHz or GHz
        :return: Bool True if MHz else False for GHz
        """
        freq = self.max_freq
        count = 0
        while freq != 0:
            count += 1
            freq //= 10
        if count < 4:
            return True
        else:
            return False

    def tot_num_frequencies(self, df):
        """
        This function determines how many frequencies were included in the sweep or list
        :param df: Unsorted DataFrame
        :return: Number of different frequencies in DataFrame
        """
        start_freq = (df['freq'].values[0])
        self.num_of_frequencies = 1
        for x in range(1, len(df.index)):
            if start_freq == df['freq'].values[x]:
                return
            elif start_freq != df['freq'].values[x]:
                self.num_of_frequencies += 1
        return

    @staticmethod
    def limit_ten(df):
        """
        This function will limit the DataFrame to 10 frequencies
        :param df: Unsorted DataFrame
        :return: DataFrame with first ten frequencies
        """
        tenth_freq = df.freq.iloc[9]
        df = df.loc[df['freq'] <= tenth_freq]
        return df

    def check_s11(self, df):
        """
        This function checks to see if S11 measurements are present in DataFrame
        :param df: DataFrame
        :return: Bool: if True DataFrame contains S11 measurements
        """
        df = df[df['measurement_type'].notnull()]
        df = df[df['measurement_type'].str.contains('S11')]
        if not df.empty:
            # If S11 measurements are in file, send PRESENT signal back to MainWindow
            self.signals.s11_present.emit()
            return True
        else:
            # If S11 measurements are NOT in file, send ABSENT signal back to MainWindow
            self.signals.s11_absent.emit()
            return False

    @staticmethod
    def check_s21(df):
        """
        This function checks to see if S21 measurements are present in DataFrame
        :param df: DataFrame
        :return: Bool: if True DataFrame contains S21 measurements
        """
        df = df[df['measurement_type'].notnull()]
        df = df[df['measurement_type'].str.contains('S21')]
        if not df.empty:
            return True
        else:
            return False

    def start_graphing(self, is_live=None):
        """
        This function takes the arguments passed by JSON and calls initial functions
        :return: None
        """
        # check if real time updates to file are happening
        if is_live is None:
            self.live = self.is_live()
        else:
            self.live = is_live

        # check if file exist and not empty
        is_empty = self.is_file_empty()
        if is_empty:
            print('File is empty')
            return
        df = self.read_file()
        if df.empty:
            print('File only contains column headers')
            return

        self.check_s11(df)
        self.tot_num_frequencies(df)  # Total number of frequencies
        self.max_frequency(df)  # Max frequency
        if self.num_of_frequencies:  # If measurements are in dataframe, continue
            if self.num_of_frequencies > 10:  # If more than ten frequencies are recorded, limit to ten
                df = self.limit_ten(df)  # Limits the data frame to ten frequencies
            if self.s11:  # True if GUI user asks for S11
                if self.check_s11(df):  # Checks to see if S11 measurements exist in file
                    df_s11 = self.dataframe_for_s11(df)  # Create the S11 data frame
                    self.s11_rectangular_graph(df_s11)  # Graph the S11 measurements in rectangular form
                    return
                else:
                    return
            if self.check_s21(df):  # Checks to see if S21 values are in dataframe
                df_s21 = self.dataframe_for_s21(df)  # Create the S21 data frame
                df_s21 = self.sort_file(df_s21)  # Sorts the S21 data frame
                if self.polar:  # True if GUI user asks for S21 in polar form, else the want rectangular form
                    self.graph_all_polar(df_s21)  # Graph the S21 measurements in polar form
                else:
                    self.graph_all_rect(df_s21)  # Graph the S21 measurements in rectangular form
        return


class NavigationToolbar(NavigationToolbar2QT):
    """
    !!!Class overrides matplotlib NavigationToolbar2QT!!!
    We only need to use the Save button so everything else is commented out
    """
    def _init_toolbar(self):
        pass

    # only display the buttons we need
    NavigationToolbar2QT.toolitems = (
        # ('Home', 'Reset original view', 'home', 'home'),
        # ('Back', 'Back to previous view', 'back', 'back'),
        # ('Forward', 'Forward to next view', 'forward', 'forward'),
        # (None, None, None, None),
        # ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        # ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        # ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
        # (None, None, None, None),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
    )


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
