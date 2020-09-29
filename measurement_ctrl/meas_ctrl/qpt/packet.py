################################################################################
#
#  Description: 
#      This file contains a collection of functions to facilitate the creation
#      of Tx packets. The functions fall into two categories:
#          1. Packet utils for LRC Checksum calculation and handling packet ESC
#             chars.
#          2. Packet creation functions for producing transmittable packets.
#
#  Status:
#      Good enough for the short term. No changes will probably be needed for
#      the LRC/ESC functions and alot of the packet generation functions are
#      sufficient, however, as the positioner comms system begins to be 
#      integrated with the rest of the software, particularly the VNA, more
#      functionality will need to be added to facilitate a robust, stable
#      communication system with the QPT. Also, eventually the configuration
#      api for the QPT Positioner will need improvement, which will necessitate
#      adding functionality here.
#
#  Author: Thomas Hoover
#  Date: 20200417
#  Built with Python Version: 3.8.2
#
################################################################################
import qpt.integer as qi
from qpt.constants import CTRL, ESC, ESC_MASK, STATIC_TX


ctrl_chars = CTRL.values()


def generate_LRC(data):
    """Generates LRC Checksum for packet based on data.

    data: Bytes representing the command number and packet data to be transmitted.
    returns: Byte representation of the LRC checksum for the given data.
    """
    checksum = 0
    for item in data:
        checksum = checksum ^ item
    return (checksum).to_bytes(1, byteorder='little')


def valid_LRC(data):
    """Determines if the LRC Checksum of a packet is valid.

    data: Bytes representing the command number, packet data, and LRC checksum of
        a received packet.
    returns: True if the transmitted LRC checksum matches the calculated 
        LRC checksum
    """
    checksum = generate_LRC(data)
    if checksum == b'\x00':
        return True
    return False


def insert_esc(data):
    """Inserts escape char 0x1b before any data value, including the LRC,
    that matches a control char, then sets bit 7 of the byte matching a 
    control char.

    data: Bytes representing the complete packet, aside from the STX and ETX 
        control chars.
    returns: Packet that is ready to transmit once STX and ETX are added.
    """
    tx_packet = bytes()
    # ctrl = CTRL.values()
    for item in data:
        val = item.to_bytes(1, byteorder='little')
        if val in ctrl_chars or val == ESC:
            tx_packet += b'\x1b'
            tx_packet += (item | ESC_MASK).to_bytes(1, byteorder='little')
        else:
            tx_packet += val
    return tx_packet


def strip_esc(data):
    """Strips escape char 0x1b from infront of data values, including the LRC,
    that match a control char, then clears bit 7 of the byte matching a 
    control char.

    data: Bytes representing the complete packet, including the STX and ETX 
        control chars.
    returns: Packet that is ready to be parsed.
    """
    rx = list(data)
    rx_packet = bytes()
    include_next = False
    for i in range(len(rx)):
        val = rx[i].to_bytes(1, byteorder='little')
        if val != ESC or include_next is True:
            rx_packet += val
            include_next = False
        else:
            rx[i+1] = (rx[i+1] & (~ESC_MASK))
            include_next = True
    return rx_packet


def get_status():
    """Command 0x31: "Get Status/Jog"
    Creates packet to query the status of the QPT Positioner.

    return: Packet that is ready to transmit.
    """
    return STATIC_TX['GET_STATUS']


def jog_positioner(
        pan_speed,
        pan_dir,
        tilt_speed,
        tilt_dir,
        override_soft_limit=False):
    """Command 0x31: "Get Status/Jog"
    Creates packet to jog the QPT positioner in pan_dir and tilt_dir 
    at pan_speed and tilt_speed.

    pan_speed: must be between 0-127. Speed of 0 means no movement.
    pan_dir: 1 for CW, 0 for CCW
    tilt_speed: must be between 0-127. Speed of 0 means no movement.
    tilt_dir: 1 for UP, 0 for DOWN
    override_soft_limit: kwarg default is False, passing in a value of True
      for the kwarg will allow for the overriding of soft limits during a jog.
      THIS SHOULD ONLY BE SET WHEN INITIALLY SETTING UP THE SOFT LIMITS. Its
      current setting will be returned in the OSLR bit.
    returns: Packet that is ready to transmit.

    NOTE: Client should observe the angular readings during jog to confirm
      the motors are moving the proper direction and are not stalled.

    TODO: Add tests to test_packet.py, and verify it functions correctly.
    """
    if pan_speed >= 0 and pan_speed <= 127 and tilt_speed >= 0 and tilt_speed <= 127:
        pan = qi.Integer((pan_speed<<1) | pan_dir).lower_byte()
        tilt = qi.Integer((tilt_speed<<1) | tilt_dir).lower_byte()
        if override_soft_limit is True:
            tx_data = bytes(b'\x31' + b'\x04' + pan + tilt + b'\x00\x00')
        else:
            tx_data = bytes(b'\x31' + b'\x00' + pan + tilt + b'\x00\x00')
        LRC = generate_LRC(tx_data)
        return bytes(b'\x02' + insert_esc(tx_data + LRC) + b'\x03')
    return None


