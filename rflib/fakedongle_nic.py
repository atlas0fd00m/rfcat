import rflib

import usb
import time
import queue
import logging
import unittest
import threading
import traceback
import math
import random

from rflib.const import *
from rflib.bits import ord23

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')
logger = logging.getLogger(__name__)

EP0BUFSIZE = 512

# For Spectrum Analyzer testing with FakeDongle
def generate_fake_specan_data(num_channels=83, noise_floor=-80, signal_dbm=-50, seed=None):
    """Generate realistic fake RSSI values for spectrum analyzer testing.
    
    Args:
        num_channels: Number of frequency channels (default 83 for 2.4GHz band)
        noise_floor: Base noise floor in dBm (typical: -90 to -70, default: -80)
        signal_dbm: Peak signal strength in dBm (typical: -60 to -40, default: -50)
        seed: Optional random seed for deterministic test data
        
    Returns:
        tuple: (rssi_bytes, dbm_values) where rssi_bytes is formatted for ccspecan.py
        
    Conversion formula used by ccspecan: dbm = (((byte ^ 0x80) / 2) - 88)
    Valid dBm range: [-88, +40] due to unsigned byte constraints.
    """
    if seed is not None:
        random.seed(seed)
    
    rssi_values = []
    dbm_values = []
    
    num_signals_max = min(4, max(1, (num_channels // 20)))
    num_signals = random.randint(2, num_signals_max) if num_signals_max >= 2 else num_signals_max
    signal_range_start = 15
    signal_range_end = max(signal_range_start + 1, num_channels - 15)
    
    if signal_range_start < signal_range_end and num_signals > 0:
        signal_centers = sorted(random.sample(range(signal_range_start, signal_range_end), min(num_signals, (signal_range_end - signal_range_start))))
        bandwidths = {c: random.randint(3, 7) for c in signal_centers}
    else:
        signal_centers = []
        bandwidths = {}
    
    for i in range(num_channels):
        dbm = noise_floor + random.uniform(-3, 5)
        
        for center, bw in bandwidths.items():
            dist = abs(i - center)
            if dist <= bw:
                gaussian = math.exp(-0.5 * (dist / (bw/2)) ** 2) if dist > 0 else 1.0
                signal_val = signal_dbm + (noise_floor - signal_dbm) * (1 - gaussian)
                dbm = max(dbm, signal_val)
        
        dbm = max(-88, min(+35, dbm))
        dbm_values.append(dbm)
        
        temp = int((dbm + 88) * 2)
        byte_val = (temp & 0xFF) ^ 0x80
        rssi_values.append(byte_val)
    
    return bytes(rssi_values), dbm_values


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
        self._specan_queue = queue.Queue()  # For spectrum analyzer testing
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
        for intreg, intval in list(FAKE_INTERRUPT_REGISTERS.items()):
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

    def queue_specan_frame(self, rssi_bytes, timestamp=None):
        """Queue a specan frame for retrieval by recv(APP_SPECAN, SPECAN_QUEUE, timeout).
        
        Used for testing spectrum analyzer features without physical hardware.
        
        Args:
            rssi_bytes: RSSI data bytes (already XOR'd with 0x80 format)
            timestamp: Optional Unix timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()
        self._specan_queue.put((rssi_bytes, timestamp))

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
                    
                elif cmd == 0x40:   # RFCAT_START_SPECAN: enter specan mode
                    # no hardware action needed; the auto-generator (when FAKE_RFCAT)
                    # fills the specan queue. Just acknowledge.
                    self.txdata(app, cmd, data[:1] or b'\x00')
                elif cmd == 0x41:   # RFCAT_STOP_SPECAN: leave specan mode
                    self.txdata(app, cmd, b'\x00')
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
        
        Special handling for APP_SPECAN: if specan frames are queued, they will be returned
        in the format expected by ccspecan.py (rssi_bytes) -- the recv() pipeline prepends
        the '@' framing header.
        
        NOTE: `timeout` is in milliseconds here, matching EP_TIMEOUT_* constants (eg. 10ms).
        '''
        starttime = time.time()
        # convert millisecond timeout to seconds; clamp minimum so we don't spin hot
        timeout_s = max((timeout / 1000.0), 0.001)

        # First check for specan data if APP_SPECAN channel is requested
        # chan == 5 is the OUT pipe; 0x85 (0x80|5) is the IN pipe (what bulkRead uses)
        is_specan = (chan in (5, 0x85))
        if is_specan:
            if self._specan_queue.qsize() > 0:
                rssi_bytes, timestamp = self._specan_queue.get_nowait()
                from rflib.const import APP_SPECAN
                # deliver the frame payload (without the '@' header; runEP5_recv
                # expects bulkRead to return the packed app/cmd/len + data frame).
                self.txdata(APP_SPECAN, 1, rssi_bytes)
                try:
                    out = self.bulk5.get_nowait()
                except queue.Empty:
                    out = b''
                logger.debug('<= fakeDoer.bulkRead(5, %r) == <SPECAN_FRAME>', length)
                return b"@" + out

        # poll for either bulk5 messages or (if specan) newly-arriving specan frames
        while time.time() - starttime < timeout_s:
            try:
                out = self.bulk5.get_nowait()
                logger.debug('<= fakeDoer.bulkRead(5, %r) == %r', length, out)
                return b"@" + out
            except queue.Empty:
                if is_specan and self._specan_queue.qsize() > 0:
                    rssi_bytes, timestamp = self._specan_queue.get_nowait()
                    from rflib.const import APP_SPECAN
                    self.txdata(APP_SPECAN, 1, rssi_bytes)
                    try:
                        out = self.bulk5.get_nowait()
                    except queue.Empty:
                        out = b''
                    logger.debug('<= fakeDoer.bulkRead(5, %r) == <SPECAN_FRAME>', length)
                    return b"@" + out
                time.sleep(.005)

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

class FakeRfCat(rflib.RfCat):  # Inherits methods but initializes fake dongle in __init__
    """Fake RfCat that uses FakeDongle instead of USB hardware.
    
    All methods inherited from rflib.RfCat/FHSSNIC work normally - only init differs.
    We call super().__init__() to get the full threaded state machine (recv/send/ctrl
    threads), but override resetup() so no USB hardware probing ever happens. The
    fake dongle is created eagerly during resetup() and strapped into self._do.
    """
    def __init__(self, idx=0, debug=False, copyDongle=None, RfMode=RFST_SRX, safemode=False):
        # create the fake hardware objects up-front; parent will not clobber
        # because we override resetup() to be a no-op hardware-wise
        self._fake_d = fakeDon()
        self._fake_do = fakeDongle()
        # call the full parent init: starts recv/send/ctrl threads + all state
        super().__init__(idx=idx, debug=debug, copyDongle=copyDongle,
                         RfMode=RfMode, safemode=safemode)

    def resetup(self, console=True, copyDongle=None):
        # never probe USB hardware: strap in the fake dongle directly.
        if self._debug > 0:
            print("[FakeRfCat] resetup: strapping in FakeDongle (no USB scan)", file=sys.stderr)
        self._d = self._fake_d
        self._do = self._fake_do
        self.devnum = 0
        self.chipnum = FAKE_PARTNUM
        self.chipstr = "FakeDongle"
        self._usbmaxi = EP5IN_MAX_PACKET_SIZE
        self._usbmaxo = EP5OUT_MAX_PACKET_SIZE
        self._usbcfg = None
        self._usbintf = None
        self._usbeps = []
        self.ep5timeout = EP_TIMEOUT_ACTIVE
        # threading/locks are established by USBDongle.__init__ via setup(); ensure
        # the receive thread is gated on so data can flow.
        if self.rsema is None:
            import threading
            self.rsema = threading.Lock()
        if self.xsema is None:
            import threading
            self.xsema = threading.Lock()
        self._threadGo.set()
        if not self._safemode:
            self.ping(3, wait=10, silent=True)

    def _internal_select_dongle(self, console=False):
        """Override to do nothing - fake dongle already initialized."""
        if hasattr(self, '_debug') and self._debug:
            print("[FakeRfCat] Using pre-initialized FakeDongle")

    def getPartNum(self):
        return FAKE_PARTNUM

