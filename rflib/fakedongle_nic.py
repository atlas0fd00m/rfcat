import rflib

import usb
import time
import queue
import logging
import unittest
import threading
import traceback

from rflib.const import *
from rflib.bits import ord23

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
        #if type(data) == str:
        #    raise(Exception("Cannot write 'str' to fakeMemory!  Must use 'bytes'"))

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
        logger.info('mmio_RFST(0x%x, %r)', tgt, dbyte)
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
        logger.info('mmio_MARCSTATE(0x%x, %r) rfst=%r', tgt, dbyte, rfst)
        return MARC_STATE_RX

class fakeDon:
    pass



MAX_CHANNELS            =   880
MAX_TX_MSGS             =   2
MAX_TX_MSGLEN           =   240   # must match RF_MAX_TX_CHUNK in rflib/chipcon_nic.py
                                  # and be divisible by 16 for crypto operations
DEFAULT_NUM_CHANS       = 83
DEFAULT_NUM_CHANHOPS    = 83

class MAC_Data:
    def __init__(self):
        self.mac_state = FHSS_STATE_NONHOPPING
        self.MAC_threshold = 6              # when the T2 clock as overflowed this many times, change channel
        self.MAC_timer = 0                  # this tracks how many times it's overflowed (really?  32-bits for these two?!?)
        self.NumChannels = DEFAULT_NUM_CHANS                # in case of multiple paths through the available channels 
        self.NumChannelHops = DEFAULT_NUM_CHANHOPS             # total number of channels in pattern (>= g_MaxChannels)
        self.curChanIdx = 0                 # indicates current channel index of the hopping pattern
        self.tLastStateChange = 0
        self.tLastHop = 0
        self.desperatelySeeking = 0         # this should be unnecessary, and should instead use mac_state?
        self.txMsgIdx = 0
        self.txMsgIdxDone = 0
        self.synched_chans = 0

    def serialize(self):
        return struct.pack("<B8H2BH", 
               self.mac_state,
               self.MAC_threshold,
               self.MAC_timer,
               self.NumChannels,
               self.NumChannelHops,
               self.curChanIdx,
               self.tLastStateChange,
               self.tLastHop,
               self.desperatelySeeking,
               self.txMsgIdx,
               self.txMsgIdxDone,
               self.synched_chans)

    def deserialize(self, data):
       (self.mac_state,
               self.MAC_threshold,
               self.MAC_timer,
               self.NumChannels,
               self.NumChannelHops,
               self.curChanIdx,
               self.tLastStateChange,
               self.tLastHop,
               self.desperatelySeeking,
               self.txMsgIdx,
               self.txMsgIdxDone,
               self.synched_chans) = struct.unpack("<B8H2BH", data)


