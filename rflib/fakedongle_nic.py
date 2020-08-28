import rflib

import usb
import time
import queue
import logging
import unittest
import threading
import traceback

from rflib.const import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger(__name__)

EP0BUFSIZE = 512


class fakeMemory:
    def __init__(self, size=64*1024):
        self.memory = [0 for x in range(size)]
        self.mmio = {}
        #self.mmio[X_RFST] = self.mmio_RFST
        #self.mmio[X_RFST] = self.mmio_MARCSTATE

    def readMemory(self, addr, size):
        logger.debug("fm.readMemory(0x%x, 0x%x)", addr, size)
        chunk = b''.join([b'%c' % x for x in self.memory[addr:addr+size]])
        if len(chunk) < size:
            chunk += b"@" * (size-len(chunk))
        return chunk

    def writeMemory(self, addr, data):
        logger.debug("fm.writeMemory(0x%x, %r)", addr, data)
        if type(data) == str:
            raise(Exception("Cannot write 'str' to fakeMemory!  Must use 'bytes'"))

        for x in range(len(data)):
            tgt = addr+x
            val = data[x]

            handler = self.mmio.get(tgt)
            if handler is not None:
                val = handler(tgt, data[x])

            # if we didn't return None from the handler, write it anyway
            if val is not None:
                self.memory[tgt] = val

    def mmio_RFST(self, tgt, dbyte):
        logger.warning('mmio_RFST(0x%x, %r)', tgt, dbyte)
        print("RFST==%x  (%x)" % (self.readMemory(X_RFST, 1), ord(dbyte)))


        # configure MARCSTATE
        val = ord(dbyte)
        if val in (2, 3):
            val = dbyte+10

        else:
            val = MARC_STATE_RX

        self.writeMemory(MARCSTATE, b'%c'%(val))

        # still set RFST
        return dbyte

    def mmio_MARCSTATE(self, tgt, dbyte):
        rfst = self.readMemory(X_RFST, 1)
        logger.warning('mmio_MARCSTATE(0x%x, %r) rfst=%r', tgt, dbyte, rfst)
        return MARC_STATE_RX

class fakeDon:
    pass


