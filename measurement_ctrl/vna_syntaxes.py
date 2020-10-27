################################################################################
#  vna_syntaxes

#  Description: Contains functions that generate GPIB commands for the given
#               VNA model type and given command type.
#
#  Dependencies: n/a
#
#  Author(s): Eric Li
#  Date: 2020/09/30
#  Built with Python Version: 3.8.5
################################################################################
from enum import Enum, auto


class Model(Enum):
    """Add additional VNAs here"""
    HP_8753D = auto()
    # ex: NEW_VNA = auto()


def check_model(string):
    """Indicate a unique portion of the returned *IDN? query string
    which can identify the specific VNA model"""
    if '8753D' in string:
        return Model.HP_8753D
    else:
        raise Exception('Model is either not supported, or model is not found in query message: {}'.format(string))


def reset(model):
    """This action should perform a full reset on the VNA"""
    commands = {
        Model.HP_8753D: 'PRES',
    }
    return commands.get(model)


def form2(model):
    """This action should set the array data from the VNA to be transferred in 32-bit floating point format"""
    commands = {
        Model.HP_8753D: 'FORM2',
    }
    return commands.get(model)


def edit_list(model):
    """This action should prompt VNA to edit the list frequency table"""
    commands = {
        Model.HP_8753D: 'EDITLIST',
    }
    return commands.get(model)


def add_list_freq(model, arg):
    """This action should contain 3 steps:
    1. Add a new segment
    2. Modify the center frequency of the segment
    3. Done with segment
    """
    argument_valid = {
        Model.HP_8753D: arg * 10 ** 3 in range(30000, 6 * 10 ** 9 + 1),
    }

    commands = {
        Model.HP_8753D: 'SADD; CENT {} KHZ; SDON'.format(arg),
    }
    if argument_valid.get(model):
        return commands.get(model)
    else:
        raise Exception('The frequency is not in the valid range: {} MHz'.format(arg))


def list_freq_mode(model):
    """This action should select the list frequency sweep mode"""
    commands = {
        Model.HP_8753D: 'LISFREQ',
    }
    return commands.get(model)


def clear_list(model):
    """This action should clear the selected list"""
    commands = {
        Model.HP_8753D: 'CLEL',
    }
    return commands.get(model)


def lin_freq_start(model, arg):
    """This action should set the start frequency for a linear frequency sweep"""
    argument_valid = {
        Model.HP_8753D: arg * 10 ** 3 in range(30000, 6 * 10 ** 9),
    }

    commands = {
        Model.HP_8753D: 'STAR {} KHZ'.format(arg),
    }
    if argument_valid.get(model):
        return commands.get(model)
    else:
        raise Exception('The frequency is not in the valid range: {} MHz'.format(arg / 1000))


def lin_freq_end(model, arg):
    """This action should set the stop frequency for a linear frequency sweep"""
    argument_valid = {
        Model.HP_8753D: arg * 10 ** 3 in range(30000, 6 * 10 ** 9 + 1),
    }

    commands = {
        Model.HP_8753D: 'STOP {} KHZ'.format(arg),
    }
    if argument_valid.get(model):
        return commands.get(model)
    else:
        raise Exception('The frequency is not in the valid range: {} MHz'.format(arg / 1000))


def lin_freq_points(model, arg):
    """This action should set the number of points for a linear frequency sweep"""
    argument_valid = {
        Model.HP_8753D: arg in range(1, 1633),
    }

    commands = {
        Model.HP_8753D: 'POIN {}'.format(arg),
    }
    if argument_valid.get(model):
        return commands.get(model)
    else:
        raise Exception('The number of points for the linear frequency sweep is invalid: {}'.format(arg))


def lin_freq_mode(model):
    """This action should select the linear frequency sweep mode"""
    commands = {
        Model.HP_8753D: 'LINFREQ',
    }
    return commands.get(model)


def avg_factor(model, arg):
    """This action should set the averaging factor"""
    argument_valid = {
        Model.HP_8753D: arg in range(1, 1000),
    }

    commands = {
        Model.HP_8753D: 'AVERFACT {}'.format(arg),
    }
    if argument_valid.get(model):
        return commands.get(model)
    else:
        raise Exception('The averaging factor is invalid: {}'.format(arg))


def avg_on(model):
    """This action should turn ON averaging"""
    commands = {
        Model.HP_8753D: 'AVERO1',
    }
    return commands.get(model)


def avg_reset(model):
    """This action should restart the averaging"""
    commands = {
        Model.HP_8753D: 'AVERREST',
    }
    return commands.get(model)


def if_bw(model, arg):
    """This action should set the IF bandwidth"""
    argument_valid = {
        Model.HP_8753D: arg == 10 or arg == 30 or arg == 100 or arg == 300 or arg == 1000 or arg == 3000 or arg == 3700,
    }

    commands = {
        Model.HP_8753D: 'IFBW {} HZ'.format(arg),
    }
    if argument_valid.get(model):
        return commands.get(model)
    else:
        raise Exception('The IF bandwidth value is invalid: {} Hz'.format(arg))


def s21(model):
    """This action should select S21 for the active channel"""
    commands = {
        Model.HP_8753D: 'S21',
    }
    return commands.get(model)


def s11(model):
    """This action should select S11 for the active channel"""
    commands = {
        Model.HP_8753D: 'S11',
    }
    return commands.get(model)


def polar(model):
    """This action should select the polar display format"""
    commands = {
        Model.HP_8753D: 'POLA'
    }
    return commands.get(model)


def polar_log_marker(model):
    """This action should select log markers as the readout format for polar display"""
    commands = {
        Model.HP_8753D: 'POLMLOG'
    }
    return commands.get(model)


def auto_scale(model):
    """This action should auto scale the active channel"""
    commands = {
        Model.HP_8753D: 'AUTO',
    }
    return commands.get(model)


def data_to_mem(model):
    """This action should store the trace in channel memory"""
    commands = {
        Model.HP_8753D: 'DATI',
    }
    return commands.get(model)


def display_data_and_mem(model):
    """This action should display both data and memory of the active channel"""
    commands = {
        Model.HP_8753D: 'DISPDATM',
    }
    return commands.get(model)


def output_formatted_data(model):
    """This action should output the formatted trace data the active channel
    because data is in polar for this project, returned data should be real-imaginary pairs"""
    commands = {
        Model.HP_8753D: 'OUTPFORM',
    }
    return commands.get(model)


def cal_s11_1_port(model):
    """This action should begin an S11 1-port calibration sequence"""
    commands = {
        Model.HP_8753D: 'CALIS111',
    }
    return commands.get(model)


def cal_s11_1_port_open(model):
    """This action should select the open class"""
    commands = {
        Model.HP_8753D: 'CLASS11A',
    }
    return commands.get(model)


def cal_s11_1_port_short(model):
    """This action should select the short class"""
    commands = {
        Model.HP_8753D: 'CLASS11B',
    }
    return commands.get(model)


def cal_s11_1_port_load(model):
    """This action should select the load class"""
    commands = {
        Model.HP_8753D: 'CLASS11C',
    }
    return commands.get(model)


def save_1_port_cal(model):
    """This action should complete the 1-port calibration sequence"""
    commands = {
        Model.HP_8753D: 'SAV1',
    }
    return commands.get(model)


def correction_on(model):
    """This action should turn error correction ON"""
    commands = {
        Model.HP_8753D: 'CORRON',
    }
    return commands.get(model)
