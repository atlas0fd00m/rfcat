import rflib

import usb
import time
import queue
import logging
import unittest
import threading

from rflib.const import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger(__name__)

EP0BUFSIZE = 512


class fakeMemory:
    def __init__(self, size=64*1024):
        self.memory = [0 for x in range(size)]

    def readMemory(self, addr, size):
        return ''.join([chr(x) for x in self.memory[addr:addr+size]])

    def writeMemory(self, addr, data):
        self.memory = self.memory[:addr] + data + self.memory[addr+len(data):]


class fakeDon:
    pass


class fakeDongle:
    def __init__(self):
        self._initrcvd = False
        self.bulk5 = queue.Queue()
        self.bulk0 = [0 for x in range(EP0BUFSIZE)]
        self.memory = fakeMemory()

    def controlMsg(self, flags, request, buf, value, index, timeout):
        if flags & USB_BM_REQTYPE_DIR_OUT:
            logger.warn("=> fakeDoer.controlMsg(flags=0x%x, request=%r, buf=%r, value=%r, index=%x, timeout=%r)", flags, request, buf, value, index, timeout)
        elif flags & USB_BM_REQTYPE_DIR_IN:
            logger.warn("<= fakeDoer.controlMsg(flags=0x%x, request=%r, buf=%r, value=%r, index=%x, timeout=%r)", flags, request, buf, value, index, timeout)

    def bulkWrite(self, chan, buf, timeout=1):
        self._initrcvd = buf
        logger.debug("=> fakeDoer.bulkWrite(5, %r)", buf)

        app, cmd, mlen = struct.unpack("<BBH", buf[:4])
        data = buf[4:]

        if app == APP_SYSTEM:
            if cmd == SYS_CMD_PEEK:
                size, addr = struct.unpack("<HH", data[:4])
                retmsg = struct.pack("<BBH", app, cmd, size) 
                retmsg += 'A' * size
                self.bulk5.put(retmsg)

            elif cmd == SYS_CMD_POKE:
                size, addr = struct.unpack("<HH", data[:4])
                retmsg = struct.pack("<BBH", app, cmd, size) 
                retmsg += 'A' * size
                self.bulk5.put(retmsg)

            elif cmd == SYS_CMD_PING:
                self.bulk5.put(buf)

            elif cmd == SYS_CMD_RFMODE:
                self.bulk5.put(buf)

            else:
                self.log('WTFO!  no APP_SYSTEM::0x%x', cmd)
                self.bulk5.put(buf)

        elif app == APP_NIC:
            if cmd == NIC_GET_AES_MODE:
                retmsg = struct.pack("<BBH", app, cmd, 1) 
                retmsg += '\0'
                self.bulk5.put(retmsg)

            else:
                self.log('WTFO!  no APP_NIC::0x%x', cmd)
                self.bulk5.put(buf)
        else:
            # everything else...  just echo
            self.bulk5.put(buf)

        return len(buf)

    def bulkRead(self, chan, length, timeout=1):
        starttime = time.time()

        while time.time() - starttime < timeout:
            try:
                out = self.bulk5.get_nowait()
                logger.debug('<= fakeDoer.bulkRead(5, %r) == %r', length, out)
                return "@" + out
            except queue.Empty:
                time.sleep(.05)

            logger.debug('<= fakeDoer.bulkRead(5, %r) == <EmptyQueue>', length)
            raise usb.USBError('Operation timed out (FakeDongle)')

    def log(self, msg, *args):
        if len(args):
            msg = msg % args
        self.bulk5.put(struct.pack('<BBH', APP_DEBUG, DEBUG_CMD_STRING, len(msg)) + msg)
            
class FakeRfCat(rflib.RfCat):
    def __init__(self, idx=0, debug=True, copyDongle=None, RfMode=RFST_SRX):
        # instantiate ourself as an official RfCat dongle
        rflib.RfCat.__init__(self, idx, debug, copyDongle, RfMode)

    def _internal_select_dongle(self, console=False):
        logger.warn("FakeDongle._internal_select_dongle()")
        self._d = fakeDon()
        self._do = fakeDongle()
        self.console = console

    def getPartNum(self):
        return FAKE_PARTNUM