class fakeDongle:
    def __init__(self):
        self._recvbuf = b''
        self.bulk5 = queue.Queue()
        self.bulk0 = [0 for x in range(EP0BUFSIZE)]
        self.memory = fakeMemory()

        self.memory.writeMemory(0xdf00, FAKE_MEM_DF00)
        self.memory.writeMemory(0xdf46, b'\xf0\x0d')
        for intreg, intval in FAKE_INTERRUPT_REGISTERS.items():
            logger.warning('setting interrupt register: %r = %r', intreg, intval)
            self.memory.writeMemory(eval(intreg), intval)

    def controlMsg(self, flags, request, buf, value, index, timeout):
        logger.info("controlMsg: 0x%x %r %r 0x%x %r %r", flags, request, buf, value, index, timeout)
        try:
            # split by direction (IN/OUT)
            if flags & USB_BM_REQTYPE_DIR_IN:
                logger.warning("<= fakeDoer.controlMsg(flags=0x%x, request=%r, buf=%r, value=%r, index=%x, timeout=%r)", flags, request, buf, value, index, timeout)
                if request == EP0_CMD_GET_DEBUG_CODES:
                    return b'AB'
                if request == EP0_CMD_PEEKX:
                    return self.memory.readMemory(value, buf)

            else:  # flags & USB_BM_REQTYPE_DIR_OUT fails since USB_BM_REQTYPE_DIR_OUT == 0!
                logger.warning("=> fakeDoer.controlMsg(flags=0x%x, request=%r, buf=%r, value=%r, index=%x, timeout=%r)", flags, request, buf, value, index, timeout)
                if request == EP0_CMD_POKEX:
                    self.memory.writeMemory(value, buf)

        except:
            logger.error(traceback.format_exc())

    def txdata(self, app, cmd, data):
        self.bulk5.put(struct.pack('<BBH', app, cmd, len(data)) + data)

    def bulkWrite(self, chan, buf, timeout=1):
        try:
            # handle write "parts"
            buflen = len(buf)   # need to return this, because that's what the libusb interface does.
            self._recvbuf += buf
            logger.debug("=> fakeDoer.bulkWrite(5, %r)", buf)

            curbuflen = len(self._recvbuf)
            if curbuflen < 4:
                return buflen

            app, cmd, mlen = struct.unpack("<BBH", self._recvbuf[:4])

            if curbuflen < mlen+2:
                logger.info("bulkWrite: returning because buffer isn't big enough: len: %x  need: %x", curbuflen, mlen+2)
                return buflen

            # now handle a packet
            pkt = self._recvbuf[:mlen+4]

            data = pkt[4:]
            #print("_recvbuf:%r\t\tpkt:%r\t\tapp:%x\tcmd:%x\tdata:%r\t\tmlen:%r\t" % (self._recvbuf, pkt, app, cmd, data, hex(mlen)))
            self._recvbuf = self._recvbuf[mlen+4:]

            if app == APP_SYSTEM:
                if cmd == SYS_CMD_PEEK:
                    size, addr = struct.unpack("<HH", data[:4])
                    retmsg = self.memory.readMemory(addr, size)
                    self.txdata(app, cmd, retmsg) 

                elif cmd == SYS_CMD_POKE:
                    addr, = struct.unpack("<H", data[:2])
                    size = mlen - 2
                    chunk = data[2:2+size]
                    logger.info("=>> POKE: pkt:%r\t\tdata:%r\t\tsize:%r\t\taddr:%r\t\t%r", repr(pkt), repr(data), hex(size), hex(addr), chunk)
                    self.memory.writeMemory(addr, chunk)

                    self.bulk5.put(pkt)

                elif cmd == SYS_CMD_PING:
                    self.bulk5.put(pkt)

                elif cmd == SYS_CMD_BUILDTYPE:
                    self.txdata(app, cmd, FAKE_DONGLE_BUILDDATA)

                elif cmd == SYS_CMD_COMPILER:
                    self.txdata(app, cmd, FAKE_DONGLE_COMPILER)

                elif cmd == SYS_CMD_DEVICE_SERIAL_NUMBER:
                    self.txdata(app, cmd, FAKE_DONGLE_SERIALNUM)

                elif cmd == SYS_CMD_RFMODE:
                    if len(data) > 1:
                        logger.warning("ummm. what's this extra data in your SYS_CMD_RFMODE command?")
                    if len(data) == 0:
                        logger.warning("SYS_CMD_RFMODE: need a byte to put in X_RFST!")
                    else:
                        self.memory.writeMemory(X_RFST, data[0:1])
                    self.txdata(app, cmd, data)

                else:
                    self.log(b'WTFO!  no APP_SYSTEM::0x%x', cmd)
                    self.bulk5.put(pkt)

            elif app == APP_NIC:
                if cmd == NIC_GET_AES_MODE:
                    retmsg = struct.pack("<BBH", app, cmd, 1) 
                    retmsg += b'\0'
                    self.bulk5.put(retmsg)
                    self.txdata(app, cmd, b'\0')

                else:
                    self.log(b'WTFO!  no APP_NIC::0x%x', cmd)
                    self.bulk5.put(pkt)
            else:
                # everything else...  just echo
                self.bulk5.put(pkt)

            return buflen

        except:
            logger.error(traceback.format_exc())

    def bulkRead(self, chan, length, timeout=1):
        starttime = time.time()

        while time.time() - starttime < timeout:
            try:
                out = self.bulk5.get_nowait()
                logger.debug('<= fakeDoer.bulkRead(5, %r) == %r', length, out)
                return b"@" + out
            except queue.Empty:
                time.sleep(.05)

            logger.debug('<= fakeDoer.bulkRead(5, %r) == <EmptyQueue>', length)
            raise usb.USBError('Operation timed out (FakeDongle)')

    def log(self, msg, *args):
        if len(args):
            msg = msg % args
        self.bulk5.put(struct.pack('<BBH', APP_DEBUG, DEBUG_CMD_STRING, len(msg)) + msg)
            
class FakeRfCat(rflib.RfCat):
    def __init__(self, idx=0, debug=False, copyDongle=None, RfMode=RFST_SRX):
        # instantiate ourself as an official RfCat dongle
        rflib.RfCat.__init__(self, idx, debug, copyDongle, RfMode)

    def _internal_select_dongle(self, console=False):
        self._d = fakeDon()
        self._do = fakeDongle()
        self.console = console

    def getPartNum(self):
        return FAKE_PARTNUM