class fakeDongle:
    '''
    This class emulates a real RfCat dongle (the physical device), as well as LibUSB.
    '''
    def __init__(self):
        self._recvbuf = b''
        self.bulk5 = queue.Queue()
        self.bulk0 = [0 for x in range(EP0BUFSIZE)]
        self.memory = fakeMemory()

        self.start_ts = time.time()
        self.aesMode = 0
        self.ampMode = 0
        self.macdata = MAC_Data()
        self.NIC_ID = 0
        self.g_txMsgQueue = ['\0'*(MAX_TX_MSGLEN+1) for x in range(MAX_TX_MSGS)]
        self.g_Channels = b''

        self.memory.writeMemory(0xdf00, FAKE_MEM_DF00)
        self.memory.writeMemory(0xdf46, b'\xf0\x0d')
        for intreg, intval in FAKE_INTERRUPT_REGISTERS.items():
            logger.info('setting interrupt register: %r = %r', intreg, intval)
            self.memory.writeMemory(eval(intreg), intval)

    def clock(self):
        return time.time() - self.start_ts

    def controlMsg(self, flags, request, buf, value, index, timeout):
        logger.info("controlMsg: 0x%x %r %r 0x%x %r %r", flags, request, buf, value, index, timeout)
        try:
            # split by direction (IN/OUT)
            if flags & USB_BM_REQTYPE_DIR_IN:
                logger.info("<= fakeDoer.controlMsg(flags=0x%x, request=%r, buf=%r, value=%r, index=%x, timeout=%r)", flags, request, buf, value, index, timeout)
                if request == EP0_CMD_GET_DEBUG_CODES:
                    return b'AB'
                if request == EP0_CMD_PEEKX:
                    return self.memory.readMemory(value, buf)

            else:  # flags & USB_BM_REQTYPE_DIR_OUT fails since USB_BM_REQTYPE_DIR_OUT == 0!
                logger.info("=> fakeDoer.controlMsg(flags=0x%x, request=%r, buf=%r, value=%r, index=%x, timeout=%r)", flags, request, buf, value, index, timeout)
                if request == EP0_CMD_POKEX:
                    self.memory.writeMemory(value, buf)

        except:
            logger.error(traceback.format_exc())

    def txdata(self, app, cmd, data):
        if type(data) == int and data < 0x100:
            data = b'%c' % data
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

            # handle commands for the SYSTEM app
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

            # handle commands for the NIC app
            elif app == APP_NIC:
                if cmd == NIC_GET_AES_MODE:
                    self.txdata(app, cmd, b'%c' % self.aesMode)

                elif cmd == NIC_SET_AES_MODE:
                    self.aesMode = ord23(data[0])
                    self.txdata(app, cmd, b'%c' % self.aesMode)

                elif cmd == NIC_SET_AMP_MODE:
                    self.ampMode = ord23(data[0])
                    self.txdata(app, cmd, b'%c' % self.ampMode)

                elif cmd == NIC_GET_AMP_MODE:
                    self.txdata(app, cmd, b'%c' % self.ampMode)

                elif cmd == NIC_SET_AES_IV:
                    self.setAES(data, ENCCS_CMD_LDIV, (self.aesMode & AES_CRYPTO_MODE))
                    self.txdata(app, cmd, data[:16])

                elif cmd == NIC_SET_AES_KEY:
                    self.setAES(data, ENCCS_CMD_LDKEY, (self.aesMode & AES_CRYPTO_MODE))
                    self.txdata(app, cmd, data[:16])

                elif cmd == NIC_SET_ID:
                    # fixme: sending 8 bit to 16 bit function???
                    self.NIC_ID = ord23(data[0])
                    self.txdata(app, cmd, data[0])

                elif cmd == NIC_LONG_XMIT:
                    # load up macdata queues, follow-on with 
                    #
                    #
                    # this is duplicating our work in transmit_long().  pick one.
                    if (macdata.mac_state != FHSS_STATE_NONHOPPING):
                        data[0] = RC_RF_MODE_INCOMPAT
                        self.txdata(app, cmd, data[0])
                   
                    else:
                        length, blocks = struct.unpack("<HB", data[:2])
                        txTotal= 0
                        data[0] = transmit_long(data[3:], length, blocks)
                        self.txdata(app, cmd, data[0])

                elif cmd == NIC_LONG_XMIT_MORE:
                    length = ord23(data[0])
                    if (length == 0):
                        if(rfTxTotalTXLen):
                            self.debug("dropout final wait!")
                            #debughex16(rfTxTotalTXLen)
                            #debughex(g_txMsgQueue[0][0])
                            #debughex(g_txMsgQueue[1][0])
                            self.lastCode[1] = LCE_DROPPED_PACKET
                            data[0] = RC_TX_DROPPED_PACKET
                            #LED = 0
                            #resetRFSTATE()
                            self.macdata.mac_state = FHSS_STATE_NONHOPPING
                            self.txdata(app, cmd, b'%c' % RC_TX_DROPPED_PACKET)
                            return
                        
                        #LED = 0
                        self.macdata.mac_state = FHSS_STATE_NONHOPPING
                        self.debug("total bytes tx:")
                        #debughex16(txTotal)
                        self.txdata(app, cmd, b'%c' % LCE_NO_ERROR)
                        return
                    
                    # catch if we've been called out of sequence, or we've had an underrun
                    if (self.macdata.mac_state != FHSS_STATE_LONG_XMIT):
                        self.debug("underrun")
                        # TX underrun
                        if(self.lastCode[1] == LCE_DROPPED_PACKET):
                            self.txdata(app, cmd, b'%c' % RC_TX_DROPPED_PACKET)
                            
                        else:
                            self.lastCode[1] = LCE_RF_MULTI_BUFFER_NOT_INIT
                            self.txdata(app, cmd, b'%c' % RC_RF_MODE_INCOMPAT)
                        
                        #LED = 0
                        #resetRFSTATE()
                        self.macdata.mac_state = FHSS_STATE_NONHOPPING
                    else:
                        # add data to rolling datafer
                        #data[0] = MAC_tx(&data[1], (__xdata u8) len)
                        # check for any other error return
                        #if(data[0] && data[0] != RC_ERR_BUFFER_NOT_AVAILABLE)
                        #{
                        #    debug("datafer error");
                        #    debughex(data[0]);
                        #    LED = 0;
                        #    resetRFSTATE();
                        #    self.macdata.mac_state = FHSS_STATE_NONHOPPING;
                        #}
                        self.txdata(app, cmd, data[0]);

                elif cmd == FHSS_XMIT:
                    length = ord23(data[0])
                    #len += (*data++) << 8;
                    #repeat = *data++;
                    #repeat += (*data++) << 8;
                    #offset = *data++;
                    #offset += (*data++) << 8;
                    #transmit(data, len, repeat, offset);
                    #MAC_tx(data, len);
                    ##/// for some strange reason, if we call this in MAC_tx it dies, but not from here. ugh.
                    if (length > MAX_TX_MSGLEN):
                        self.debug("FHSSxmit message too long");
                        self.txdata(app, cmd, b'%c' % length);
                        return buflen

                    elif (self.g_txMsgQueue[self.macdata.txMsgIdx][0] != 0):
                        self.debug("still waiting on the last packet");
                        self.txdata(app, cmd, b'%c' % length);
                        return buflen

                    g_txMsgQueue[self.macdata.txMsgIdx][0] = length
                    g_txMsgQueue[self.macdata.txMsgIdx][1] = data[1:]

                    self.macdata.txMsgIdx += 1
                    if (self.macdata.txMsgIdx >= MAX_TX_MSGS):
                        self.macdata.txMsgIdx = 0;

                    self.txdata(app, cmd,  b'%c' % length)
                    
                elif cmd == FHSS_SET_CHANNELS:
                    self.macdata.NumChannels = ord23(data[0])
                    if (self.macdata.NumChannels <= MAX_CHANNELS):
                        self.g_Channels = data[2:self.macdata.NumChannels]
                        self.txdata(app, cmd, struct.pack("<H", self.macdata.NumChannels))

                    else:
                        self.txdata(app, cmd, b"NO DEAL")

                elif cmd == FHSS_GET_CHANNELS:
                    self.txdata(app, cmd, self.g_Channels)

                elif cmd == FHSS_NEXT_CHANNEL:
                    #MAC_set_chanidx(MAC_getNextChannel());
                    self.macdata.curChanIdx += 1

                    chan = self.setFHSSchanByIdx(self.macdata.curChanIdx)
                    self.txdata(app, cmd, b'%c' % chan) 

                elif cmd == FHSS_CHANGE_CHANNEL:
                    #PHY_set_channel(data[0]);
                    self.memory.writeMemory(CHANNR, data[0])
                    self.txdata(app, cmd, data[0]);

                elif cmd == FHSS_START_HOPPING:
                    self.begin_hopping(0);
                    self.txdata(app, cmd, data[0]);

                elif cmd == FHSS_STOP_HOPPING:
                    self.stop_hopping();
                    self.txdata(app, cmd, data[0]);

                elif cmd == FHSS_SET_MAC_THRESHOLD:
                    self.macdata.MAC_threshold = ord23(data[0])
                    self.txdata(app, cmd, data[0]);

                elif cmd == FHSS_GET_MAC_THRESHOLD:
                    self.txdata(app, cmd, struct.pack("<I", self.macdata.MAC_threshold))

                elif cmd == FHSS_SET_MAC_DATA:
                    self.debugx(data);
                    #debughex(data[0]);
                    self.macdata.deserialize(data)
                    self.txdata(app, cmd, data);

                elif cmd == FHSS_GET_MAC_DATA:
                    self.macdata.MAC_timer = self.get_rf_MAC_timer()
                    self.txdata(app, cmd, self.macdata.serialize());

                elif cmd == FHSS_START_SYNC:
                    #MAC_sync(data[0])
                    self.txdata(app, cmd, data[0]);
                    
                elif cmd == FHSS_SET_STATE:
                    # store the main timer value for beginning of this phase.
                    self.macdata.tLastStateChange = self.clock()
                    self.macdata.mac_state = ord23(data[0])
                    
                    # if macdata.mac_state is > 2, make sure the T2 interrupt is set
                    # if macdata.mac_state <= 2, make sure T2 interrupt is ignored
                    if self.macdata.mac_state in (FHSS_STATE_NONHOPPING, FHSS_STATE_DISCOVERY, FHSS_STATE_SYNCHING):
                        self.stop_hopping();

                    elif self.macdata.mac_state == FHSS_STATE_SYNCINGMASTER:
                        self.MAC_do_Master_scanny_thingy();

                    elif self.macdata.mac_state in (FHSS_STATE_SYNCHED, FHSS_STATE_SYNC_MASTER):
                        self.begin_hopping(0);
                    
                    self.txdata(app, cmd, data[0]);
                    
                elif cmd == FHSS_GET_STATE:
                    self.txdata(app, cmd, self.macdata.mac_state)
                    
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
        '''
        In standard USB fashion, bulkRead() handles the "IN" communication, whereby the "host" 
        pulls information back from the "device".  ie. our responses to commands.

        RfCat polls this function repeatedly, to provide the illusion of bi-directional
        communication, when in fact USB (pre-v3) is completely host-driven.  If a USB device
        gets to talk, it's because the host asked for information.

        For our purposes, bulkRead() simply pops data out of the EP5 Bulk "queue" and returns.

        This has *nothing* to do with "reading" from the memory.  bulkRead() gives the dongle
        the "talking stick"
        '''
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
        self.txdata(APP_DEBUG, DEBUG_CMD_STRING, msg)

    # no need to reinvent the wheel, this is a difference in CC1111 memories, not functionality
    debug  = log
    debugx = log

    def setAES(self, data, cmd, flags):
        '''
        For now, we do nothing.
        '''
        return

    def setFHSSchanByIdx(self, chanidx):
        chan = self.g_Channels[chanidx]
        self.memory.writeMemory(CHANNR, chan)
        return chan

    def begin_hopping(self, startchan):
        self.memory.writeMemory(CHANNR, b'%c' % startchan)
        return
    def stop_hopping(self):
        return

    def get_rf_MAC_timer(self):
        return int((self.clock() * 20) % self.macdata.MAC_threshold)

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

