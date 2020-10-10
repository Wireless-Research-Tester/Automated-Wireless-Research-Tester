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
import time
from threading import Lock

import pyvisa as visa

import integer as qi
import packet as pkt
from constants import BIT0, BIT1, BIT2, BIT3, BIT4, BIT5, BIT6, BIT7
from packet_parser import Parser

from PyQt5 import QtCore as qtc


class CommsSignals(qtc.QObject):
    pass


class Comms:
    _LIMIT = 25


    def __init__(self, com_port, baud_rate):
        self.rm = visa.ResourceManager()
        self.comms = self.rm.open_resource(com_port)
        self.comms.read_termination = b'\x03'
        self.comms.write_termination = b'\x03'
        self.comms.timeout = 30
        self.comms.baud_rate = baud_rate
        self.comms.stop_bites = visa.constants.StopBits.one
        self.comms.parity = visa.constants.Parity.none
        self.comms.data_bits = 8
        self.connected = self.init_comms_link()


    def init_comms_link(self):
        tries = 0
        rx = self.positioner_query(pkt.get_status())
        while tries < self._LIMIT and rx == None:
            rx = self.positioner_query(pkt.get_status())
            tries = tries + 1
        if rx == None:
            return False
        return True


    def positioner_query(self, msg):
        self.comms.write_raw(msg)
        try:
            time.sleep(.02)
            rx = self.comms.read_raw()
        except visa.errors.VisaIOError as err:
            return None
        return rx


    def clear_rx_buffer(self):
        clear = False
        while clear is False:
            try:
                rx = self.comms.read_raw()
            except visa.errors.VisaIOError as err:
                clear = True
"""End Comms Class"""


class PositionerSignals(qtc.QObject):
    """Defines the signals available from the QPT-130 Positioner"""
    executing   = qtc.pyqtSignal(bool )
    currentPan  = qtc.pyqtSignal(str)
    currentTilt = qtc.pyqtSignal(str)
    softFault   = qtc.pyqtSignal(tuple)
    hardFault   = qtc.pyqtSignal(tuple)


