""""
=============
Popups
=============
Displays and clears pop-ups for the main and settings window
** Works if the for help buttons as on/off displays
"""""


settings_enabled = False
main_enabled = False

def settings_popups(self):
    global settings_enabled

    if not settings_enabled:
        #display pop-ups
        settings_enabled = True
        #settings_ui
        self.start_label_4.setToolTip('Start frequency for sweep')
        self.stop_label_4.setToolTip('Stop frequency for sweep')
        self.points_label_4.setToolTip('Number of data points for frequency sweep')
        self.list_label_5.setToolTip('Frequency list of measurements')
        self.Impedance_label_7.setToolTip('Measure AUT impedance \n' + 'Requires calibration')
        self.Calibration_label_7.setToolTip('Perform S11 single port calibration')
        self.Averaging_label_7.setToolTip('Number of measurements for VNA to average for each measurement')
        self.posMov_label_7.setToolTip('Hover over options for more details')
        self.cont_radioButton_7.setToolTip('Measurements collected with positioner in continuous movement \n' +
                                           'Requires slower rotation speed')
        self.discrete_radioButton_7.setToolTip('Measurements made with positioner stopped at each azimuth angle')
        self.res_label_7.setToolTip('Azimuth spacing between measurement points')
        self.GPIB_addr_label_6.setToolTip('GPIB address for VNA')
        self.sweep_elevation_label_6.setToolTip('AUT elevation angle')
        self.label.setToolTip('Directory for project data files')

    else:
        #erase pop-ups
        settings_enabled = False
        self.start_label_4.setToolTip('')
        self.stop_label_4.setToolTip('')
        self.points_label_4.setToolTip('')
        self.list_label_5.setToolTip('')
        self.Impedance_label_7.setToolTip('')
        self.Calibration_label_7.setToolTip('')
        self.Averaging_label_7.setToolTip('')
        self.posMov_label_7.setToolTip('')
        self.cont_radioButton_7.setToolTip('')
        self.discrete_radioButton_7.setToolTip('')
        self.res_label_7.setToolTip('')
        self.GPIB_addr_label_6.setToolTip('')
        self.sweep_elevation_label_6.setToolTip('')
        self.label.setToolTip('')


def main_popups(self):
    global main_enabled

    if not main_enabled:
        #display pop-ups
        main_enabled = True
        #transport_ui
        self.playButton.setToolTip('Begin measurement')
        #meas_display_ui
        self.az_lcdNumber.setToolTip('Current positioner azimuth')
        self.el_lcdNumber.setToolTip('Current positioner elevation')
        #progress_ui
        self.progressBar.setToolTip('Measurement progress')
        #pos_control_ui
        self.portLabel.setToolTip('Serial port for positioner')
        self.label_2.setToolTip('Explain what this does')
        self.faultReset.setToolTip('Explain what this does')

    else:
        #erase pop-ups
        main_enabled = False
        self.playButton.setToolTip('')
        self.progressBar.setToolTip('')
        self.az_lcdNumber.setToolTip('')
        self.el_lcdNumber.setToolTip('')
        self.portLabel.setToolTip('')
        self.label_2.setToolTip('')
        self.faultReset.setToolTip('')

