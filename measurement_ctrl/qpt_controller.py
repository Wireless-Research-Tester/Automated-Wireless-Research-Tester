###############################################################################
# qpt_controller
# Description:
#
#
# Status:
#
#
# Dependencies: PyQt5
#
# Author: Thomas Hoover
# Date: 20201017
# Built with Python Version: 3.8.2
# For any questions, contact Thomas at tomhoover1@gmail.com
###############################################################################
from PyQt5 import QtCore as qtc

from measurement_ctrl.positioner import Positioner
from measurement_ctrl.integer import Coordinate

from queue import PriorityQueue, Empty, Full
from dataclasses import dataclass, field
from typing import Any
import time
import traceback, sys

@dataclass(order=True)
class QPTMessage:
    """Wrapper for message to be transmitted by the positioner to support
    using a PriorityQueue to synchronize communicates between the 
    main thread/measurement control thread and the positioner control thread
    """ 
    priority: int
    item: Any=field(compare=False)


class QPTMessageQueue(qtc.QObject):
    def __init__(self):
        super().__init__()
        self.q = PriorityQueue()
        self.qpt_connected = False

    def ready4msg(self):
        if self.qpt_connected and not self.q.full():
            return True
        return False

    def clear_Q(self):
        del self.q
        self.q = PriorityQueue()

    @qtc.pyqtSlot(list)
    def q_jog_cw_list(self, args):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(1, ['JogCW', args[0], args[1], args[2]]))

    @qtc.pyqtSlot(bool)
    def q_jog_cw(self, bool_val):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(1, ['JogCW', 'sw']))

    @qtc.pyqtSlot(list)
    def q_jog_ccw_list(self, args):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(1, ['JogCCW', args[0], args[1], args[2]]))

    @qtc.pyqtSlot(bool)
    def q_jog_ccw(self, bool_val):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(1, ['JogCCW', 'sw']))

    @qtc.pyqtSlot(list)
    def q_jog_up_list(self, args):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(1, ['JogUp', args[0], args[1], args[2]]))

    @qtc.pyqtSlot(bool)
    def q_jog_up(self, bool_val):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(1, ['JogUp', 'sw']))

    @qtc.pyqtSlot(list)
    def q_jog_down_list(self, args):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(1, ['JogDown', args[0], args[1], args[2]]))

    @qtc.pyqtSlot(bool)
    def q_jog_down(self, bool_val):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(1, ['JogDown', 'sw']))

    @qtc.pyqtSlot()
    def q_stop(self):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(0, ['Stop']))

    @qtc.pyqtSlot(list)
    def q_move_to(self, args):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(1, ['MoveTo', args[0], args[1], args[2]]))

    @qtc.pyqtSlot()
    def q_zero_offsets(self):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(2, ['ZeroOffsets']))

    @qtc.pyqtSlot()
    def q_align_to_center(self):
        if self.ready4msg():
            self.q.put_nowait(QPTMessage(2, ['AlignToCenter']))

    # @qtc.pyqtSlot()
    # def q_fault_reset(self, things):
    #     pass

"""End QPTMessageQueue"""


class QPTMasterSignals(qtc.QObject):
    """Defines the signals available from the QPTWorker object."""
    response = qtc.pyqtSignal(str)
    error = qtc.pyqtSignal(tuple)
    timeout = qtc.pyqtSignal(str)
    connected = qtc.pyqtSignal()
    disconnected = qtc.pyqtSignal()
    currentPan = qtc.pyqtSignal(str)
    currentTilt = qtc.pyqtSignal(str)
    fPan = qtc.pyqtSignal(float)
    fTilt = qtc.pyqtSignal(float)


