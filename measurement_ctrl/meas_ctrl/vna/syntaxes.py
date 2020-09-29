from enum import Enum, auto


class Action(Enum):
    RESET = auto()
    FORM2 = auto()
    EDIT_LIST = auto()
    ADD_LIST_FREQ = auto()
    LIST_FREQ_MODE = auto()
    CLEAR_LIST = auto()
    LIN_FREQ_START = auto()
    LIN_FREQ_END = auto()
    LIN_FREQ_POINTS = auto()
    LIN_FREQ_MODE = auto()
    AVG_FACTOR = auto()
    AVG_ON = auto()
    AVG_RESET = auto()
    IF_BW = auto()
    S21 = auto()
    S11 = auto()
    POLAR = auto()
    POLAR_LOG_MARKER = auto()
    AUTO_SCALE = auto()
    DATA_TO_MEM = auto()
    DISPLAY_DATA_AND_MEM = auto()
    OUTPUT_FORMATTED_DATA = auto()
    CAL_S11_1_PORT = auto()
    CAL_S11_1_PORT_OPEN = auto()
    CAL_S11_1_PORT_SHORT = auto()
    CAL_S11_1_PORT_LOAD = auto()
    SAVE_1_PORT_CAL = auto()
    CORRECTION_ON = auto()


class Model(Enum):
    HP_8753D = auto()


def check_model(string):
    if '8753D' in string:
        return Model.HP_8753D
    else:
        raise Exception('Model is either not supported, or model is not found in query message: {}'.format(string))


def find_command(model, action, arg=0):
    if action == Action.RESET:
        return reset(model)
    elif action == Action.FORM2:
        return form2(model)
    elif action == Action.EDIT_LIST:
        return edit_list(model)
    elif action == Action.ADD_LIST_FREQ:
        return add_list_freq(model, arg)
    elif action == Action.LIST_FREQ_MODE:
        return list_freq_mode(model)
    elif action == Action.CLEAR_LIST:
        return clear_list(model)
    elif action == Action.LIN_FREQ_START:
        return lin_freq_start(model, arg)
    elif action == Action.LIN_FREQ_END:
        return lin_freq_end(model, arg)
    elif action == Action.LIN_FREQ_POINTS:
        return lin_freq_points(model, arg)
    elif action == Action.LIN_FREQ_MODE:
        return lin_freq_mode(model)
    elif action == Action.AVG_FACTOR:
        return avg_factor(model, arg)
    elif action == Action.AVG_ON:
        return avg_on(model)
    elif action == Action.AVG_RESET:
        return avg_reset(model)
    elif action == Action.IF_BW:
        return if_bw(model, arg)
    elif action == Action.S21:
        return s21(model)
    elif action == Action.S11:
        return s11(model)
    elif action == Action.POLAR:
        return polar(model)
    elif action == Action.POLAR_LOG_MARKER:
        return polar_log_marker(model)
    elif action == Action.AUTO_SCALE:
        return auto_scale(model)
    elif action == Action.DATA_TO_MEM:
        return data_to_mem(model)
    elif action == Action.DISPLAY_DATA_AND_MEM:
        return display_data_and_mem(model)
    elif action == Action.OUTPUT_FORMATTED_DATA:
        return output_formatted_data(model)
    elif action == Action.CAL_S11_1_PORT:
        return cal_s11_1_port(model)
    elif action == Action.CAL_S11_1_PORT_OPEN:
        return cal_s11_1_port_open(model)
    elif action == Action.CAL_S11_1_PORT_SHORT:
        return cal_s11_1_port_short(model)
    elif action == Action.CAL_S11_1_PORT_LOAD:
        return cal_s11_1_port_load(model)
    elif action == Action.SAVE_1_PORT_CAL:
        return save_1_port_cal(model)
    elif action == Action.CORRECTION_ON:
        return correction_on(model)
    else:
        raise Exception('Invalid action, find_command() does the recognize the action: {}'.format(action))


# this action should perform a full reset on the VNA
def reset(model):
    commands = {
        Model.HP_8753D: 'PRES',
    }
    return commands.get(model)