def stop():
    """Command 0x31: "Get Status/Jog"
    Creates packet to STOP the QPT Positioner from continuing an automated move.

    returns: Packet that is ready to transmit.
    """
    return STATIC_TX['STOP']


def fault_reset():
    """Command 0x31: "Get Status/Jog"
    Creates packet to reset latching faults, which are the hard faults:
        Timeout (TO): A commanded axis has not moved within the prescribed timeframe
        Direction Error (DE): A commanded axis has moved in the wrong direction.
        Current Overload (OL): A commanded axis has tripped the current overload.

    A timeout fault will be set if an axis fails to move witin 1 second,
      which may be the result of a stalled motor, an overloaded platform,
      or a physical obstruction prohibiting motor movement.
    A directional error fault will be set if an axis is detected as moving
      in the wrong direction. This may be the result of improper motor wiring.
    
    NOTE: The TO and DE faults will only occur during automated moves
      - 'Move_To_Coords' 0x33
      - 'Move_To_Delta'  0x34
      - 'Move_To_Zero'   0x35

    If a motor either has its current draw exceed the allowable value, or
      if its junction temperature exceeds 145 degrees C, an overload fault
      will be set.

    returns: Packet that is ready to transmit.
    """
    return STATIC_TX['FAULT_RESET']


def move_to_entered_coords(coord):
    """Command 0x33: "Move To Entered Coordinates"
    Creates packet to move the QPT Positioner to the entered coordinate.

    coord: qpt.integer.Coordinate to move the positioner to.
    returns: Packet that is ready to transmit.
    """
    tx_data = bytes(b'\x33' + coord.to_bytes())
    LRC = generate_LRC(tx_data)
    return bytes(b'\x02' + insert_esc(tx_data + LRC) + b'\x03')


def move_to_delta_coords(coord):
    """Command 0x34: "Move To Delta Coordinates"
    Creates a packet to move the QPT Positioner to the delta provided.

    coord: qpt.integer.Coordinate representing the delta to move the positioner to.
    returns: Packet that is ready to transmit.
    """
    tx_data = bytes(b'\x34' + coord.to_bytes())
    LRC = generate_LRC(tx_data)
    return bytes(b'\x02' + insert_esc(tx_data + LRC) + b'\x03')


def move_to_absolute_zero():
    """Command 0x35: "Move To Absolute 0/0"
    Creates packet to move the QPT Positioner to absolute 0/0.

    returns: Packet that is ready to transmit.
    """
    return STATIC_TX['MOVE_TO_ABSOLUTE_ZERO']


def get_angle_correction():
    """Command 0x70: "Get Pan & Tilt Angle Correction"
    Creates packet to query the QPT Positioner for the current angle correction.

    returns: Packet that is ready to transmit.
    """
    return STATIC_TX['GET_ANGLE_CORRECTION']


def get_soft_limit(axis):
    """Command 0x71: "Get Soft Limit"
    Creates packet to query the QPT Positioner for the current soft limit on
    the specified axis.

    axis:
        0 = CW
        1 = CCW
        2 = UP
        3 = DOWN
    returns: Packet that is ready to transmit.

    TODO: Add tests to test_packet.py, and verify it functions correctly.    
    """
    if axis in range(4):
        tx_data = bytes(b'\x71' + (axis).to_bytes(1, byteorder='little'))
        LRC = generate_LRC(tx_data)
        return bytes(b'\x02' + insert_esc(tx_data + LRC) + b'\x03')
    return None


def set_angle_correction(coord):
    """Command 0x80: "Set Pan & Tilt Angle Correction"
    Creates packet to set the QPT Positioner's pan and tilt angle corrections
    to the pan and tilt angle passed to the function in coord.

    coord: qpt.integer.Coordinate containing the pan and tilt angles to set
        the positioner angle correction offsets to.
    returns: Packet that is ready to transmit.

    TODO: Add tests to test_packet.py, and verify it functions correctly.
    """
    if coord is not None:
        tx_data = bytes(b'\x80' + coord.to_bytes())
        LRC = generate_LRC(tx_data)
        return bytes(b'\x02' + insert_esc(tx_data + LRC) + b'\x03')
    return None


