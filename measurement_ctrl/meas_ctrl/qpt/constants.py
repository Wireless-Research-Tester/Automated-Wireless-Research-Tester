################################################################################
#
#  Description:
#
#
#  Status:
#
#
#  Dependencies:
#      PyVISA Version: 1.10.1
#
#  Author: Thomas Hoover
#  Date: 20200417
#  Built with Python Version: 3.8.2
#
################################################################################
import enum


# Control Chars
CTRL = {
    'STX' : b'\x02', # Start-of-Text Char
    'ETX' : b'\x03', # End-of-Text Char
    'ACK' : b'\x06', # Acknowledged Char
    'NAK' : b'\x15', # Not-Acknowledged Char
}


# Positioner Commands 
CMD = {
    'Get_Status_Jog'         : b'\x31', # Get Status/Jog
    'Move_To_Coords'         : b'\x33', # Move To Entered Coordinates
    'Move_To_Delta'          : b'\x34', # Move To Delta Coordinates
    'Move_To_Zero'           : b'\x35', # Move To Absolute 0/0
    'Get_Angle_Correction'   : b'\x70', # Get Pan & Tilt Angle Correction
    'Get_Soft_Limit'         : b'\x71', # Get Soft Limit
    'Set_Angle_Correction'   : b'\x80', # Set Pan & Tilt Angle Correction
    'Set_Soft_Limit_To_Cur'  : b'\x81', # Set Soft Limit to Current Possition
    'Align_Angles_To_Center' : b'\x82', # Align Angles to Center
    'Clear_Angle_Correction' : b'\x84', # Clear Angle Correction
    'Get_Center_Position'    : b'\x90', # Get Center Position in RU's'
    'Set_Center_Position'    : b'\x91', # Set Center Position
    'Get_Minimum_Speeds'     : b'\x92', # Get Minimum Speeds
    'Set_Minimum_Speeds'     : b'\x93', # Set Minimum Speeds
    'Communication_Timeout'  : b'\x96', # Get/Set Communication Timeout
    'Get_Maximum_Speeds'     : b'\x98', # Get Maximum Speeds
    'Set_Maximum_Speeds'     : b'\x99', # Set Maximum Speeds
}


# Static Transmission Packets
STATIC_TX = {
    'GET_STATUS'             : b'\x02\x31\x00\x00\x00\x00\x00\x31\x03',
    'STOP'                   : b'\x02\x31\x1b\x82\x00\x00\x00\x00\x33\x03',
    'FAULT_RESET'            : b'\x02\x31\x01\x00\x00\x00\x00\x30\x03',
    'MOVE_TO_ABSOLUTE_ZERO'  : b'\x02\x35\x35\x03',
    'GET_ANGLE_CORRECTION'   : b'\x02\x70\x70\x03',
    'ALIGN_ANGLES_TO_CENTER' : b'\x02\x82\x82\x03',
    'CLEAR_ANGLE_CORRECTION' : b'\x02\x84\x84\x03',
    'SET_CENTER_POSITION'    : b'\x02\x91\x91\x03',
    'GET_MINIMUM_SPEEDS'     : b'\x02\x92\x92\x03',
    'GET_MAXIMUM_SPEEDS'     : b'\x02\x98\x98\x03',
}


# Escape Character and Escape Mask
ESC =  b'\x1b' # Used to escape a data or LRC byte that matches a control char
ESC_MASK = int.from_bytes(b'\x80', byteorder='little') # Bitmask used to set and clear bit 7 in data or LRC bytes that match control chars


# Bitmasks used to set and clear bits in data or control bytes
BIT0 = int.from_bytes(b'\x01', byteorder='little')
BIT1 = int.from_bytes(b'\x02', byteorder='little')
BIT2 = int.from_bytes(b'\x04', byteorder='little')
BIT3 = int.from_bytes(b'\x08', byteorder='little')
BIT4 = int.from_bytes(b'\x10', byteorder='little')
BIT5 = int.from_bytes(b'\x20', byteorder='little')
BIT6 = int.from_bytes(b'\x40', byteorder='little')
BIT7 = int.from_bytes(b'\x80', byteorder='little')


# Errors
@enum.unique
class StatusCodes(enum.IntEnum):
    """Specifies the status codes the positioner can have.
    """

    # Pan Status Codes
    sfault_clockwise_soft_limit = -1000
    sfault_counter_clockwise_soft_limit = -1001
    hfault_clockwise_hard_limit = -1002
    hfault_counter_clockwise_hard_limit = -1003
    hfault_pan_timeout = -1004
    hfault_pan_direction_error = -1005
    hfault_pan_current_overload = -1006
    sfault_pan_resolver_fault = -1007
    status_clockwise_moving = 1000
    status_counter_clockwise_moving = 1001

    # Tilt Status Codes
    sfault_up_soft_limit = -2000
    sfault_down_soft_limit = -2001
    hfault_up_hard_limit = -2002
    hfault_down_hard_limit = -2003
    hfault_tilt_timeout = -2004
    hfault_tilt_direction_error = -2005
    hfault_tilt_current_overload = -2006
    sfault_tilt_resolver_fault = -2007
    status_up_moving = 2000
    status_down_moving = 2001

    # General Status Codes
    status_high_res = 3000
    status_low_res = -3000
    status_executing = 3001
    status_not_executing = -3001
    status_destination = 3002
    status_not_destination = -3002
    status_soft_limit_override = 3003
    status_not_soft_limit_override = -3003
    