# this action should set the array data from the VNA to be transferred in ASCII floating point format
def form2(model):
    commands = {
        Model.HP_8753D: 'FORM2',
    }
    return commands.get(model)


# this action should prompt VNA to edit the list frequency table
def edit_list(model):
    commands = {
        Model.HP_8753D: 'EDITLIST',
    }
    return commands.get(model)


# this action should contain 3 steps:
# 1. Add a new segment
# 2. Modify the center frequency of the segment
# 3. Done with segment
def add_list_freq(model, arg):
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


# this action should select the list frequency sweep mode
def list_freq_mode(model):
    commands = {
        Model.HP_8753D: 'LISFREQ',
    }
    return commands.get(model)


# this action should clear the selected list
def clear_list(model):
    commands = {
        Model.HP_8753D: 'CLEL',
    }
    return commands.get(model)


# this action should set the start frequency for a linear frequency sweep
def lin_freq_start(model, arg):
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


# this action should set the stop frequency for a linear frequency sweep
def lin_freq_end(model, arg):
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


# this action should set the number of points for a linear frequency sweep
def lin_freq_points(model, arg):
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


# this action should select the linear frequency sweep mode
def lin_freq_mode(model):
    commands = {
        Model.HP_8753D: 'LINFREQ',
    }
    return commands.get(model)


# this action should set the averaging factor
def avg_factor(model, arg):
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


# this action should turn ON averaging.
def avg_on(model):
    commands = {
        Model.HP_8753D: 'AVERO1',
    }
    return commands.get(model)


# this action should restart the averaging
def avg_reset(model):
    commands = {
        Model.HP_8753D: 'AVERREST',
    }
    return commands.get(model)


# this action should set the IF bandwidth
def if_bw(model, arg):
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


# this action should select S21 for the active channel
def s21(model):
    commands = {
        Model.HP_8753D: 'S21',
    }
    return commands.get(model)


# this action should select S11 for the active channel
def s11(model):
    commands = {
        Model.HP_8753D: 'S11',
    }
    return commands.get(model)


# this action should select the polar display format
def polar(model):
    commands = {
        Model.HP_8753D: 'POLA'
    }
    return commands.get(model)


# this action should select log markers as the readout format for polar display
def polar_log_marker(model):
    commands = {
        Model.HP_8753D: 'POLMLOG'
    }
    return commands.get(model)


# this action should auto scale the active channel
def auto_scale(model):
    commands = {
        Model.HP_8753D: 'AUTO',
    }
    return commands.get(model)


# this action should store the trace in channel memory
def data_to_mem(model):
    commands = {
        Model.HP_8753D: 'DATI',
    }
    return commands.get(model)


# this action should display both data and memory of the active channel
def display_data_and_mem(model):
    commands = {
        Model.HP_8753D: 'DISPDATM',
    }
    return commands.get(model)


# this action should output the formatted trace data the active channel
# because data is in polar for this project, returned data should be real-imaginary pairs
def output_formatted_data(model):
    commands = {
        Model.HP_8753D: 'OUTPFORM',
    }
    return commands.get(model)


# this action should begin an S11 1-port calibration sequence
def cal_s11_1_port(model):
    commands = {
        Model.HP_8753D: 'CALIS111',
    }
    return commands.get(model)


# this action should select the open class
def cal_s11_1_port_open(model):
    commands = {
        Model.HP_8753D: 'CLASS11A',
    }
    return commands.get(model)


# this action should select the short class
def cal_s11_1_port_short(model):
    commands = {
        Model.HP_8753D: 'CLASS11B',
    }
    return commands.get(model)


# this action should select the load class
def cal_s11_1_port_load(model):
    commands = {
        Model.HP_8753D: 'CLASS11C',
    }
    return commands.get(model)


# this action should complete the 1-port calibration sequence
def save_1_port_cal(model):
    commands = {
        Model.HP_8753D: 'SAV1',
    }
    return commands.get(model)


# this action should turn error correction ON
def correction_on(model):
    commands = {
        Model.HP_8753D: 'CORRON',
    }
    return commands.get(model)