def set_soft_limit_to_current_position(axis):
    """Command 0x81: "Set Soft Limit To Current Position"
    Creates packet to set the QPT Positioner's soft limit to the current
    position on the specified axis.

    axis:
        0 = CW
        1 = CCW
        2 = UP
        3 = DOWN
    returns: Packet that is ready to transmit.

    TODO: Add tests to test_packet.py, and verify it functions correctly.  
    """
    if axis in range(4):
        tx_data = bytes(b'\x81' + (axis).to_bytes(1, byteorder='little'))
        LRC = generate_LRC(tx_data)
        return bytes(b'\x02' + insert_esc(tx_data + LRC) + b'\x03')
    return None


def align_angles_to_center():
    """Command 0x82: "Align Angles To Center"
    Creates packet to set the QPT Positioner's angle corrections so that the 
    current position is considered a center position displaying a pan and tilt
    angle of 0 degrees.

    returns: Packet that is ready to transmit.
    """
    return STATIC_TX['ALIGN_ANGLES_TO_CENTER']


def clear_angle_correction():
    """Command 0x84: "Clear Angle Correction"
    Creates packet to reset any angular corrections to zero, realigning the platform
    angular display to the true 0/0 position.

    returns: Packet that is ready to transmit.
    """
    return STATIC_TX['CLEAR_ANGLE_CORRECTION']


def get_center_position_in_RUs():
    """Command 0x90: "Get Center Position in RU's"
    Creates packet to get the center position in resolver units (RU's)

    returns: Packet that is ready to transmit.
    """
    return bytes.fromhex('02 90 90 03')


def set_center_position():
    """Command 0x91: "Set Center Position"
    Creates packet to set the center position for the pan/tilt resolvers.

    returns: Packet that is ready to transmit.
    """
    return STATIC_TX['SET_CENTER_POSITION']


def get_minimum_speeds():
    """Command 0x92: "Get Minimum Speeds"
    Creates packet to query the QPT Positioner for the minimum speed of both
    the pan and tilt motors.

    returns: Packet that is ready to transmit.
    """
    return STATIC_TX['GET_MINIMUM_SPEEDS']


def set_minimum_speeds(pan_speed, tilt_speed):
    """Command 0x93: "Set Minimum Speeds"
    Creates packet to set the QPT Positioner minimum speeds to
    pan_speed and tilt_speed.

    pan_speed: must be between 0-255
    tilt_speed: must be between 0-255
    returns: Packet that is ready to transmit.

    TODO: Add tests to test_packet.py, and verify it functions correctly.
    """
    if pan_speed >= 0 and pan_speed <= 255 and tilt_speed >= 0 and tilt_speed <= 255:
        p = (pan_speed).to_bytes(1, byteorder='little')
        t = (tilt_speed).to_bytes(1, byteorder='little')
        tx_data = bytes(b'\x93' + p + t)
        LRC = generate_LRC(tx_data)
        return bytes(b'\x02' + insert_esc(tx_data + LRC) + b'\x03')
    return None


def get_set_communication_timeout(query, timeout):
    """Command 0x96: "Get/Set Communication Timeout"
    Creates packet to either get or set the communication timeout based on
    the value of query.

    query: if query is True query timeout, if query is False set timeout
    timeout: must be between 0-120 (in seconds)
    returns: Packet that is ready to transmit.

    TODO: Add tests to test_packet.py, and verify it functions correctly.
    """
    if query is True:
        tx_data = bytes(b'\x96\x80')
        LRC = generate_LRC(tx_data)
        return bytes(b'\x02' + insert_esc(tx_data + LRC) + b'\x03')
    elif query is False and timeout >= 0 and timeout <= 120:
        tx_data = timeout.to_bytes(1, byteorder='little')
        LRC = generate_LRC(tx_data)
        return bytes(b'\x02' + insert_esc(tx_data + LRC) + b'\x03')
    return None


def get_maximum_speeds():
    """Command 0x98: "Get Maximum Speeds"
    Creates packet to query the QPT Positioner for the maximum speed of both
    the pan and tilt motors.

    returns: Packet that is ready to transmit.
    """
    return STATIC_TX['GET_MAXIMUM_SPEEDS']


def set_maximum_speeds(pan_speed, tilt_speed):
    """Command 0x99: "Set Maximum Speeds"
    Creates packet to set the QPT Positioner maximum speeds to
    pan_speed and tilt_speed.

    pan_speed: must be between 1-255
    tilt_speed: must be between 1-255
    returns: Packet that is ready to transmit.

    TODO: Add tests to test_packet.py, and verify it functions correctly.
    """
    if pan_speed >= 1 and pan_speed <= 255 and tilt_speed >= 1 and tilt_speed <= 255:
        p = (pan_speed).to_bytes(1, byteorder='little')
        t = (tilt_speed).to_bytes(1, byteorder='little')
        tx_data = bytes(b'\x99' + p + t)
        LRC = generate_LRC(tx_data)
        return bytes(b'\x02' + insert_esc(tx_data + LRC) + b'\x03')
    return None

