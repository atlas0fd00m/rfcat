#!/usr/bin/env ipython
import sys, usb, threading, time, struct
#from chipcondefs import *
from cc1111client import *

APP_NIC =                       0x42
NIC_RECV =                      0x1
NIC_XMIT =                      0x2
NIC_SET_ID =                    0x3
NIC_RFMODE =                    0x4

FHSS_SET_CHANNELS =             0x10
FHSS_NEXT_CHANNEL =             0x11
FHSS_CHANGE_CHANNEL =           0x12
FHSS_SET_MAC_THRESHOLD =        0x13
FHSS_GET_MAC_THRESHOLD =        0x14
FHSS_SET_MAC_DATA =             0x15
FHSS_GET_MAC_DATA =             0x16
FHSS_XMIT =                     0x17

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
            

class FHSSNIC(USBDongle):
    def __init__(self, idx=0, debug=False):
        USBDongle.__init__(self, idx, debug)

    def setRfMode(self, rfmode, parms=''):
        r = self.send(APP_NIC, NIC_RFMODE, "%c"%rfmode + parms)

    def RFxmit(self, data):
        self.send(APP_NIC, NIC_XMIT, "%c%s" % (len(data)+1, data))

    def RFrecv(self, timeout=100):
        return self.recv(APP_NIC, NIC_RECV, timeout)

    def FHSSxmit(self, data):
        self.send(APP_NIC, FHSS_XMIT, "%c%s" % (len(data)+1, data))

    def changeChannel(self, chan):
        return self.send(APP_NIC, FHSS_CHANGE_CHANNEL, "%c" % (chan))

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
        datastr = self.send(APP_NIC, FHSS_GET_MAC_DATA, '')
        print (repr(datastr))
        data = struct.unpack("<BIHHHHHHBBH", datastr[4:])
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