class Positioner:
    def __init__(self, com_port, baud_rate):
        self.comms = Comms(com_port, baud_rate)
        self.p = Parser()
        self.curr_lock = Lock()

        # General Properties
        self.status_executing = False
        self.comms_timeout = False
        self.curr_position = qi.Coordinate(0,0)
        self.dest_position = qi.Coordinate(0,0)
        self.pan_center_RU = 0
        self.tilt_center_RU = 0
        self.status_high_res = True
        self.status_dest_coords = False
        self.status_soft_limit_override = False
        self.angle_corrections = qi.Coordinate(0,0)

        # Pan Properties
        self.pan_min_speed = 0
        self.pan_max_speed = 0
        self.pan_cw_soft_limit = 0
        self.pan_ccw_soft_limit = 0
        self.pan_status_cw_moving = False
        self.pan_status_ccw_moving = False

        # Pan Status
        self.sfault_cw_soft_limit = False
        self.sfault_ccw_soft_limit = False
        self.hfault_cw_hard_limit = False
        self.hfault_ccw_hard_limit = False
        self.hfault_pan_timeout = False
        self.hfault_pan_direction_error = False
        self.hfault_pan_current_overload = False
        self.sfault_pan_resolver_fault = False

        # Tilt Properties
        self.tilt_min_speed = 0
        self.tilt_max_speed = 0
        self.tilt_up_soft_limit = 0
        self.tilt_down_soft_limit = 0
        self.tilt_status_up_moving = False
        self.tilt_status_down_moving = False

        # Tilt Status
        self.sfault_up_soft_limit = False
        self.sfault_down_soft_limit = False
        self.hfault_up_hard_limit = False
        self.hfault_down_hard_limit = False
        self.hfault_tilt_timeout = False
        self.hfault_tilt_direction_error = False
        self.hfault_tilt_current_overload = False
        self.sfault_tilt_resolver_fault = False

        # Initialize positioner signals, properties and status
        self.signals = PositionerSignals()
        self.update_positioner_stats()

        # Jog speed limits
        self.MAX_PAN_TIME = 1240
        self.MIN_PAN_SPEED = 8
        self.MAX_PAN_SPEED = 127

        self.MAX_TILT_TIME = 700
        self.MIN_TILT_SPEED = 17
        self.MAX_TILT_SPEED = 127


    def move_to(self, pan, tilt, move_type='stop'):
        # Set min speed high enough the motors wont timeout while stopping
        self.p.parse(self.comms.positioner_query(pkt.set_minimum_speeds(50,50)),self)

        # Issue the appropriate movement command
        if move_type == 'abs':
            coord = qi.Coordinate(pan,tilt)
            self.p.parse(self.comms.positioner_query(pkt.move_to_entered_coords(coord)),self)
        elif move_type == 'delta':
            coord = qi.Coordinate(pan,tilt)
            self.p.parse(self.comms.positioner_query(pkt.move_to_delta_coords(coord)),self)
        elif move_type == 'zero':
            self.p.parse(self.comms.positioner_query(pkt.move_to_absolute_zero()),self)
        else:
            self.p.parse(self.comms.positioner_query(pkt.stop()),self)

        # Force the positioner to update status before letting it do anything
        # else. This is to ensure that the status_executing flag gets updated
        # after issuing the move command
        time.sleep(.12)
        self.p.parse(self.comms.positioner_query(pkt.get_status()),self)
        time.sleep(.12)


    def get_position(self):
        with self.curr_lock:
            curr = self.curr_position
        return curr


    def get_status(self):
        self.p.parse(self.comms.positioner_query(pkt.get_status()), self)


    def jog_cw(self, pan_speed, target):
        self.p.parse(self.comms.positioner_query(pkt.set_minimum_speeds(8,17)),self)
        if self.curr_position.pan_angle() < target.pan_angle():
            rx = self.comms.positioner_query(pkt.jog_positioner(pan_speed, 1, 0, 0))
            self.p.parse(rx, self)
        else:
            self.move_to(0,0,'stop')


    def jog_ccw(self, pan_speed, target):
        self.p.parse(self.comms.positioner_query(pkt.set_minimum_speeds(8,17)),self)
        if self.curr_position.pan_angle() > target.pan_angle():
            rx = self.comms.positioner_query(pkt.jog_positioner(pan_speed, 0, 0, 0))
            self.p.parse(rx, self)
        else:
            self.move_to(0,0,'stop')


    def jog_up(self, tilt_speed, target):
        self.p.parse(self.comms.positioner_query(pkt.set_minimum_speeds(8,17)),self)
        if self.curr_position.tilt_angle() < target.tilt_angle():
            rx = self.comms.positioner_query(pkt.jog_positioner(0, 0, tilt_speed, 1))
            self.p.parse(rx, self)
        else:
            self.move_to(0,0,'stop')
            

    def jog_down(self, tilt_speed, target):
        self.p.parse(self.comms.positioner_query(pkt.set_minimum_speeds(8,17)),self)
        if self.curr_position.tilt_angle() > target.tilt_angle():
            rx = self.comms.positioner_query(pkt.jog_positioner(0, 0, tilt_speed, 0))
            self.p.parse(rx, self)
        else:
            self.move_to(0,0,'stop')


    def print_curr(self):
        with self.curr_lock:
            print('Current Position => PAN: {:3.2f}, TILT: {:2.2f}, TIME: {:3.4f}'.format(
                self.curr_position.pan_angle(),
                self.curr_position.tilt_angle(),
                time.time()))


    def update_positioner_stats(self):
        self.p.parse(self.comms.positioner_query(pkt.get_status()), self)
        self.p.parse(self.comms.positioner_query(pkt.get_angle_correction()), self)
        self.p.parse(self.comms.positioner_query(pkt.get_soft_limit(0)), self)
        self.p.parse(self.comms.positioner_query(pkt.get_soft_limit(1)), self)
        self.p.parse(self.comms.positioner_query(pkt.get_soft_limit(2)), self)
        self.p.parse(self.comms.positioner_query(pkt.get_soft_limit(3)), self)
        self.p.parse(self.comms.positioner_query(pkt.get_minimum_speeds()), self)
        self.p.parse(self.comms.positioner_query(pkt.get_set_communication_timeout(True,0)), self)
        self.p.parse(self.comms.positioner_query(pkt.get_maximum_speeds()), self)
"""End Positioner Class"""