class QPTMaster(qtc.QThread):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.m_portName = None
        self.m_baudRate = None
        self.m_mutex = qtc.QMutex()
        self.m_quit = False
        self.m_connected = False
        self.Q = QPTMessageQueue()
        self.signals = QPTMasterSignals()


    def run(self):
        # Get port name and baud rate from member variables
        self.m_mutex.lock()
        currentPortName = self.m_portName
        currentBaudRate = int(self.m_baudRate)
        self.m_mutex.unlock()

        # attempt to initialize connection with the postioner, if there is an
        # error, catch the exception and emit the error back to the gui and
        # then exit the thread, else, emit connected signal
        try:
            qpt = Positioner(currentPortName, currentBaudRate)
            self.msleep(500)
            if qpt.comms.connected is not True:
                self.Q.qpt_connected = False
                self.m_connected = False
                # print('Positioner failed to connect')
                return None
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            # print('Positioner failed to connect')
            self.signals.error.emit((exctype, value, traceback.format_exc()))
            return None
        else:
            self.signals.connected.emit()
            self.m_connected = True
            self.Q.qpt_connected = True
            # print('Positioner connected')

        # main communications loop with the positioner
        # sends a msg with the positioner ever 120ms, some slight variation
        # in the period for transmission is acceptable, so msleep is used
        # to yield thread until next transmission
        while not self.m_quit:
            # Check if message queue has any items in it, if not, catch the
            # Empty exception and send a query to get the current status of
            # the positioner
            try:
                msg = self.Q.q.get_nowait()
            except Empty as e:
                msg = ['GetStatus']
            else:
                msg = msg.item

            # Decode the message to send to the positioner then trigger
            # the packet transmission
            if msg[0] == 'Stop':
                qpt.move_to(0,0,'stop')
                self.Q.clear_Q()
            
            elif msg[0] == 'GetStatus':
                qpt.get_status()
            
            elif msg[0] == 'JogCW':
                if msg[1] == 'sw':
                    qpt.jog_cw(30, Coordinate(180,0))
                    if self.parent.settings.right_toolButton_4.isDown() is not True:
                        self.Q.clear_Q()
                else:
                    # print(msg[1],msg[2])
                    qpt.jog_cw(msg[2], msg[3])

            elif msg[0] == 'JogCCW':
                if msg[1] == 'sw':
                    qpt.jog_ccw(30, Coordinate(-180,0))
                    if self.parent.settings.left_toolButton_4.isDown() is not True:
                        self.Q.clear_Q()
                else:
                    qpt.jog_ccw(msg[2], msg[3])

            elif msg[0] == 'JogUp':
                if msg[1] == 'sw':
                    qpt.jog_up(30, Coordinate(0, 90))
                    if self.parent.settings.up_toolButton_4.isDown() is not True:
                        self.Q.clear_Q()                    
                else:
                    qpt.jog_up(msg[2], msg[3])

            elif msg[0] == 'JogDown':
                if msg[1] == 'sw':
                    qpt.jog_down(30, Coordinate(0, -90))
                    if self.parent.settings.down_toolButton_4.isDown() is not True:
                        self.Q.clear_Q()                    
                else:
                    qpt.jog_down(msg[2], msg[3])

            elif msg[0] == 'MoveTo':
                qpt.move_to(msg[1], msg[2], msg[3])

            elif msg[0] == 'ZeroOffsets':
                qpt.clear_offsets()

            elif msg[0] == 'AlignToCenter':
                qpt.align_to_center()

            self.signals.currentPan.emit('{:0.2f}'.format(qpt.curr_position.pan_angle()))
            self.signals.fPan.emit(qpt.curr_position.pan_angle())
            self.signals.currentTilt.emit('{:0.2f}'.format(qpt.curr_position.tilt_angle()))
            self.signals.fTilt.emit(qpt.curr_position.tilt_angle())
            self.msleep(120)
            # end comms loop, breaks if self.m_quit is True

        qpt.move_to(0,0,'stop')
        del qpt
        self.m_connected = False
        self.Q.qpt_connected = False


    def init_connection(self, portName, baudRate):
        locker = qtc.QMutexLocker(self.m_mutex)
        self.m_portName = portName
        self.m_baudRate = baudRate
        if not self.isRunning():
            self.start()
        else:
            print('QPTMaster is already connected and running')


    def disconnect(self):
        locker = qtc.QMutexLocker(self.m_mutex)
        self.m_quit = True
        while self.isRunning():
            self.msleep(120)


