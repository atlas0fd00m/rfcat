#!/usr/bin/env ipython
import sys
import usb
import code
import time
import struct
import threading
import re
#from chipcondefs import *
from cc1111client import *

APP_NIC =                       0x42
NIC_RECV =                      0x1
NIC_XMIT =                      0x2
NIC_SET_ID =                    0x3
NIC_RFMODE =                    0x4
NIC_SET_RECV_LARGE =            0x5
NIC_SET_AES_MODE =              0x6
NIC_GET_AES_MODE =              0x7
NIC_SET_AES_IV =                0x8
NIC_SET_AES_KEY =               0x9


FHSS_SET_CHANNELS =             0x10
FHSS_NEXT_CHANNEL =             0x11
FHSS_CHANGE_CHANNEL =           0x12
FHSS_SET_MAC_THRESHOLD =        0x13
FHSS_GET_MAC_THRESHOLD =        0x14
FHSS_SET_MAC_DATA =             0x15
FHSS_GET_MAC_DATA =             0x16
FHSS_XMIT =                     0x17
FHSS_GET_CHANNELS =             0x18

FHSS_SET_STATE =                0x20
FHSS_GET_STATE =                0x21
FHSS_START_SYNC =               0x22
FHSS_START_HOPPING =            0x23
FHSS_STOP_HOPPING =             0x24

FHSS_STATE_NONHOPPING =         0
FHSS_STATE_DISCOVERY =          1
FHSS_STATE_SYNCHING =           2
FHSS_LAST_NONHOPPING_STATE =    FHSS_STATE_SYNCHING

FHSS_STATE_SYNCHED =            3
FHSS_STATE_SYNC_MASTER =        4
FHSS_STATE_SYNCINGMASTER =      5
FHSS_LAST_STATE =               5       # used for testing


FHSS_STATES = {}
for key,val in globals().items():
    if key.startswith("FHSS_STATE_"):
        FHSS_STATES[key] = val
        FHSS_STATES[val] = key
                

T2SETTINGS = {}
T2SETTINGS_24MHz = {
    100: (4, 147, 3),
    150: (5, 110, 3),
    200: (5, 146, 3),
    250: (5, 183, 3),
    }
T2SETTINGS_26MHz = {
    100: (4, 158, 3),
    150: (5, 119, 3),
    200: (5, 158, 3),
    250: (5, 198, 3),
    }
    
TIP = (64,128,256,1024)

def calculateT2(ms, mhz=24):
    TICKSPD = [(mhz*1000000/pow(2,x)) for x in range(8)]
    
    ms = 1.0*ms/1000
    candidates = []
    for tickidx in xrange(8):
        for tipidx in range(4):
            for PR in xrange(256):
                T = 1.0 * PR * TIP[tipidx] / TICKSPD[tickidx]
                if abs(T-ms) < .010:
                    candidates.append((T, tickidx, tipidx, PR))
    diff = 1024
    best = None
    for c in candidates:
        if abs(c[0] - ms) < diff:
            best = c
            diff = abs(c[0] - ms)
    return best
    #return ms, candidates, best
            
def invertBits(data):
    output = []
    ldata = len(data)
    off = 0

    if ldata&1:
        output.append( chr( ord( data[0] ) ^ 0xff) )
        off = 1

    if ldata&2:
        output.append( struct.pack( "<H", struct.unpack( "<H", data[off:off+2] )[0] ^ 0xffff) )
        off += 2

    #method 1
    #for idx in xrange( off, ldata, 4):
    #    output.append( struct.pack( "<I", struct.unpack( "<I", data[idx:idx+4] )[0] & 0xffff) )

    #method2
    count = ldata / 4
    #print ldata, count
    numlist = struct.unpack( "<%dI" % count, data[off:] )
    modlist = [ struct.pack("<L", (x^0xffffffff) ) for x in numlist ]
    output.extend(modlist)

    return ''.join(output)




