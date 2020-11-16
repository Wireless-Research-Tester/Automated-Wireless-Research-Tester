################################################################################
# integer
# Description: 
#   This file contains the implementation of two classes that
#   support data types useful for interacting with the QPT Positioner.
#   First, the Integer class, for representing Ints in the format required
#   by the QPT. Second, the Coordinate class, which is essentially an
#   ordered pair for representing a specific combination of azimuth and 
#   elevation angles of the positioner in degrees.
#
# Status:
#   Mostly finished, I do not foresee any major changes being necessary,
#   except for possibly having to adjust the min and max values in the 
#   Coordinate class. I think, however, that if this is going to cause an
#   issue, it won't be until down the road when examining how to improve
#   the configuration api for the QPT Postioner.
#
# Author: Thomas Hoover
# Date: 20200417
# Built with Python Version: 3.8.2
# For any questions, contact Thomas at tomhoover1@gmail.com
################################################################################
class Integer:
    """Integer: a class to represent a integer value that adheres to the
    PTHR-90 Embedded Controller Protocol Rev J (located in qpt/docs).

    Protocol Format Requirements:
        -> 16-bit, signed two's-complement little endian integers.
        -> Simple split between the two integer bytes.
        -> First byte should represent the LSB of the integer, the second
           byte the MSB of the integer.
        -> Max integer value of 32767.
        -> Min integer value of -32768.

    Examples:
        Integer Value    Integer in Hex    First Byte    Second Byte
        *************    **************    **********    ***********
            32767            0x7fff           0xff           0x7f
              2              0x0002           0x02           0x00
              1              0x0001           0x01           0x00
              0              0x0000           0x00           0x00
             -1              0xffff           0xff           0xff
             -2              0xfffe           0xfe           0xff
           -32768            0x8000           0x00           0x80

    NOTE:
        The QPT's microcontroller performs no range or format checking
        of inputs. The upper and lower bounds of the integer range are 
        enforced by the class via the constructor, however, the correct
        formatting of the value must be used when passed to the QPT
        (ie. integer.to_bytes()).  Additionally, each command in the protocol's
        instruction set that requires an Int data member in the tx packet may
        further limit the allowable range of the Int, any client of this 
        class that uses this class to generate packet data to transmit to the
        QPT is responsible for ensuring the range is appropriate for the
        given command.
    """
    _MAX_INT = 32767
    _MIN_INT = -32768

    def __init__(self, val):
        if isinstance(val, int) and val <= self._MAX_INT and val >= self._MIN_INT:
            self._value = int(val).to_bytes(2, byteorder='little', signed=True)
            self._valid = True
        else:
            self._value = None
            self._valid = False

    def is_valid(self):
        return self._valid

    def lower_byte(self):
        if self._valid:
            return self._value[0].to_bytes(1, byteorder='little')
        return None

    def upper_byte(self):
        if self._valid:
            return self._value[1].to_bytes(1, byteorder='little')
        return None

    def to_int(self):
        if self._valid:
            return int.from_bytes(self._value, byteorder='little', signed=True)
        return None

    def to_bytes(self):
        if self._valid:
            return self._value
        return None

    def to_hex(self):
        if self._valid:
            return self._value.hex('-')
        return None
"""End Integer Class"""


class Coordinate:
    """Coordinate: implements an ordered pair value representing a 
    QPT position (pan, tilt), where pan is the QPT's azimuth angle and tilt 
    is the QPT's elevation angle, both in degrees. 
    """
    offsets = {
        'pan'  : 0.0,
        'tilt' : 0.0,
    }

    limits = {
        'MIN_AZ'  : -180.00,
        'MAX_AZ'  :  180.00,
        'MIN_EL'  :  -90.00,
        'MAX_EL'  :   90.00,
        'MIN_INT' :  -18000,
        'MAX_INT' :   18000,
    }


    def __init__(self, pan, tilt, fromqpt=False):
        if fromqpt is True: 
            self._phi   = pan
            self._theta = tilt
            self._valid = True
        elif    (isinstance(pan,  int) or isinstance(pan , float)) \
            and (isinstance(tilt, int) or isinstance(tilt, float)) \
            and pan  <= self.limits['MAX_AZ'] and pan  >= self.limits['MIN_AZ'] \
            and tilt <= self.limits['MAX_EL'] and tilt >= self.limits['MIN_EL']:
                self._phi   = int(pan*100 ).to_bytes(2, byteorder='little', signed='True')
                self._theta = int(tilt*100).to_bytes(2, byteorder='little', signed='True')
                self._valid = True
        else:
            self._phi   = None
            self._theta = None
            self._valid = False     

    def is_valid(self):
        return self._valid

    def update_limits(self, pan_offset, tilt_offset):
        if pan_offset == 0.0:
            self.limits['MAX_AZ']  =  180.00
            self.limits['MIN_AZ']  = -180.00
            self.limits['MAX_INT'] =  18000
            self.limits['MIN_INT'] = -18000
        else:
            self.limits['MAX_AZ']  = self.limits['MAX_AZ'] + pan_offset
            self.limits['MIN_AZ']  = self.limits['MIN_AZ'] + pan_offset
            self.limits['MAX_INT'] = self.limits['MAX_INT'] + pan_offset*100
            self.limits['MIN_INT'] = self.limits['MIN_INT'] + pan_offset*100
        if tilt_offset == 0.0:
            self.limits['MAX_EL'] =  90.00
            self.limits['MIN_EL'] = -90.00
        else:
            self.limits['MAX_EL'] = self.limits['MAX_EL'] + tilt_offset
            self.limits['MIN_EL'] = self.limits['MIN_EL'] + tilt_offset

        self.offsets['pan']  = pan_offset
        self.offsets['tilt'] = tilt_offset

    def print_limits(self):
        print('Azimuth limits:  ',  self.limits['MIN_AZ'], ' to ',  self.limits['MAX_AZ'])
        print('Elevation limits: ', self.limits['MIN_EL'], ' to  ', self.limits['MAX_EL'])
        print('Integer limits:  ',  self.limits['MIN_INT'], ' to ', self.limits['MAX_INT'])
        print('Offsets: Pan =',     self.offsets['pan'], ' Tilt =', self.offsets['tilt'])

    def pan_angle(self):
        if self._valid:
            return (int.from_bytes(self._phi, byteorder='little', signed=True) / 100) + self.offsets['pan']
        return None

    def tilt_angle(self):
        if self._valid:
            return (int.from_bytes(self._theta, byteorder='little', signed=True) / 100) + self.offsets['tilt']
        return None

    def pan_bytes(self):
        if self._valid:
            return self._phi
        return None

    def tilt_bytes(self):
        if self._valid:
            return self._theta
        return None

    def pan_hex(self):
        if self._valid:
            return self._phi.hex('-')
        return None

    def tilt_hex(self):
        if self._valid:
            return self._theta.hex('-')
        return None

    def to_bytes(self):
        if self._valid:
            return self._phi + self._theta
        return None

    def to_hex(self):
        if self._valid:
            return (self._phi + self._theta).hex('-')
        return None
"""End Coordinate Class"""

