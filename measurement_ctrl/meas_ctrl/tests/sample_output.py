class data:
    def __init__(self, measurement_type, freq, theta, phi, value_mag, value_phase):
        self.measurement_type = measurement_type
        self.freq = freq
        self.theta = theta
        self.phi = phi
        self.value_mag = value_mag
        self.value_phase = value_phase


def get_data():
    temp_data_set = []
    for i in range(0, 360):
        temp_data_set.append(data('S21', 1000, 90, i, round(-30 - abs(i - 180) / 6, 4), -i))
        temp_data_set.append(data('S21', 1100, 90, i, round(-30 - abs(i - 170) / 6, 4), -i))
        temp_data_set.append(data('S21', 1200, 90, i, round(-30 - abs(i - 160) / 6, 4), -i))
        temp_data_set.append(data('S21', 1300, 90, i, round(-30 - abs(i - 150) / 6, 4), -i))
        temp_data_set.append(data('S21', 1400, 90, i, round(-30 - abs(i - 140) / 6, 4), -i))
        temp_data_set.append(data('S21', 1500, 90, i, round(-30 - abs(i - 130) / 6, 4), -i))
        temp_data_set.append(data('S21', 1600, 90, i, round(-30 - abs(i - 120) / 6, 4), -i))
        temp_data_set.append(data('S21', 1700, 90, i, round(-30 - abs(i - 110) / 6, 4), -i))
        temp_data_set.append(data('S21', 1800, 90, i, round(-30 - abs(i - 100) / 6, 4), -i))
        temp_data_set.append(data('S21', 1900, 90, i, round(-30 - abs(i - 90) / 6, 4), -i))
    return temp_data_set