class FHSSNIC(USBDongle):
    def __init__(self, idx=0, debug=False, copyDongle=None):
        USBDongle.__init__(self, idx, debug, copyDongle)

    def setRfMode(self, rfmode, parms=''):
        r = self.send(APP_NIC, NIC_RFMODE, "%c"%rfmode + parms)

    def setAESmode(self, aesmode=AES_CRYPTO_DEFAULT):
        '''
        set AES crypto co-processor mode.
        crypto operations on inbound and outbound RF packets are independently supported
        as is the type of operation. normally this would be ENCRYPT on outbound and DECRYPT
        on inbound.
        aesmode is a bitfield. the upper half mirrors the CC1111 standard modes (CBC, ECB etc.),
        and the lower half flags whether to encrypt or not on inbound/outbound as well as which
        operation to perform:

          aesmode[7:4]     ENCCS_MODE...
          aesmode[3]       OUTBOUND 0 == OFF, 1 == ON
          aesmode[2]       OUTBOUND 0 == Decrypt, 1 == Encrypt
          aesmode[1]       INBOUND  0 == OFF, 1 == ON
          aesmode[0]       INBOUND  0 == Decrypt, 1 == Encrypt

        the following are defined in chipcondefs.

        valid CC1111 modes are:

          ENCCS_MODE_CBC
          ENCCS_MODE_CBCMAC
          ENCCS_MODE_CFB
          ENCCS_MODE_CTR
          ENCCS_MODE_ECB
          ENCCS_MODE_OFB

        valid AES operational modes are:

          AES_CRYPTO_IN_ON
          AES_CRYPTO_IN_OFF
          AES_CRYPTO_IN_ENCRYPT
          AES_CRYPTO_IN_DECRYPT
          AES_CRYPTO_OUT_ON
          AES_CRYPTO_OUT_OFF
          AES_CRYPTO_OUT_ENCRYPT
          AES_CRYPTO_OUT_DECRYPT

        aesmode is made up of the appropriate combination of the above.
        default is CBC mode, crypto enabled IN and OUT:

          (ENCCS_MODE_CBC | AES_CRYPTO_OUT_ON | AES_CRYPTO_OUT_ENCRYPT | AES_CRYPTO_IN_ON | AES_CRYPTO_IN_DECRYPT)

        '''
        return self.send(APP_NIC, NIC_SET_AES_MODE, "%c"%aesmode)

    def getAESmode(self):
        '''
        get the currently set AES co-processor mode
        '''
        return self.send(APP_NIC, NIC_GET_AES_MODE, "")

    def setAESiv(self, iv= '\0'*16):
        '''
        set the AES IV. this will persist until the next reboot, but it should be noted that some modes
        update the IV automatically with each operation, so care must be taken with the higher level 
        protocol to ensure lost packets etc. do not cause synchronisation problems. IV must be 128 bits.
        '''
        return self.send(APP_NIC, NIC_SET_AES_IV, iv)

    def setAESkey(self, key= '\0'*16):
        '''
        set the AES key. this will persist until the next reboot. key must be 128 bits.
        '''
        return self.send(APP_NIC, NIC_SET_AES_KEY, key)

    # set repeat & offset to optionally repeat tx of a section of the data block. repeat of 65535 means 'forever'
    def RFxmit(self, data, repeat=0, offset=0):
        # calculate wait time
        waitlen = len(data)
        waitlen += repeat * (len(data) - offset)
        wait = USB_TX_WAIT * ((waitlen / RF_MAX_TX_BLOCK) + 1)
        self.send(APP_NIC, NIC_XMIT, "%s" % struct.pack("<HHH",len(data),repeat,offset)+data, wait=wait)

    # set blocksize to larger than 255 to receive large blocks or 0 to revert to normal
    def RFrecv(self, timeout=USB_RX_WAIT, blocksize=None):
        if not blocksize == None:
            if blocksize > EP5OUT_BUFFER_SIZE: 
                raise(Exception("Blocksize too large. Maximum %d") % EP5OUT_BUFFER_SIZE)
            self.send(APP_NIC, NIC_SET_RECV_LARGE, "%s" % struct.pack("<H",blocksize))
        return self.recv(APP_NIC, NIC_RECV, timeout)

    def RFlisten(self):
        ''' just sit and dump packets as they come in
        kinda like discover() but without changing any of the communications settings '''
        while not keystop():

            try:
                y, t = self.RFrecv()
                print "(%5.3f) Received:  %s" % (t, y.encode('hex'))

            except ChipconUsbTimeoutException:
                pass
            except KeyboardInterrupt:
                print "Please press <enter> to stop"

        sys.stdin.read(1)

    def RFcapture(self):
        ''' dump packets as they come in, but return a list of packets when you exit capture mode.
        kinda like discover() but without changing any of the communications settings '''
        capture = []
        while not keystop():

            try:
                y, t = self.RFrecv()
                print "(%5.3f) Received:  %s" % (t, y.encode('hex'))
                capture.append((y,t))

            except ChipconUsbTimeoutException:
                pass
            except KeyboardInterrupt:
                print "Please press <enter> to stop"

        sys.stdin.read(1)
        return capture

    def FHSSxmit(self, data):
        self.send(APP_NIC, FHSS_XMIT, "%c%s" % (len(data)+1, data))

    def changeChannel(self, chan):
        return self.send(APP_NIC, FHSS_CHANGE_CHANNEL, "%c" % (chan))

    def getChannels(self, channels=[]):
        return self.send(APP_NIC, FHSS_GET_CHANNELS, '')

    def setChannels(self, channels=[]):
        chans = ''.join(["%c" % chan for chan in channels])
        length = struct.pack("<H", len(chans))
        
        return self.send(APP_NIC, FHSS_SET_CHANNELS, length + chans)

    def nextChannel(self):
        return self.send(APP_NIC, FHSS_NEXT_CHANNEL, '' )

    def startHopping(self):
        return self.send(APP_NIC, FHSS_START_HOPPING, '')

    def stopHopping(self):
        return self.send(APP_NIC, FHSS_STOP_HOPPING, '')

    def setMACperiod(self, ms, mhz=24):
        val = calculateT2(ms, mhz)
        T, tickidx, tipidx, PR = val
        print "Setting MAC period to %f secs (%x %x %x)" % (val)
        t2ctl = (ord(self.peek(X_T2CTL)) & 0xfc)   | (tipidx)
        clkcon = (ord(self.peek(X_CLKCON)) & 0xc7) | (tickidx<<3)
        
        self.poke(X_T2PR, chr(PR))
        self.poke(X_T2CTL, chr(t2ctl))
        self.poke(X_CLKCON, chr(clkcon))
        
    def setMACdata(self, data):
        datastr = ''.join([chr(d) for x in data])
        return self.send(APP_NIC, FHSS_SET_MAC_DATA, datastr)

    def getMACdata(self):
        datastr, timestamp = self.send(APP_NIC, FHSS_GET_MAC_DATA, '')
        print (repr(datastr))
        data = struct.unpack("<BIHHHHHHBBH", datastr)
        return data

    def reprMACdata(self):
        data = self.getMACdata()
        return """\
u8 mac_state                %x
u32 MAC_threshold           %x
u16 NumChannels             %x
u16 NumChannelHops          %x
u16 curChanIdx              %x
u16 tLastStateChange        %x
u16 tLastHop                %x
u16 desperatelySeeking      %x
u8  txMsgIdx                %x
u8  txMsgIdxDone            %x
u16 synched_chans           %x

""" % data
    """
        
        
    u8 mac_state;
    // MAC parameters (FIXME: make this all cc1111fhssmac.c/h?)
    u32 g_MAC_threshold;              // when the T2 clock as overflowed this many times, change channel
    u16 g_NumChannels;                // in case of multiple paths through the available channels 
    u16 g_NumChannelHops;             // total number of channels in pattern (>= g_MaxChannels)
    u16 g_curChanIdx;                 // indicates current channel index of the hopping pattern
    u16 g_tLastStateChange;
    u16 g_tLastHop;
    u16 g_desperatelySeeking;
    u8  g_txMsgIdx;
    """
    
    def getMACthreshold(self):
        return self.send(APP_NIC, FHSS_SET_MAC_THRESHOLD, struct.pack("<I",value))

    def setMACthreshold(self, value):
        return self.send(APP_NIC, FHSS_SET_MAC_THRESHOLD, struct.pack("<I",value))

    def setFHSSstate(self, state):
        return self.send(APP_NIC, FHSS_SET_STATE, struct.pack("<I",state))
        
    def getFHSSstate(self):
        state = self.send(APP_NIC, FHSS_GET_STATE, '')
        #print repr(state)
        state = ord(state[0])
        return FHSS_STATES[state], state
                                
    def mac_SyncCell(self, CellID=0x0000):
        return self.send(APP_NIC, FHSS_START_SYNC, struct.pack("<H",CellID))
                
    def setPktAddr(self, addr):
        return self.poke(ADDR, chr(addr))

    def getPktAddr(self):
        return self.peek(ADDR)

    def discover(self, lowball=1, debug=None, length=30, IdentSyncWord=False, SyncWordMatchList=None, Search=None, RegExpSearch=None):
        '''
        discover() sets lowball mode to the mode requested (length too), and begins to dump packets to the screen.  
                press <enter> to quit, and your radio config will be set back to its original configuration.

            lowball             - lowball level of choosing (see help on lowball)
            debug               - sets _debug to this setting if not None.  
            length              - arbitrary length of bytes we want to see per pseudopacket. (should be enough to identify interesting packets, but not too long)
            IdentSyncWord       - look for preamble in each packet and determine possible sync-words in use
            SyncWordMatchList   - attempt to find *these* sync words (provide a list)
            Search              - byte string to search through each received packet for (real bytes, not hex repr)
            RegExpSearch        - regular expression to search through received bytes (not the hex repr that is printed)

        '''
        oldebug = self._debug
        if IdentSyncWord and lowball <= 1:
            print "Entering Discover mode and searching for possible SyncWords..."
            if SyncWordMatchList is not None:
                print "  seeking one of: %s" % repr([hex(x) for x in SyncWordMatchList])

        else:
            if IdentSyncWord and lowball > 1: 
                print "-- lowball too high -- ignoring request to IdentSyncWord"
                IdentSyncWord = False

            print "Entering Discover mode..."

        self.lowball(level=lowball, length=length)
        if debug is not None:
            self._debug = debug

        if Search is not None:
            print "Search:",repr(Search)

        if RegExpSearch is not None:
            print "RegExpSearch:",repr(RegExpSearch)

        while not keystop():

            try:
                y, t = self.RFrecv()
                yhex = y.encode('hex')

                print "(%5.3f) Received:  %s" % (t, yhex)
                if RegExpSearch is not None:
                    ynext = y
                    for loop in range(8):
                        if (re.Search(RegExpSearch, ynext) is not None):
                            print "    REG EXP SEARCH SUCCESS:",RegExpSearch
                        ynext = bits.shiftString(ynext, 1)

                if Search is not None:
                    ynext = y
                    for loop in range(8):
                        if (Search in ynext):
                            print "    SEARCH SUCCESS:",Search
                        ynext = bits.shiftString(ynext, 1)

                if IdentSyncWord:
                    if lowball == 1:
                        y = '\xaa\xaa' + y

                    poss = bits.findDword(y)
                    if len(poss):
                        print "  possible Sync Dwords: %s" % repr([hex(x) for x in poss])

                    if SyncWordMatchList is not None:
                        for x in poss:
                            if x in SyncWordMatchList:
                                print "MATCH WITH KNOWN SYNC WORD:" + hex(x)

            except ChipconUsbTimeoutException:
                pass
            except KeyboardInterrupt:
                print "Please press <enter> to stop"

        sys.stdin.read(1)
        self._debug = oldebug
        self.lowballRestore()
        print "Exiting Discover mode..."

    def testTX(self, data="XYZABCDEFGHIJKL"):
        while (sys.stdin not in select.select([sys.stdin],[],[],0)[0]):
            time.sleep(.4)
            print "transmitting %s" % repr(data)
            self.RFxmit(data)
        sys.stdin.read(1)


def unittest(dongle):
    import cc1111client
    cc1111client.unittest(dongle)

    print "\nTesting FHSS State set/get"
    fhssstate = dongle.getFHSSstate()
    print repr(fhssstate)
    for stateidx in range(FHSS_LAST_STATE+1):
        print repr(dongle.setFHSSstate(stateidx))
        print repr(dongle.getFHSSstate())

    print repr(dongle.setFHSSstate(fhssstate[1] ))
    print repr(dongle.getFHSSstate())

if __name__ == "__main__":
    idx = 0
    if len(sys.argv) > 1:
        idx = int(sys.argv.pop())
    d = FHSSNIC(idx=idx)

