################################################################################
#
#  Description:
#      This file contains the implementation of a class for parsing packets
#      returned by the QPT Positioner, and updating QPT status & error
#      fields in response to the both the type of return packet, and
#      the data returned by the QPT in said packet.
#
#  Status:
#      By and large this class is functional, meaning that the packets all get
#      parsed correctly, however, there is work remaining to be done to
#      add PyQt signals so that the parser can emit errors to the Gui framework
#      and possibly throw exceptions, unsure if that will be necessary or if
#      emitting signals to the Gui will be enough.
#
#  Dependencies:
#      PyVISA Version: 1.10.1
#
#  Author: Thomas Hoover
#  Date: 20200806
#  Built with Python Version: 3.8.5
#
################################################################################
from time import time, sleep
import integer as qi
import packet as pkt
from constants import BIT0, BIT1, BIT2, BIT3, BIT4, BIT5, BIT6, BIT7


class Parser:
    def __init__(self):
        self.active = True 


    def parse(self, rx, qpt):
        if rx is not None:
            rx = bytes(pkt.strip_esc(rx))
            cmd = rx[1]

            if pkt.valid_LRC(rx[1:-1]) is True:
                if is_move_cmd(cmd):
                    self.update_qpt_status(rx, qpt)
                elif is_angle_correction_cmd(cmd):
                    self.update_angle_corrections(rx, qpt)
                elif is_soft_limits_cmd(cmd):
                    self.update_soft_limits(rx, qpt)
                elif is_potentiometer_center_cmd(cmd):
                    self.update_potentiometer_center(rx, qpt)
                elif is_min_speed_cmd(cmd):
                    self.update_min_speed(rx, qpt)
                elif is_max_speed_cmd(cmd):
                    self.update_max_speed(rx, qpt)
                elif is_comm_timeout_cmd(cmd):
                    self.update_comm_timeout(rx, qpt)


    def update_curr_position(self, rx, qpt):
        with qpt.curr_lock:
            qpt.curr_position = qi.Coordinate(rx[2:4], rx[4:6], fromqpt=True)
            qpt.signals.currentPan.emit('{:0.2f}'.format(qpt.curr_position.pan_angle()))
            qpt.signals.currentTilt.emit('{:0.2f}'.format(qpt.curr_position.tilt_angle()))


    def update_pan_status(self, rx, qpt):
        qpt.sfault_cs_soft_limit = bool(rx[6] & BIT7)
        qpt.sfault_ccw_soft_limit = bool(rx[6] & BIT6)
        qpt.hfault_cw_hard_limit = bool(rx[6] & BIT5)
        qpt.hfault_ccw_hard_limit = bool(rx[6] & BIT4)
        qpt.hfault_pan_timeout = bool(rx[6] & BIT3)
        qpt.hfault_pan_direction_error = bool(rx[6] & BIT2)
        qpt.hfault_pan_current_overload = bool(rx[6] & BIT1)
        qpt.sfault_pan_resolver_fault = bool(rx[6] & BIT0)


    def update_tilt_status(self, rx, qpt):
        qpt.sfault_up_soft_limit = bool(rx[7] & BIT7)
        qpt.sfault_down_soft_limit = bool(rx[7] & BIT6)
        qpt.hfault_up_hard_limit = bool(rx[7] & BIT5)
        qpt.hfault_down_hard_limit = bool(rx[7] & BIT4)
        qpt.hfault_tilt_timeout = bool(rx[7] & BIT3)
        qpt.hfault_tilt_direction_error = bool(rx[7] & BIT2)
        qpt.hfault_tilt_current_overload = bool(rx[7] & BIT1)
        qpt.sfault_tilt_resolver_fault = bool(rx[7] & BIT0)


    def update_general_status(self, rx, qpt):
        qpt.status_high_res = bool(rx[8] & BIT7)
        qpt.status_executing = bool(rx[8] & BIT6)
        qpt.status_dest_coords = bool(rx[8] & BIT5)
        qpt.status_soft_limit_override = bool(rx[8] & BIT4)
        qpt.pan_status_cw_moving = bool(rx[8] & BIT3)
        qpt.pan_status_ccw_moving = bool(rx[8] & BIT2)
        qpt.tilt_status_up_moving = bool(rx[8] & BIT1)
        qpt.tilt_status_down_moving = bool(rx[8] & BIT0)


    def update_qpt_status(self, rx, qpt):
        if rx[1] == 0x31:
            self.update_curr_position(rx, qpt)
        self.update_pan_status(rx, qpt)
        self.update_tilt_status(rx, qpt)
        self.update_general_status(rx, qpt)


    def update_soft_limits(self, rx, qpt):
        if rx[2] == 0 or rx[2] == 1:
            limit = qi.Coordinate(rx[3:5], 0, fromqpt=True).pan_angle()
            if rx[2] == 0:
                qpt.pan_cw_soft_limit = limit
            elif rx[2] == 1:
                qpt.pan_ccw_soft_limit = limit
        elif rx[2] == 2 or rx[2] == 3:
            limit = qi.Coordinate(0, rx[3:5], fromqpt=True).tilt_angle()
            if rx[2] == 2:
                qpt.tilt_up_soft_limit = limit
            elif rx[2] == 3:
                qpt.tilt_down_soft_limit = limit


    def update_potentiometer_center(self, rx, qpt):
        qpt.pan_center_RU = int.from_bytes(rx[2:4], byteorder='little', signed=True)
        qpt.tilt_center_RU = int.from_bytes(rx[4:6], byteorder='little', signed=True)


    def update_min_speed(self, rx, qpt):
        qpt.pan_min_speed = rx[2]
        qpt.tilt_min_speed = rx[3]


    def update_max_speed(self, rx, qpt):
        qpt.pan_max_speed = rx[2]
        qpt.tilt_max_speed = rx[3]


    def update_angle_corrections(self, rx, qpt):
        qpt.angle_corrections = qi.Coordinate(rx[2:4], rx[4:6], fromqpt=True)


    def update_comm_timeout(self, rx, qpt):
        qpt.comms_timeout = rx[2]    
"""End Parser Class"""


"""Parser Helper Functions"""
def is_move_cmd(cmd):
    if cmd == 0x31 or cmd == 0x33 or cmd == 0x34 or cmd == 0x35:
        return True
    return False


def is_angle_correction_cmd(cmd):
    if cmd == 0x70 or cmd == 0x80 or cmd == 0x82 or cmd == 0x84:
        return True
    return False


def is_soft_limits_cmd(cmd):
    if cmd == 0x71 or cmd == 0x81:
        return True
    return False


def is_potentiometer_center_cmd(cmd):
    if cmd == 0x90 or cmd == 0x91:
        return True
    return False


def is_min_speed_cmd(cmd):
    if cmd == 0x92 or cmd == 0x93:
        return True
    return False


def is_max_speed_cmd(cmd):
    if cmd == 0x98 or cmd == 0x99:
        return True
    return False


def is_comm_timeout_cmd(cmd):
    if cmd == 0x96:
        return True
    return False

