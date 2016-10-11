#!/usr/bin/env ipython
import re
import sys
import usb
import code
import time
import struct
import pickle
import threading
#from chipcondefs import *
from chipcon_usb import *

# band limits in Hz
FREQ_MIN_300  = 281000000
FREQ_MAX_300  = 361000000
FREQ_MIN_400  = 378000000
FREQ_MAX_400  = 481000000
FREQ_MIN_900  = 749000000
FREQ_MAX_900  = 962000000

# band transition points in Hz
FREQ_EDGE_400 = 369000000
FREQ_EDGE_900 = 615000000

# VCO transition points in Hz
FREQ_MID_300  = 318000000
FREQ_MID_400  = 424000000
FREQ_MID_900  = 848000000

SYNCM_NONE                      = 0
SYNCM_15_of_16                  = 1
SYNCM_16_of_16                  = 2
SYNCM_30_of_32                  = 3
SYNCM_CARRIER                   = 4
SYNCM_CARRIER_15_of_16          = 5
SYNCM_CARRIER_16_of_16          = 6
SYNCM_CARRIER_30_of_32          = 7

RF_SUCCESS                      = 0

RF_MAX_TX_BLOCK                 = 255
RF_MAX_TX_CHUNK                 = 240 # must match MAX_TX_MSGLEN in firmware/include/FHSS.h
                                      # and be divisible by 16 for crypto operations
RF_MAX_TX_LONG                  = 65535
RF_MAX_RX_BLOCK                 = 512 # must match BUFFER_SIZE definition in firmware/include/cc1111rf.h

APP_NIC =                       0x42
APP_SPECAN =                    0x43

NIC_RECV =                      0x1
NIC_XMIT =                      0x2
NIC_SET_ID =                    0x3
NIC_SET_RECV_LARGE =            0x5
NIC_SET_AES_MODE =              0x6
NIC_GET_AES_MODE =              0x7
NIC_SET_AES_IV =                0x8
NIC_SET_AES_KEY =               0x9
NIC_SET_AMP_MODE =              0xa
NIC_GET_AMP_MODE =              0xb
NIC_XMIT_LONG =                 0xc
NIC_XMIT_LONG_MORE =            0xd

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
                
"""  MODULATIONS
Note that MSK is only supported for data rates above 26 kBaud and GFSK,
ASK , and OOK is only supported for data rate up until 250 kBaud. MSK
cannot be used if Manchester encoding/decoding is enabled.
"""
MOD_2FSK                        = 0x00
MOD_GFSK                        = 0x10
MOD_ASK_OOK                     = 0x30
MOD_MSK                         = 0x70
MANCHESTER                      = 0x08

MODULATIONS = {
        MOD_2FSK    : "2FSK",
        MOD_GFSK    : "GFSK",
        MOD_ASK_OOK : "ASK/OOK",
        MOD_MSK     : "MSK",
        MOD_2FSK | MANCHESTER    : "2FSK/Manchester encoding",
        MOD_GFSK | MANCHESTER    : "GFSK/Manchester encoding",
        MOD_ASK_OOK | MANCHESTER : "ASK/OOK/Manchester encoding",
        MOD_MSK  | MANCHESTER    : "MSK/Manchester encoding",
        }

SYNCMODES = {
        SYNCM_NONE: "None",
        SYNCM_15_of_16: "15 of 16 bits must match",
        SYNCM_16_of_16: "16 of 16 bits must match",
        SYNCM_30_of_32: "30 of 32 sync bits must match",
        SYNCM_CARRIER: "Carrier Detect",
        SYNCM_CARRIER_15_of_16: "Carrier Detect and 15 of 16 sync bits must match",
        SYNCM_CARRIER_16_of_16: "Carrier Detect and 16 of 16 sync bits must match",
        SYNCM_CARRIER_30_of_32: "Carrier Detect and 30 of 32 sync bits must match",
        }

BSLIMITS = {
        BSCFG_BS_LIMIT_0: "No data rate offset compensation performed",
        BSCFG_BS_LIMIT_3: "+/- 3.125% data rate offset",
        BSCFG_BS_LIMIT_6: "+/- 6.25% data rate offset",
        BSCFG_BS_LIMIT_12: "+/- 12.5% data rate offset",
        }

AESMODES = {
        ENCCS_MODE_CBC: "CBC - Cipher Block Chaining",
        ENCCS_MODE_CBCMAC: "CBC-MAC - Cipher Block Chaining Message Authentication Code",
        ENCCS_MODE_CFB: "CFB - Cipher Feedback",
        ENCCS_MODE_CTR: "CTR - Counter",
        ENCCS_MODE_ECB: "ECB - Electronic Codebook",
        ENCCS_MODE_OFB: "OFB - Output Feedback",
        }

NUM_PREAMBLE = [2, 3, 4, 6, 8, 12, 16, 24 ]

ADR_CHK_TYPES = [
        "No address check",
        "Address Check, No Broadcast",
        "Address Check, 0x00 is broadcast",
        "Address Check, 0x00 and 0xff are broadcast",
        ]



PKT_FORMATS = [
        "Normal mode",
        "reserved...",
        "Random TX mode",
        "reserved",
        ]

LENGTH_CONFIGS = [
        "Fixed Packet Mode",
        "Variable Packet Mode (len=first byte after sync word)",
        "reserved",
        "reserved",
        ]
MARC_STATE_MAPPINGS = [
    (0, 'MARC_STATE_SLEEP', RFST_SIDLE),
    (1, 'MARC_STATE_IDLE', RFST_SIDLE),
    (3, 'MARC_STATE_VCOON_MC', RFST_SIDLE),
    (4, 'MARC_STATE_REGON_MC', RFST_SIDLE),
    (5, 'MARC_STATE_MANCAL', RFST_SCAL),
    (6, 'MARC_STATE_VCOON', RFST_SIDLE),
    (7, 'MARC_STATE_REGON', RFST_SIDLE),
    (8, 'MARC_STATE_STARTCAL', RFST_SCAL),
    (9, 'MARC_STATE_BWBOOST', RFST_SIDLE),
    (10, 'MARC_STATE_FS_LOCK', RFST_SIDLE),
    (11, 'MARC_STATE_IFADCON', RFST_SIDLE),
    (12, 'MARC_STATE_ENDCAL', RFST_SCAL),
    (13, 'MARC_STATE_RX', RFST_SRX),
    (14, 'MARC_STATE_RX_END', RFST_SRX ),     # FIXME: this should actually be the config setting in register
    (15, 'MARC_STATE_RX_RST', RFST_SRX),
    (16, 'MARC_STATE_TXRX_SWITCH', RFST_SIDLE),
    (17, 'MARC_STATE_RX_OVERFLOW', RFST_SIDLE),
    (18, 'MARC_STATE_FSTXON', RFST_SFSTXON),
    (19, 'MARC_STATE_TX', RFST_STX),
    (20, 'MARC_STATE_TX_END', RFST_STX),        # FIXME: this should actually be the config setting in register
    (21, 'MARC_STATE_RXTX_SWITCH', RFST_SIDLE),
    (22, 'MARC_STATE_TX_UNDERFLOW', RFST_SIDLE) # FIXME: this should actually be the config setting in register
]

MODES = {}
for num,name,rfst in MARC_STATE_MAPPINGS:
    MODES[num] = name
    MODES[name] = num


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

def makeFriendlyAscii(instring):
    out = []
    start = 0
    last = -1
    instrlen = len(instring)

    for cidx in xrange(instrlen):
        if (0x20 < ord(instring[cidx]) < 0x7f):
            if last < cidx-1:
                out.append( "." * (cidx-1-last))
                start = cidx
            last = cidx
        else:
            if last == cidx-1:
                out.append( instring[ start:last+1 ] )

    if last != cidx:
        out.append( "." * (cidx-last) )
    else: # if start == 0:
        out.append( instring[ start: ] )

    return ''.join(out)




def calculateT2(tick_ms, mhz=24):
    # each tick, not each cycle
    TICKSPD = [(mhz*1000000/pow(2,x)) for x in range(8)]
    
    tick_ms = 1.0*tick_ms/1000
    candidates = []
    for tickidx in xrange(8):
        for tipidx in range(4):
            for PR in xrange(256):
                T = 1.0 * PR * TIP[tipidx] / TICKSPD[tickidx]
                if abs(T-tick_ms) < .010:
                    candidates.append((T, tickidx, tipidx, PR))
    diff = 1024
    best = None
    for c in candidates:
        if abs(c[0] - tick_ms) < diff:
            best = c
            diff = abs(c[0] - tick_ms)
    return best
    #return ms, candidates, best
            

class EnDeCode:
    def encode(self, msg):
        raise Exception("EnDeCode.encode() not implemented.  Each subclass must implement their own")
    def decode(self, msg):
        raise Exception("EnDeCode.encode() not implemented.  Each subclass must implement their own")


def savePkts(pkts, filename):
    pickle.dump(pkts, file(filename, 'a'))
def loadPkts(filename):
    return pickle.load( file(filename, 'r'))

def printSyncWords(syncworddict):
    print "SyncWords seen:"

    tmp = []
    for x,y in syncworddict.items():
        tmp.append((y,x))
    tmp.sort()
    for y,x in tmp:
        print("0x%.4x: %d" % (x,y))

CHIPmhz = {
    0x91: 24,
    0x81: 26,
    0x11: 24,
    0x01: 26,
}

class NICxx11(USBDongle):
    '''
    NICxx11 implements radio-specific code for CCxx11 chips (2511, 1111),
    as the xx11 chips keep a relatively consistent radio interface and use
    the same radio concepts (frequency, channels, etc) and functionality
    (AES, Manchester Encoding, etc).
    '''
    def __init__(self, idx=0, debug=False, copyDongle=None, RfMode=RFST_SRX):
        USBDongle.__init__(self, idx, debug, copyDongle, RfMode)
        self.max_packet_size = RF_MAX_RX_BLOCK
        self.endec = None
        self.mhz = CHIPmhz.get(self.chipnum)
        self.freq_offset_accumulator = 0

    ######## RADIO METHODS #########
    def setRfMode(self, rfmode, parms=''):
        '''
        sets the radio state to "rfmode", and makes 
        '''
        self._rfmode = rfmode
        r = self.send(APP_SYSTEM, SYS_CMD_RFMODE, "%c" % (self._rfmode) + parms)

    ### set standard radio state to TX/RX/IDLE (TX is pretty much only good for jamming).  TX/RX modes are set to return to whatever state you choose here.
    def setModeTX(self):
        '''
        BOTH: set radio to TX state
        AND:  set radio to return to TX state when done with other states
        '''
        self.setRfMode(RFST_STX)       #FIXME: when firmware makes the change, so must this
        
    def setModeRX(self):
        '''
        BOTH: set radio to RX state
        AND:  set radio to return to RX state when done with other states
        '''
        self.setRfMode(RFST_SRX)
        
    def setModeIDLE(self):
        '''
        BOTH: set radio to IDLE state
        AND:  set radio to return to IDLE state when done with other states
        '''
        self.setRfMode(RFST_SIDLE)
        

    ### send raw state change to radio (doesn't update the return state for after RX/TX occurs)
    def strobeModeTX(self):
        '''
        set radio to TX state (transient)
        '''
        self.poke(X_RFST, "%c"%RFST_STX)

    def strobeModeRX(self):
        '''
        set radio to RX state (transient)
        '''
        self.poke(X_RFST, "%c"%RFST_SRX)

    def strobeModeIDLE(self):
        '''
        set radio to IDLE state (transient)
        '''
        self.poke(X_RFST, "%c"%RFST_SIDLE)

    def strobeModeFSTXON(self):
        '''
        set radio to FSTXON state (transient)
        '''
        self.poke(X_RFST, "%c"%RFST_SFSTXON)

    def strobeModeCAL(self):
        '''
        set radio to CAL state (will return to whichever state is configured (via setMode* functions)
        '''
        self.poke(X_RFST, "%c"%RFST_SCAL)
        
    def strobeModeReturn(self, marcstate=None):
        """
        attempts to return the the correct mode after configuring some radio register(s).
        it uses the marcstate provided (or self.radiocfg.marcstate if none are provided) to determine how to strobe the radio.
        """
        #if marcstate is None:
            #marcstate = self.radiocfg.marcstate
        #if self._debug: print("MARCSTATE: %x   returning to %x" % (marcstate, MARC_STATE_MAPPINGS[marcstate][2]) )
        #self.poke(X_RFST, "%c"%MARC_STATE_MAPPINGS[marcstate][2])
        self.poke(X_RFST, "%c" % self._rfmode)

        
        
    
    #### radio config #####
    def getRadioConfig(self):
        bytedef = self.peek(0xdf00, 0x3e)
        self.radiocfg.vsParse(bytedef)
        return bytedef

    def setRadioConfig(self, bytedef = None):
        if bytedef is None:
            bytedef = self.radiocfg.vsEmit()

        statestr, marcstate = self.getMARCSTATE()
        if marcstate != MARC_STATE_IDLE:
            self.strobeModeIDLE()

        self.poke(0xdf00, bytedef)

        self.strobeModeReturn(marcstate)
        #if (marcstate == MARC_STATE_RX):
            #self.strobeModeRX()
        #elif (marcstate == MARC_STATE_TX):
            #self.strobeModeTX()
    
        self.getRadioConfig()

        return bytedef


    ##### GETTER/SETTERS for Radio Config/Status #####
    ### radio state
    def getMARCSTATE(self, radiocfg=None):
        if radiocfg is None:
            self.getRadioConfig()
            radiocfg=self.radiocfg

        mode = radiocfg.marcstate
        return (MODES[mode], mode)

    def setRFRegister(self, regaddr, value, suppress=False):
        '''
        set the radio register 'regaddr' to 'value' (first setting RF state to IDLE, then returning to RX/TX)
            value is always considered a 1-byte value
            if 'suppress' the radio state (RX/TX/IDLE) is not modified
        '''
        if suppress:
            self.poke(regaddr, chr(value))
            return
            
        marcstate = self.radiocfg.marcstate
        if marcstate != MARC_STATE_IDLE:
            self.strobeModeIDLE()
            
        self.poke(regaddr, chr(value))
        
        self.strobeModeReturn(marcstate)
        #if (marcstate == MARC_STATE_RX):
            #self.strobeModeRX()
        #elif (marcstate == MARC_STATE_TX):
            #self.strobeModeTX()
        # if other than these, we can stay in IDLE

    def setRFbits(self, addr, bitnum, bitsz, val, suppress=False):
        ''' sets individual bits of a register '''
        mask = ((1<<bitsz) - 1) << bitnum
        rmask = ~mask

        temp = ord(self.peek(addr)) & rmask
        temp |= ((val << bitnum) & mask)

        self.setRFRegister(addr, temp, suppress=suppress)

    def setEnableCCA(self, mode=3, absthresh=0, relthresh=1, magn=3, radiocfg=None):
        '''
        4 modes of CCA:
            0 - ALWAYS, no CCA
            1 - If RSSI below threshold
            2 - Unless currently receiving a packet
            3 - If RSSI below threshold unless currently receiving a packet
        '''
        if radiocfg is None:
            radiocfg = self.radiocfg
        else:
            applyConfig = False

        mcsm1 = radiocfg.mcsm1 & 0xf
        mcsm1 |= (mode << 4)
        radiocfg.mcsm1 = mcsm1

        agcctrl2 = radiocfg.agcctrl2 & 0xf8
        agcctrl2 |= magn

        agcctrl1 = radiocfg.agcctrl1 & 0xc0
        agcctrl1 |= (absthresh & 0xf)
        agcctrl1 |= ((relthresh << 4) & 0x3)

        self.setRFRegister(MCSM1, mcsm1)
        self.setRFRegister(AGCCTRL1, agcctrl1)
        self.setRFRegister(AGCCTRL2, agcctrl2)

    def setFreq(self, freq=902000000, mhz=24, radiocfg=None, applyConfig=True):        
        if radiocfg is None:
            radiocfg = self.radiocfg
        else:
            applyConfig = False

        freqmult = (0x10000 / 1000000.0) / mhz
        num = int(freq * freqmult)
        radiocfg.freq2 = num >> 16
        radiocfg.freq1 = (num>>8) & 0xff
        radiocfg.freq0 = num & 0xff

        if (freq > FREQ_EDGE_900 and freq < FREQ_MID_900) or (freq > FREQ_EDGE_400 and freq < FREQ_MID_400) or (freq < FREQ_MID_300):
            # select low VCO
            radiocfg.fscal2 = 0x0A
        elif freq <1e9 and ((freq > FREQ_MID_900) or (freq > FREQ_MID_400) or (freq > FREQ_MID_300)):
            # select high VCO
            radiocfg.fscal2 = 0x2A

        if applyConfig:
            marcstate = radiocfg.marcstate
            if marcstate != MARC_STATE_IDLE:
                self.strobeModeIDLE()
            self.poke(FREQ2, struct.pack("3B", self.radiocfg.freq2, self.radiocfg.freq1, self.radiocfg.freq0))
            self.poke(FSCAL2, struct.pack("B", self.radiocfg.fscal2))
            
            self.strobeModeReturn(marcstate)
            #if (radiocfg.marcstate == MARC_STATE_RX):
                #self.strobeModeRX()
            #elif (radiocfg.marcstate == MARC_STATE_TX):
                #self.strobeModeTX()

    def getFreq(self, mhz=24, radiocfg=None):
        freqmult = (0x10000 / 1000000.0) / mhz
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
            
        num = (radiocfg.freq2<<16) + (radiocfg.freq1<<8) + radiocfg.freq0
        freq = num / freqmult
        return freq, hex(num)

    def getFreqEst(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        return radiocfg.freqest

    # auto-adjust frequency offset based on internal estimate from last received packet (FSK/MSK modes only)
    # note radio must be in IDLE mode when called for this to have any effect
    # the TI design note for this is missing from TI's main website but can be found here:
    # http://e2e.ti.com/cfs-file/__key/telligent-evolution-components-attachments/00-155-01-00-00-73-46-38/DN015_5F00_Permanent_5F00_Frequency_5F00_Offset_5F00_Compensation.pdf
    def adjustFreqOffset(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        self.freq_offset_accumulator += self.getFreqEst(radiocfg)
        self.freq_offset_accumulator &= 0xff
        self.setFsOffset(self.freq_offset_accumulator, mhz, radiocfg)

    # set 'standard' power - for more complex power shaping this will need to be done manually
    def setPower(self, power=None, radiocfg=None, invert=False):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        mod= self.getMdmModulation(radiocfg=radiocfg)

        # we may be only changing PA_POWER, not power levels
        if power is not None:
            if mod == MOD_ASK_OOK and not invert:
                radiocfg.pa_table0= 0x00
                radiocfg.pa_table1= power
            else:
                radiocfg.pa_table0= power
                radiocfg.pa_table1= 0x00
            self.setRFRegister(PA_TABLE0, radiocfg.pa_table0)
            self.setRFRegister(PA_TABLE1, radiocfg.pa_table1)

        radiocfg.frend0 &= ~FREND0_PA_POWER
        if mod == MOD_ASK_OOK:
            radiocfg.frend0 |= 0x01

        self.setRFRegister(FREND0, radiocfg.frend0)

    # max power settings are frequency dependent, so set frequency before calling
    def setMaxPower(self, radiocfg=None, invert=False):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        freq= self.getFreq(radiocfg=radiocfg)[0]

        if freq <= 400000000:
            power= 0xC2
        elif freq <= 464000000:
            power= 0xC0
        elif freq <= 900000000:
            power= 0xC2
        else:
            power= 0xC0

        self.setPower(power, radiocfg=radiocfg, invert=invert)

    def setMdmModulation(self, mod, radiocfg=None, invert=False):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        if (mod) & ~MDMCFG2_MOD_FORMAT:
            raise(Exception("Please use constants MOD_FORMAT_* to specify modulation and "))

        radiocfg.mdmcfg2 &= ~MDMCFG2_MOD_FORMAT
        radiocfg.mdmcfg2 |= (mod)

        power= None
        # ASK_OOK needs to flip power table
        if mod == MOD_ASK_OOK and not invert:
            if radiocfg.pa_table1 == 0x00 and radiocfg.pa_table0 != 0x00:
                power= radiocfg.pa_table0
        else:
            if radiocfg.pa_table0 == 0x00 and radiocfg.pa_table1 != 0x00:
                power= radiocfg.pa_table1

        self.setRFRegister(MDMCFG2, radiocfg.mdmcfg2)
        self.setPower(power, radiocfg=radiocfg, invert=invert)

    def getMdmModulation(self, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        mdmcfg2 = radiocfg.mdmcfg2
        mod = (mdmcfg2) & MDMCFG2_MOD_FORMAT
        return mod

    def getMdmChanSpc(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        chanspc_m = radiocfg.mdmcfg0
        chanspc_e = radiocfg.mdmcfg1 & 3
        chanspc = 1000000.0 * mhz/pow(2,18) * (256 + chanspc_m) * pow(2, chanspc_e)
        #print "chanspc_e: %x   chanspc_m: %x   chanspc: %f hz" % (chanspc_e, chanspc_m, chanspc)
        return (chanspc)

    def setMdmChanSpc(self, chanspc=None, chanspc_m=None, chanspc_e=None, mhz=24, radiocfg=None):
        '''
        calculates the appropriate exponent and mantissa and updates the correct registers
        chanspc is in kHz.  if you prefer, you may set the chanspc_m and chanspc_e settings 
        directly.

        only use one or the other:
        * chanspc
        * chanspc_m and chanspc_e
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        if (chanspc != None):
            for e in range(4):
                m = int(((chanspc * pow(2,18) / (1000000.0 * mhz * pow(2,e)))-256) +.5)    # rounded evenly
                if m < 256:
                    chanspc_e = e
                    chanspc_m = m
                    break
        if chanspc_e is None or chanspc_m is None:
            raise(Exception("ChanSpc does not translate into acceptable parameters.  Should you be changing this?"))

        #chanspc = 1000000.0 * mhz/pow(2,18) * (256 + chanspc_m) * pow(2, chanspc_e)
        #print "chanspc_e: %x   chanspc_m: %x   chanspc: %f hz" % (chanspc_e, chanspc_m, chanspc)
        
        radiocfg.mdmcfg1 &= ~MDMCFG1_CHANSPC_E            # clear out old exponent value
        radiocfg.mdmcfg1 |= chanspc_e
        radiocfg.mdmcfg0 = chanspc_m
        self.setRFRegister(MDMCFG1, (radiocfg.mdmcfg1))
        self.setRFRegister(MDMCFG0, (radiocfg.mdmcfg0))

    def makePktVLEN(self, maxlen=RF_MAX_TX_BLOCK, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        if maxlen > RF_MAX_TX_BLOCK:
            raise(Exception("Packet too large (%d bytes). Maximum variable length packet is %d bytes." % (maxlen, RF_MAX_TX_BLOCK)))

        radiocfg.pktctrl0 &= ~PKTCTRL0_LENGTH_CONFIG
        radiocfg.pktctrl0 |= 1
        radiocfg.pktlen = maxlen
        self.setRFRegister(PKTCTRL0, (radiocfg.pktctrl0))
        self.setRFRegister(PKTLEN, (radiocfg.pktlen))


    def makePktFLEN(self, flen=RF_MAX_TX_BLOCK, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        if flen > EP5OUT_BUFFER_SIZE - 4:
            raise(Exception("Packet too large (%d bytes). Maximum fixed length packet is %d bytes." % (flen, EP5OUT_BUFFER_SIZE - 6)))

        radiocfg.pktctrl0 &= ~PKTCTRL0_LENGTH_CONFIG
        # if we're sending a large block, pktlen is dealt with by the firmware
        # using 'infinite' mode
        if flen > RF_MAX_TX_BLOCK:
            radiocfg.pktlen = 0x00
        else:
            radiocfg.pktlen = flen
        self.setRFRegister(PKTCTRL0, (radiocfg.pktctrl0))
        self.setRFRegister(PKTLEN, (radiocfg.pktlen))

    def getPktLEN(self):
        '''
        returns (pktlen, pktctrl0)
        '''
        return (self.radiocfg.pktlen, self.radiocfg.pktctrl0 & PKTCTRL0_LENGTH_CONFIG)
        
    def setEnablePktCRC(self, enable=True, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        crcE = (0,1)[enable]<<2
        crcM = ~(1<<2)
        radiocfg.pktctrl0 &= crcM
        radiocfg.pktctrl0 |= crcE
        self.setRFRegister(PKTCTRL0, (radiocfg.pktctrl0))

    def getEnablePktCRC(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        return (radiocfg.pktctrl0 >>2) & 0x1

    def setEnablePktDataWhitening(self, enable=True, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        dwEnable = (0,1)[enable]<<6
        radiocfg.pktctrl0 &= ~PKTCTRL0_WHITE_DATA
        radiocfg.pktctrl0 |= dwEnable
        self.setRFRegister(PKTCTRL0, (radiocfg.pktctrl0))

    def getEnablePktDataWhitening(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        return (radiocfg.pktctrl0 >>6) & 0x1

    def setPktPQT(self, num=3, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        num &=  7
        num <<= 5
        numM = ~(7<<5)
        radiocfg.pktctrl1 &= numM
        radiocfg.pktctrl1 |= num
        self.setRFRegister(PKTCTRL1, (radiocfg.pktctrl1))

    def getPktPQT(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        return (radiocfg.pktctrl1 >> 5) & 7

    def setEnablePktAppendStatus(self, enable=True, radiocfg=None):
        '''
        enable append status bytes. two bytes will be appended to the payload of the packet, containing
        RSSI and LQI values as well as CRC OK.
        '''
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        radiocfg.pktctrl1 &= ~PKTCTRL1_APPEND_STATUS
        radiocfg.pktctrl1 |= (enable<<2)
        self.setRFRegister(PKTCTRL1, radiocfg.pktctrl1)

    def getEnablePktAppendStatus(self, radiocfg=None):
        '''
        return append status bytes setting.
        '''
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        pktctrl1 = radiocfg.pktctrl1
        append = (pktctrl1>>2) & 0x01
        return append

    def setEnableMdmManchester(self, enable=True, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        radiocfg.mdmcfg2 &= ~MDMCFG2_MANCHESTER_EN
        radiocfg.mdmcfg2 |= (enable<<3)
        self.setRFRegister(MDMCFG2, radiocfg.mdmcfg2)

    def getEnableMdmManchester(self, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        mdmcfg2 = radiocfg.mdmcfg2
        mchstr = (mdmcfg2>>3) & 0x01
        return mchstr

    def setEnableMdmFEC(self, enable=True, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        fecEnable = (0,1)[enable]<<7
        radiocfg.mdmcfg1 &= ~MFMCFG1_FEC_EN
        radiocfg.mdmcfg1 |= fecEnable
        self.setRFRegister(MDMCFG1, (radiocfg.mdmcfg1))

    def getEnableMdmFEC(self, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        mdmcfg1 = radiocfg.mdmcfg1
        fecEnable = (mdmcfg1>>7) & 0x01
        return fecEnable

    def setEnableMdmDCFilter(self, enable=True, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        dcfEnable = (0,1)[enable]<<7
        radiocfg.mdmcfg2 &= ~MDMCFG2_DEM_DCFILT_OFF
        radiocfg.mdmcfg2 |= dcfEnable
        self.setRFRegister(MDMCFG2, radiocfg.mdmcfg2)

    def getEnableMdmDCFilter(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        dcfEnable = (radiocfg.mdmcfg2>>7) & 0x1
        return dcfEnable


    def setFsIF(self, freq_if, mhz=24, radiocfg=None):
        '''
        Note that the SmartRF Studio software
        automatically calculates the optimum register
        setting based on channel spacing and channel
        filter bandwidth. (from cc1110f32.pdf)
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        ifBits = freq_if * pow(2,10) / (1000000.0 * mhz)
        ifBits = int(ifBits + .5)       # rounded evenly

        if ifBits >0x1f:
            raise(Exception("FAIL:  freq_if is too high?  freqbits: %x (must be <0x1f)" % ifBits))
        radiocfg.fsctrl1 &= ~(0x1f)
        radiocfg.fsctrl1 |= int(ifBits)
        self.setRFRegister(FSCTRL1, (radiocfg.fsctrl1))

    def getFsIF(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        freq_if = (radiocfg.fsctrl1&0x1f) * (1000000.0 * mhz / pow(2,10))
        return freq_if


    def setFsOffset(self, if_off, mhz=24, radiocfg=None):
        '''
        Note that the SmartRF Studio software
        automatically calculates the optimum register
        setting based on channel spacing and channel
        filter bandwidth. (from cc1110f32.pdf)
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        radiocfg.fsctrl0 = if_off
        self.setRFRegister(FSCTRL0, (radiocfg.fsctrl0))

    def getFsOffset(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        freqoff = radiocfg.fsctrl0
        return freqoff

    def getChannel(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        self.getRadioConfig()
        return radiocfg.channr

    def setChannel(self, channr, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        radiocfg.channr = channr
        self.setRFRegister(CHANNR, (radiocfg.channr))

    def setMdmChanBW(self, bw, mhz=24, radiocfg=None):
        '''
        For best performance, the channel filter
        bandwidth should be selected so that the
        signal bandwidth occupies at most 80% of the
        channel filter bandwidth. The channel centre
        tolerance due to crystal accuracy should also
        be subtracted from the signal bandwidth. The
        following example illustrates this:

            With the channel filter bandwidth set to 500
            kHz, the signal should stay within 80% of 500
            kHz, which is 400 kHz. Assuming 915 MHz
            frequency and +/-20 ppm frequency uncertainty
            for both the transmitting device and the
            receiving device, the total frequency
            uncertainty is +/-40 ppm of 915 MHz, which is
            +/-37 kHz. If the whole transmitted signal
            bandwidth is to be received within 400 kHz, the
            transmitted signal bandwidth should be
            maximum 400 kHz - 2*37 kHz, which is 326
            kHz.

        DR:1.2kb Dev:5.1khz Mod:GFSK RXBW:63kHz sensitive     fsctrl1:06 mdmcfg:e5 a3 13 23 11 dev:16 foc/bscfg:17/6c agctrl:03 40 91 frend:56 10
        DR:1.2kb Dev:5.1khz Mod:GFSK RXBW:63kHz lowpower      fsctrl1:06 mdmcfg:e5 a3 93 23 11 dev:16 foc/bscfg:17/6c agctrl:03 40 91 frend:56 10    (DEM_DCFILT_OFF)
        DR:2.4kb Dev:5.1khz Mod:GFSK RXBW:63kHz sensitive     fsctrl1:06 mdmcfg:e6 a3 13 23 11 dev:16 foc/bscfg:17/6c agctrl:03 40 91 frend:56 10
        DR:2.4kb Dev:5.1khz Mod:GFSK RXBW:63kHz lowpower      fsctrl1:06 mdmcfg:e6 a3 93 23 11 dev:16 foc/bscfg:17/6c agctrl:03 40 91 frend:56 10    (DEM_DCFILT_OFF)
        DR:38.4kb Dev:20khz Mod:GFSK RXBW:94kHz sensitive     fsctrl1:08 mdmcfg:ca a3 13 23 11 dev:36 foc/bscfg:16/6c agctrl:43 40 91 frend:56 10    (IF changes, Deviation)
        DR:38.4kb Dev:20khz Mod:GFSK RXBW:94kHz lowpower      fsctrl1:08 mdmcfg:ca a3 93 23 11 dev:36 foc/bscfg:16/6c agctrl:43 40 91 frend:56 10    (.. DEM_DCFILT_OFF)

        DR:250kb Dev:129khz Mod:GFSK RXBW:600kHz sensitive    fsctrl1:0c mdmcfg:1d 55 13 23 11 dev:63 foc/bscfg:1d/1c agctrl:c7 00 b0 frend:b6 10    (IF_changes, Deviation)

        DR:500kb            Mod:MSK  RXBW:750kHz sensitive    fsctrl1:0e mdmcfg:0e 55 73 43 11 dev:00 foc/bscfg:1d/1c agctrl:c7 00 b0 frend:b6 10    (IF_changes, Modulation of course, Deviation has different meaning with MSK)
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        chanbw_e = None
        chanbw_m = None
        for e in range(4):
            m = int(((mhz*1000000.0 / (bw *pow(2,e) * 8.0 )) - 4) + .5)        # rounded evenly
            if m < 4:
                chanbw_e = e
                chanbw_m = m
                break
        if chanbw_e is None:
            raise(Exception("ChanBW does not translate into acceptable parameters.  Should you be changing this?"))

        bw = 1000.0*mhz / (8.0*(4+chanbw_m) * pow(2,chanbw_e))
        #print "chanbw_e: %x   chanbw_m: %x   chanbw: %f kHz" % (e, m, bw)

        radiocfg.mdmcfg4 &= ~(MDMCFG4_CHANBW_E | MDMCFG4_CHANBW_M)
        radiocfg.mdmcfg4 |= ((chanbw_e<<6) | (chanbw_m<<4))
        self.setRFRegister(MDMCFG4, (radiocfg.mdmcfg4))

    def getMdmChanBW(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        chanbw_e = (radiocfg.mdmcfg4 >> 6) & 0x3
        chanbw_m = (radiocfg.mdmcfg4 >> 4) & 0x3
        bw = 1000000.0*mhz / (8.0*(4+chanbw_m) * pow(2,chanbw_e))
        #print "chanbw_e: %x   chanbw_m: %x   chanbw: %f hz" % (chanbw_e, chanbw_m, bw)
        return bw

    def setMdmDRate(self, drate, mhz=24, radiocfg=None):
        ''' 
        set the baud of data being modulated through the radio
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        drate_e = None
        drate_m = None
        for e in range(16):
            m = int((drate * pow(2,28) / (pow(2,e)* (mhz*1000000.0))-256) + .5)        # rounded evenly
            if m < 256:
                drate_e = e
                drate_m = m
                break
        if drate_e is None:
            raise(Exception("DRate does not translate into acceptable parameters.  Should you be changing this?"))

        drate = 1000000.0 * mhz * (256+drate_m) * pow(2,drate_e) / pow(2,28)
        if self._debug: print "drate_e: %x   drate_m: %x   drate: %f Hz" % (drate_e, drate_m, drate)
        
        radiocfg.mdmcfg3 = drate_m
        radiocfg.mdmcfg4 &= ~MDMCFG4_DRATE_E
        radiocfg.mdmcfg4 |= drate_e
        self.setRFRegister(MDMCFG3, (radiocfg.mdmcfg3))
        self.setRFRegister(MDMCFG4, (radiocfg.mdmcfg4))

    def getMdmDRate(self, mhz=24, radiocfg=None):
        ''' 
        get the baud of data being modulated through the radio
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        drate_e = radiocfg.mdmcfg4 & 0xf
        drate_m = radiocfg.mdmcfg3

        drate = 1000000.0 * mhz * (256+drate_m) * pow(2,drate_e) / pow(2,28)
        #print "drate_e: %x   drate_m: %x   drate: %f hz" % (drate_e, drate_m, drate)
        return drate
        
        
    def setMdmDeviatn(self, deviatn, mhz=24, radiocfg=None):
        ''' 
        configure the deviation settings for the given modulation scheme
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        dev_e = None
        dev_m = None
        for e in range(8):
            m = int((deviatn * pow(2,17) / (pow(2,e)* (mhz*1000000.0))-8) + .5)        # rounded evenly
            if m < 8:
                dev_e = e
                dev_m = m
                break
        if dev_e is None:
            raise(Exception("Deviation does not translate into acceptable parameters.  Should you be changing this?"))

        dev = 1000000.0 * mhz * (8+dev_m) * pow(2,dev_e) / pow(2,17)
        #print "dev_e: %x   dev_m: %x   deviatn: %f Hz" % (e, m, dev)
        
        radiocfg.deviatn = (dev_e << 4) | dev_m
        self.setRFRegister(DEVIATN, radiocfg.deviatn)

    def getMdmDeviatn(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        dev_e = radiocfg.deviatn >> 4
        dev_m = radiocfg.deviatn & DEVIATN_DEVIATION_M
        dev = 1000000.0 * mhz * (8+dev_m) * pow(2,dev_e) / pow(2,17)
        return dev

    def getMdmSyncWord(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        return (radiocfg.sync1 << 8) + radiocfg.sync0

    def setMdmSyncWord(self, word, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        radiocfg.sync1 = word >> 8
        radiocfg.sync0 = word & 0xff
        self.setRFRegister(SYNC1, (radiocfg.sync1))
        self.setRFRegister(SYNC0, (radiocfg.sync0))

    def getMdmSyncMode(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        return radiocfg.mdmcfg2 & MDMCFG2_SYNC_MODE

    def setMdmSyncMode(self, syncmode=SYNCM_15_of_16, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        radiocfg.mdmcfg2 &= ~MDMCFG2_SYNC_MODE
        radiocfg.mdmcfg2 |= syncmode
        self.setRFRegister(MDMCFG2, (radiocfg.mdmcfg2))

    def getMdmNumPreamble(self, radiocfg=None):
        '''
        get the minimum number of preamble bits to be transmitted. note this is a flag, not a count
        so the return value must be interpeted - e.g. 0x30 == 0x03 << 4 == MFMCFG1_NUM_PREAMBLE_6 == 6 bytes
        '''
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        preamble= (radiocfg.mdmcfg1 & MFMCFG1_NUM_PREAMBLE)
        return preamble

    def setMdmNumPreamble(self, preamble=MFMCFG1_NUM_PREAMBLE_4, radiocfg=None):
        '''
        set the minimum number of preamble bits to be transmitted (default: MFMCFG1_NUM_PREAMBLE_4)
        '''
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        radiocfg.mdmcfg1 &= ~MFMCFG1_NUM_PREAMBLE
        radiocfg.mdmcfg1 |= preamble
        self.setRFRegister(MDMCFG1, (radiocfg.mdmcfg1))

    def getBSLimit(self, radiocfg=None):
        '''
        get the saturation point for the data rate offset compensation algorithm
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        return radiocfg.bscfg&BSCFG_BS_LIMIT

    def setBSLimit(self, bslimit, radiocfg=None):
        '''
        set the saturation point for the data rate offset compensation algorithm
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        radiocfg.bscfg &= ~BSCFG_BS_LIMIT
        radiocfg.bscfg |= bslimit
        self.setRFRegister(BSCFG, (radiocfg.bscfg))

    def calculateMdmDeviatn(self, mhz=24, radiocfg=None):
        ''' calculates the optimal DEVIATN setting for the current freq/baud
        * totally experimental *
        from Smart RF Studio:
        1.2 kbaud 5.1khz dev
        2.4 kbaud 5.1khz dev
        38.4 kbaud 20khz dev
        250 kbaud 129khz dev
        '''
        baud = self.getMdmDRate(mhz, radiocfg)
        if baud <= 2400:
            deviatn = 5100
        elif baud <= 38400:
            deviatn = 20000 * ((baud-2400)/36000)
        else:
            deviatn = 129000 * ((baud-38400)/211600)
        self.setMdmDeviatn(deviatn)

    def calculatePktChanBW(self, mhz=24, radiocfg=None):
        ''' calculates the optimal ChanBW setting for the current freq/baud
        * totally experimental *
        from Smart RF Studio:
        1.2 kbaud BW: 63khz
        2.4 kbaud BW: 63khz
        38.4kbaud BW: 94khz
        250 kbaud BW: 600khz
        '''
        freq, freqhex = self.getFreq()
        center_freq = freq + 14000000
        freq_uncertainty =  20e-6 * freq  # +-20ppm
        freq_uncertainty *= 2          # both xmitter and receiver
        #minbw = (2 * freq_uncertainty) + self.getMdmDRate() # uncertainty for both sender/receiver
        minbw = (self.getMdmDRate() + freq_uncertainty) 

        possibles = [ 53e3,63e3,75e3,93e3,107e3,125e3,150e3,188e3,214e3,250e3,300e3,375e3,428e3,500e3,600e3,750e3, ]
        for bw in possibles:
            #if (.8 * bw)  > minbw:      # can't occupy more the 80% of BW
            if (bw)  > minbw:
                break
        self.setMdmChanBW(bw, mhz, radiocfg)

    def calculateFsIF(self, mhz=24, radiocfg=None):
        ''' calculates the optimal IF setting for the current freq/baud
        * totally experimental *
        1.2 kbaud IF: 140khz
        2.4 kbaud IF: 140khz
        38.4kbaud IF: 164khz (140khz for "sensitive" version)
        250 kbaud IF: 281khz
        500 kbaud IF: 328khz
        '''
        pass
    def calculateFsOffset(self, mhz=24, radiocfg=None):
        ''' calculates the optimal FreqOffset setting for the current freq/baud
        * totally experimental *
        '''

        pass

    def getRSSI(self):
        rssi = self.peek(RSSI)
        return rssi

    def getLQI(self):
        lqi = self.peek(LQI)
        return lqi

       
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

    def setAmpMode(self, ampmode=0):
        '''
        set the amplifier mode (RF amp external to CC1111)
        '''
        return self.send(APP_NIC, NIC_SET_AMP_MODE, "%c"%ampmode)
    def getAmpMode(self):
        '''
        get the amplifier mode (RF amp external to CC1111)
        '''
        return self.send(APP_NIC, NIC_GET_AMP_MODE, "")

    def setPktAddr(self, addr):
        return self.poke(ADDR, chr(addr))

    def getPktAddr(self):
        return self.peek(ADDR)

    def setEnDeCoder(self, endec=None):
        self.endec = endec

    ##### RADIO XMIT/RECV and UTILITY FUNCTIONS #####
    # set repeat & offset to optionally repeat tx of a section of the data block. repeat of 65535 means 'forever'
    def RFxmit(self, data, repeat=0, offset=0):
        # encode, if necessary
        if self.endec is not None:
            data = self.endec.encode(data)

        if len(data) > RF_MAX_TX_BLOCK:
            if repeat or offset:
                return PY_TX_BLOCKSIZE_INCOMPAT
            return self.RFxmitLong(data, doencoding=False)

        # calculate wait time
        waitlen = len(data)
        waitlen += repeat * (len(data) - offset)
        wait = USB_TX_WAIT * ((waitlen / RF_MAX_TX_BLOCK) + 1)
        self.send(APP_NIC, NIC_XMIT, "%s" % struct.pack("<HHH",len(data),repeat,offset)+data, wait=wait)

    def RFxmitLong(self, data, doencoding=True):
        # encode, if necessary
        if self.endec is not None and doencoding:
            data = self.endec.encode(data)

        if len(data) > RF_MAX_TX_LONG:
            return PY_TX_BLOCKSIZE_TOO_LARGE

        datalen = len(data)

        # calculate wait time
        waitlen = len(data)
        wait = USB_TX_WAIT * ((waitlen / RF_MAX_TX_BLOCK) + 1)


        # load chunk buffers
        chunks = []
        for x in range(datalen / RF_MAX_TX_CHUNK):
            chunks.append(data[x * RF_MAX_TX_CHUNK:(x + 1) * RF_MAX_TX_CHUNK])
        if datalen % RF_MAX_TX_CHUNK:
            chunks.append(data[-(datalen % RF_MAX_TX_CHUNK):])

        preload = RF_MAX_TX_BLOCK / RF_MAX_TX_CHUNK
        retval, ts = self.send(APP_NIC, NIC_XMIT_LONG, "%s" % struct.pack("<HB",datalen,preload)+data[:RF_MAX_TX_CHUNK * preload], wait=wait*preload)
        #sys.stderr.write('=' + repr(retval))
        error = struct.unpack("<B", retval[0])[0]
        if error:
            return error

        chlen = len(chunks)
        for chidx in range(preload, chlen):
            chunk = chunks[chidx]
            error = RC_TEMP_ERR_BUFFER_NOT_AVAILABLE
            while error == RC_TEMP_ERR_BUFFER_NOT_AVAILABLE:
                retval,ts = self.send(APP_NIC, NIC_XMIT_LONG_MORE, "%s" % struct.pack("B", len(chunk))+chunk, wait=wait)
                error = struct.unpack("<B", retval[0])[0]
            if error:
                return error
                #if error == RC_TEMP_ERR_BUFFER_NOT_AVAILABLE:
                #    sys.stderr.write('.')
            #sys.stderr.write('+')
        # tell dongle we've finished
        retval,ts = self.send(APP_NIC, NIC_XMIT_LONG_MORE, "%s" % struct.pack("B", 0), wait=wait)
        return struct.unpack("<b", retval[0])[0]

    def RFtestLong(self, data="BLAHabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZblahaBcDeFgHiJkLmNoPqRsTuVwXyZBLahAbCdEfGhIjKlMnOpQrStUvWxYz"):
        datalen = len(data)

        chunks = []
        while len(data):
            chunks.append(data[:RF_MAX_TX_CHUNK])
            data = data[RF_MAX_TX_CHUNK:]

        retval, ts = self.send(APP_NIC, NIC_XMIT_LONG, "%s" % struct.pack("<H",datalen)+chunks[0], wait=1000)
        sys.stderr.write('=' + repr(retval))


    # set blocksize to larger than 255 to receive large blocks or 0 to revert to normal
    def RFrecv(self, timeout=USB_RX_WAIT, blocksize=None):
        if not blocksize == None:
            if blocksize > EP5OUT_BUFFER_SIZE: 
                raise(Exception("Blocksize too large. Maximum %d") % EP5OUT_BUFFER_SIZE)
            self.send(APP_NIC, NIC_SET_RECV_LARGE, "%s" % struct.pack("<H",blocksize))
        data = self.recv(APP_NIC, NIC_RECV, timeout)
        # decode, if necessary
        if self.endec is not None:
            # strip off timestamp, process data, then reapply timestamp to continue
            msg, ts = data
            msg = self.endec.decode(msg)
            data = msg, ts

        return data

    def RFlisten(self):
        ''' just sit and dump packets as they come in
        kinda like discover() but without changing any of the communications settings '''
        print "Entering RFlisten mode...  packets arriving will be displayed on the screen"
        print "(press Enter to stop)"
        while not keystop():

            try:
                y, t = self.RFrecv()
                print "(%5.3f) Received:  %s  | %s" % (t, y.encode('hex'), makeFriendlyAscii(y))

            except ChipconUsbTimeoutException:
                pass
            except KeyboardInterrupt:
                print "Please press <enter> to stop"

        sys.stdin.read(1)

    def RFcapture(self):
        ''' dump packets as they come in, but return a list of packets when you exit capture mode.
        kinda like discover() but without changing any of the communications settings '''
        capture = []
        print "Entering RFlisten mode...  packets arriving will be displayed on the screen (and returned in a list)"
        print "(press Enter to stop)"
        while not keystop():

            try:
                y, t = self.RFrecv()
                #print "(%5.3f) Received:  %s" % (t, y.encode('hex'))
                print "(%5.3f) Received:  %s  | %s" % (t, y.encode('hex'), makeFriendlyAscii(y))
                capture.append((y,t))

            except ChipconUsbTimeoutException:
                pass
            except KeyboardInterrupt:
                print "Please press <enter> to stop"

        sys.stdin.read(1)
        return capture

    def discover(self, lowball=1, debug=None, length=30, IdentSyncWord=False, ISWsensitivity=4, ISWminpreamble=2, SyncWordMatchList=None, Search=None, RegExpSearch=None):
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

        if IdentSyncWord == True (or SyncWordMatchList != None), returns a dict of unique possible SyncWords identified along with the number of times seen.
        '''
        retval = {}
        oldebug = self._debug
        
        if SyncWordMatchList != None:
            IdentSyncWord = True

        if IdentSyncWord:
            if lowball <= 1:
                print "Entering Discover mode and searching for possible SyncWords..."
                if SyncWordMatchList != None:
                    print "  seeking one of: %s" % repr([hex(x) for x in SyncWordMatchList])

            else:
                print "-- lowball too high -- ignoring request to IdentSyncWord"
                print "Entering Discover mode..."
                IdentSyncWord = False

        self.lowball(level=lowball, length=length)
        if debug is not None:
            self._debug = debug

        if Search is not None:
            print "Search:",repr(Search)

        if RegExpSearch is not None:
            print "RegExpSearch:",repr(RegExpSearch)

        print "(press Enter to quit)"
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
                    #if lowball == 1:
                    #    y = '\xaa\xaa' + y

                    poss = bits.findSyncWord(y, ISWsensitivity, ISWminpreamble)
                    if len(poss):
                        print "  possible Sync Dwords: %s" % repr([hex(x) for x in poss])
                        for dw in poss:
                            lst = retval.get(dw, 0)
                            lst += 1
                            retval[dw] = lst

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

        if len(retval) == 0:
            return

        printSyncWords(retval)
        return retval


    def lowball(self, level=1, sync=0xaaaa, length=250, pqt=0, crc=False, fec=False, datawhite=False):
        '''
        this configures the radio to the lowest possible level of filtering, potentially allowing complete radio noise to come through as data.  very useful in some circumstances.
        level == 0 changes the Sync Mode to SYNCM_NONE (wayyy more garbage)
        level == 1 (default) sets the Sync Mode to SYNCM_CARRIER (requires a valid carrier detection for the data to be considered a packet)
        level == 2 sets the Sync Mode to SYNCM_CARRIER_15_of_16 (requires a valid carrier detection and 15 of 16 bits of SYNC WORD match for the data to be considered a packet)
        level == 3 sets the Sync Mode to SYNCM_CARRIER_16_of_16 (requires a valid carrier detection and 16 of 16 bits of SYNC WORD match for the data to be considered a packet)
        '''
        if hasattr(self, '_last_radiocfg') and len(self._last_radiocfg):
            print('not saving radio state.  already have one saved.  use lowballRestore() to restore the saved config and the next time you run lowball() the radio config will be saved.')
        else:
            self._last_radiocfg = self.getRadioConfig()

        self.makePktFLEN(length)
        self.setEnablePktCRC(crc)
        self.setEnableMdmFEC(fec)
        self.setEnablePktDataWhitening(datawhite)
        self.setMdmSyncWord(sync)
        self.setPktPQT(pqt)
        
        if (level == 3):
            self.setMdmSyncMode(SYNCM_CARRIER_16_of_16)
        elif (level == 2):
            self.setMdmSyncMode(SYNCM_15_of_16)
        elif (level == 1):
            self.setMdmSyncMode(SYNCM_CARRIER)
        else:
            self.setMdmSyncMode(SYNCM_NONE)


    def lowballRestore(self):
        if not hasattr(self, '_last_radiocfg'):
            raise(Exception("lowballRestore requires that lowball have been executed first (it saves radio config state!)"))
        self.setRadioConfig(self._last_radiocfg)
        self._last_radiocfg = ''

    ##### REPR FUNCTIONS #####
    def printRadioConfig(self, mhz=24, radiocfg=None):
        print self.reprRadioConfig(mhz, radiocfg)

    def reprRadioConfig(self, mhz=24, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        output = []

        output.append( "== Hardware ==")
        output.append( self.reprHardwareConfig())
        output.append( "\n== Software ==")
        output.append( self.reprSoftwareConfig())
        output.append( "\n== Frequency Configuration ==")
        output.append( self.reprFreqConfig(mhz, radiocfg))
        output.append( "\n== Modem Configuration ==")
        output.append( self.reprModemConfig(mhz, radiocfg))
        output.append( "\n== Packet Configuration ==")
        output.append( self.reprPacketConfig(radiocfg))
        output.append( "\n== AES Crypto Configuration ==")
        output.append( self.reprAESMode())
        output.append( "\n== Radio Test Signal Configuration ==")
        output.append( self.reprRadioTestSignalConfig(radiocfg))
        output.append( "\n== Radio State ==")
        output.append( self.reprRadioState(radiocfg))
        output.append("\n== Client State ==")
        output.append( self.reprClientState())
        return "\n".join(output)

    def reprMdmModulation(self, radiocfg=None):
        mod = self.getMdmModulation(radiocfg)
        return ("Modulation:          %s" % MODULATIONS[mod])

    def reprRadioTestSignalConfig(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        output = []
        #output.append("GDO2_INV:            %s" % ("do not Invert Output", "Invert output")[(radiocfg.iocfg2>>6)&1])
        #output.append("GDO2CFG:             0x%x" % (radiocfg.iocfg2&0x3f))
        #output.append("GDO_DS:              %s" % (("minimum drive (>2.6vdd","Maximum drive (<2.6vdd)")[radiocfg.iocfg1>>7]))
        #output.append("GDO1_INV:            %s" % ("do not Invert Output", "Invert output")[(radiocfg.iocfg1>>6)&1])
        #output.append("GDO1CFG:             0x%x"%(radiocfg.iocfg1&0x3f))
        #output.append("GDO0_INV:            %s" % ("do not Invert Output", "Invert output")[(radiocfg.iocfg0>>6)&1])
        #output.append("GDO0CFG:             0x%x"%(radiocfg.iocfg0&0x3f))
        output.append("TEST2:               0x%x"%radiocfg.test2)
        output.append("TEST1:               0x%x"%radiocfg.test1)
        output.append("TEST0:               0x%x"%(radiocfg.test0&0xfd))
        output.append("VCO_SEL_CAL_EN:      0x%x"%((radiocfg.test2>>1)&1))
        return "\n".join(output)


    def reprFreqConfig(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        output = []
        freq,num = self.getFreq(mhz, radiocfg)
        output.append("Frequency:           %f hz (%s)" % (freq,num))

        output.append("Channel:             %d" % radiocfg.channr)


        freq_if = self.getFsIF(mhz, radiocfg)
        freqoff = self.getFsOffset(mhz, radiocfg)
        freqest = self.getFreqEst(radiocfg)
        
        output.append("Intermediate freq:   %d hz" % freq_if)
        output.append("Frequency Offset:    %d +/-" % freqoff)
        output.append("Est. Freq Offset:    %d" % freqest)

        return "\n".join(output)

    def reprAESMode(self):
        output = []
        aesmode= ord(self.getAESmode()[0])

        output.append("AES Mode:            %s" % AESMODES[(aesmode & AES_CRYPTO_MODE)])
        if aesmode & AES_CRYPTO_IN_ENABLE:
            output.append("Crypt RF Input:      %s" % ("Decrypt", "Encrypt")[(aesmode & AES_CRYPTO_IN_TYPE)])
        else:
            output.append("Crypt RF Input:      off")
        if aesmode & AES_CRYPTO_OUT_ENABLE:
            output.append("Crypt RF Output:     %s" % ("Decrypt", "Encrypt")[(aesmode & AES_CRYPTO_OUT_TYPE) >> 2])
        else:
            output.append("Crypt RF Output:     off")

        return "\n".join(output)

    def reprPacketConfig(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        output = []
        output.append("Sync Word:           0x%.2X%.2X" % (radiocfg.sync1, radiocfg.sync0))
        output.append("Packet Length:       %d" % radiocfg.pktlen)
        length_config = radiocfg.pktctrl0&3
        output.append("Length Config:       %s" % LENGTH_CONFIGS[length_config])

        output.append("Configured Address:  0x%x" % radiocfg.addr)

        pqt = self.getPktPQT(radiocfg)
        output.append("Preamble Quality Threshold: 4 * %d" % pqt)

        append = (radiocfg.pktctrl1>>2) & 1
        output.append("Append Status:       %s" % ("No","Yes")[append])

        adr_chk = radiocfg.pktctrl1&3
        output.append("Rcvd Packet Check:   %s" % ADR_CHK_TYPES[adr_chk])

        whitedata = self.getEnablePktDataWhitening(radiocfg)
        output.append("Data Whitening:      %s" % ("off", "ON (but only with cc2400_en==0)")[whitedata])

        pkt_format = (radiocfg.pktctrl0>>5)&3
        output.append("Packet Format:       %s" % PKT_FORMATS[pkt_format])

        crc = self.getEnablePktCRC(radiocfg)
        output.append("CRC:                 %s" % ("disabled", "ENABLED")[crc])

        return "\n".join(output)

    def printRadioState(self, radiocfg=None):
        print self.reprRadioState(radiocfg)

    def reprRadioState(self, radiocfg=None):
        output = []
        try:
            if radiocfg==None:
                self.getRadioConfig()
                radiocfg = self.radiocfg

            output.append("     MARCSTATE:      %s (%x)" % (self.getMARCSTATE(radiocfg)))
            output.append("     DONGLE RESPONDING:  mode :%x, last error# %d"%(self.getDebugCodes()))
        except:
            output.append(repr(sys.exc_info()))
            output.append("     DONGLE *not* RESPONDING")

        return "\n".join(output)

    def reprModemConfig(self, mhz=24, radiocfg=None):
        output = []
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        reprMdmModulation = self.reprMdmModulation(radiocfg)
        syncmode = self.getMdmSyncMode(radiocfg)

        output.append(reprMdmModulation)

        drate = self.getMdmDRate(mhz, radiocfg)
        output.append("DRate:               %f hz"%drate)

        bw = self.getMdmChanBW(mhz, radiocfg)
        output.append("ChanBW:              %f hz"%bw)

        output.append("DEVIATION:           %f hz" % self.getMdmDeviatn(mhz, radiocfg))

        output.append("Sync Mode:           %s" % SYNCMODES[syncmode])

        num_preamble = (radiocfg.mdmcfg1>>4)&7
        output.append("Min TX Preamble:     %d bytes" % (NUM_PREAMBLE[num_preamble]) )

        chanspc = self.getMdmChanSpc(mhz, radiocfg)
        output.append("Chan Spacing:        %f hz" % chanspc)

        bslimit = radiocfg.bscfg & BSCFG_BS_LIMIT
        output.append("BSLimit:             %s"%BSLIMITS[bslimit])

        output.append("DC Filter:           %s" % (("enabled", "disabled")[self.getEnableMdmDCFilter(radiocfg)]))

        mchstr = self.getEnableMdmManchester(radiocfg)
        output.append("Manchester Encoding: %s" %  (("disabled","enabled")[mchstr]))

        fec = self.getEnableMdmFEC(radiocfg)
        output.append("Fwd Err Correct:     %s" % (("disabled","enabled")[fec]))
        

        return "\n".join(output)

   
    def checkRepr(self, matchstr, checkval, maxdiff=0):
        starry = self.reprRadioConfig().split('\n')
        line,val = getValueFromReprString(starry, matchstr)
        try:
            f = checkval.__class__(val.split(" ")[0])
            if abs(f-checkval) <= maxdiff:
                print "  passed: reprRadioConfig test: %s %s" % (repr(val), checkval)
            else:
                print " *FAILED* reprRadioConfig test: %s %s %s" % (repr(line), repr(val), checkval)

        except ValueError, e:
            print "  ERROR checking repr: %s" % e

    def testTX(self, data="XYZABCDEFGHIJKL"):
        while (sys.stdin not in select.select([sys.stdin],[],[],0)[0]):
            time.sleep(.4)
            print "transmitting %s" % repr(data)
            self.RFxmit(data)
        sys.stdin.read(1)

    ######## APPLICATION METHODS - more for demonstration than anything ########
    def setup24330MHz(self):
        #self.setRadioConfig('0c4eff000800000b0065600068b583231145073f14166c4340915610a90a0011593f3f8831090000000000000000c02e0006000000000000000000000000'.decode('hex'))
        self.getRadioConfig()
        rc = self.radiocfg
        rc.iocfg0     = 0x06
        rc.sync1      = 0x0c
        rc.sync0      = 0x4e
        rc.pktlen     = 0xff
        rc.pktctrl1   = 0x00
        rc.pktctrl0   = 0x08
        rc.fsctrl1    = 0x0b
        rc.fsctrl0    = 0x00
        rc.addr       = 0x00
        rc.channr     = 0x00
        rc.mdmcfg4    = 0x68
        rc.mdmcfg3    = 0xb5
        rc.mdmcfg2    = 0x83
        rc.mdmcfg1    = 0x23
        rc.mdmcfg0    = 0x11
        rc.mcsm2      = 0x07
        rc.mcsm1      = 0x3f
        rc.mcsm0      = 0x14
        rc.deviatn    = 0x45
        rc.foccfg     = 0x16
        rc.bscfg      = 0x6c
        #rc.agcctrl2  |= AGCCTRL2_MAX_DVGA_GAIN
        rc.agcctrl2   = 0x43
        rc.agcctrl1   = 0x40
        rc.agcctrl0   = 0x91
        rc.frend1     = 0x56
        rc.frend0     = 0x10
        rc.fscal3     = 0xad
        rc.fscal2     = 0x0A
        rc.fscal1     = 0x00
        rc.fscal0     = 0x11
        rc.test2      = 0x88
        rc.test1      = 0x31
        rc.test0      = 0x09
        rc.pa_table0  = 0xc0
        self.setRadioConfig()

    def setup900MHz(self):
        self.getRadioConfig()
        rc = self.radiocfg
        rc.iocfg0     = 0x06
        rc.sync1      = 0x0b
        rc.sync0      = 0x0b
        rc.pktlen     = 0xff
        rc.pktctrl1   = 0xe5
        rc.pktctrl0   = 0x04
        rc.fsctrl1    = 0x12
        rc.fsctrl0    = 0x00
        rc.addr       = 0x00
        rc.channr     = 0x00
        rc.mdmcfg4    = 0x3e
        rc.mdmcfg3    = 0x55
        rc.mdmcfg2    = 0x73
        rc.mdmcfg1    = 0x23
        rc.mdmcfg0    = 0x55
        rc.mcsm2      = 0x07
        rc.mcsm1      = 0x30
        rc.mcsm0      = 0x00
        rc.deviatn    = 0x16
        rc.foccfg     = 0x17
        rc.bscfg      = 0x6c
        rc.agcctrl2  |= AGCCTRL2_MAX_DVGA_GAIN
        rc.agcctrl2   = 0x03
        rc.agcctrl1   = 0x40
        rc.agcctrl0   = 0x91
        rc.frend1     = 0x56
        rc.frend0     = 0x10
        rc.fscal3     = 0xEA
        rc.fscal2     = 0x2A
        rc.fscal1     = 0x00
        rc.fscal0     = 0x1F
        rc.test2      = 0x88
        rc.test1      = 0x31
        rc.test0      = 0x09
        rc.pa_table0  = 0xc0
        self.setRadioConfig()

    def setup900MHzHopTrans(self):
        self.getRadioConfig()
        rc = self.radiocfg
        rc.iocfg0     = 0x06
        rc.sync1      = 0x0b
        rc.sync0      = 0x0b
        rc.pktlen     = 0xff
        rc.pktctrl1   = 0x04
        rc.pktctrl0   = 0x05
        rc.addr       = 0x00
        rc.channr     = 0x00
        rc.fsctrl1    = 0x06
        rc.fsctrl0    = 0x00
        rc.mdmcfg4    = 0xee
        rc.mdmcfg3    = 0x55
        rc.mdmcfg2    = 0x73
        rc.mdmcfg1    = 0x23
        rc.mdmcfg0    = 0x55
        rc.mcsm2      = 0x07
        rc.mcsm1      = 0x30
        rc.mcsm0      = 0x18
        rc.deviatn    = 0x16
        rc.foccfg     = 0x17
        rc.bscfg      = 0x6c
        rc.agcctrl2   = 0x03
        rc.agcctrl1   = 0x40
        rc.agcctrl0   = 0x91
        rc.frend1     = 0x56
        rc.frend0     = 0x10
        rc.fscal3     = 0xEA
        rc.fscal2     = 0x2A
        rc.fscal1     = 0x00
        rc.fscal0     = 0x1F
        rc.test2      = 0x88
        rc.test1      = 0x31
        rc.test0      = 0x09
        rc.pa_table0  = 0xc0
        self.setRadioConfig()

    def setup900MHzContTrans(self):
        self.getRadioConfig()
        rc = self.radiocfg
        rc.iocfg0     = 0x06
        rc.sync1      = 0x0b
        rc.sync0      = 0x0b
        rc.pktlen     = 0xff
        rc.pktctrl1   = 0x04
        rc.pktctrl0   = 0x05
        rc.addr       = 0x00
        rc.channr     = 0x00
        rc.fsctrl1    = 0x06
        rc.fsctrl0    = 0x00
        rc.freq2      = 0x26
        rc.freq1      = 0x55
        rc.freq0      = 0x55
        rc.mdmcfg4    = 0xee
        rc.mdmcfg3    = 0x55
        rc.mdmcfg2    = 0x73
        rc.mdmcfg1    = 0x23
        rc.mdmcfg0    = 0x55
        rc.mcsm2      = 0x07
        rc.mcsm1      = 0x30
        rc.mcsm0      = 0x18
        rc.deviatn    = 0x16
        rc.foccfg     = 0x17
        rc.bscfg      = 0x6c
        rc.agcctrl2   = 0x03
        rc.agcctrl1   = 0x40
        rc.agcctrl0   = 0x91
        rc.frend1     = 0x56
        rc.frend0     = 0x10
        rc.fscal3     = 0xEA
        rc.fscal2     = 0x2A
        rc.fscal1     = 0x00
        rc.fscal0     = 0x1F
        rc.test2      = 0x88
        rc.test1      = 0x31
        rc.test0      = 0x09
        rc.pa_table0  = 0xc0
        self.setRadioConfig()

    def setup_rfstudio_902PktTx(self):
        self.getRadioConfig()
        rc = self.radiocfg
        rc.iocfg2     = 0x00
        rc.iocfg1     = 0x00
        rc.iocfg0     = 0x06
        rc.sync1      = 0x0b
        rc.sync0      = 0x0b
        rc.pktlen     = 0xff
        rc.pktctrl1   = 0x04
        rc.pktctrl0   = 0x05
        rc.addr       = 0x00
        rc.channr     = 0x00
        rc.fsctrl1    = 0x0c
        rc.fsctrl0    = 0x00
        rc.freq2      = 0x25
        rc.freq1      = 0x95
        rc.freq0      = 0x55
        rc.mdmcfg4    = 0x1d
        rc.mdmcfg3    = 0x55
        rc.mdmcfg2    = 0x13
        rc.mdmcfg1    = 0x23
        rc.mdmcfg0    = 0x11
        rc.mcsm2      = 0x07
        rc.mcsm1      = 0x30
        rc.mcsm0      = 0x18
        rc.deviatn    = 0x63
        rc.foccfg     = 0x1d
        rc.bscfg      = 0x1c
        rc.agcctrl2   = 0xc7
        rc.agcctrl1   = 0x00
        rc.agcctrl0   = 0xb0
        rc.frend1     = 0xb6
        rc.frend0     = 0x10
        rc.fscal3     = 0xEA
        rc.fscal2     = 0x2A
        rc.fscal1     = 0x00
        rc.fscal0     = 0x1F
        rc.test2      = 0x88
        rc.test1      = 0x31
        rc.test0      = 0x09
        rc.pa_table7  = 0x00
        rc.pa_table6  = 0x00
        rc.pa_table5  = 0x00
        rc.pa_table4  = 0x00
        rc.pa_table3  = 0x00
        rc.pa_table2  = 0x00
        rc.pa_table1  = 0x00
        #rc.pa_table0  = 0x8e
        rc.pa_table0  = 0xc0
        self.setRadioConfig()

class FHSSNIC(NICxx11):
    '''
    advanced NIC implementation for CCxx11 chips, including Frequency Hopping
    '''
    def FHSSxmit(self, data):
        return self.send(APP_NIC, FHSS_XMIT, "%c%s" % (len(data), data))

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

    def setMACperiod(self, dwell_ms, mhz=24):
        macdata = self.getMACdata()
        cycles_per_channel = macdata[1]
        ticks_per_cycle = 256
        tick_ms = dwell_ms / (ticks_per_cycle * cycles_per_channel)
        val = calculateT2(tick_ms, mhz)
        T, tickidx, tipidx, PR = val
        print "Setting MAC period to %f secs (%x %x %x)" % (val)
        t2ctl = (ord(self.peek(X_T2CTL)) & 0xfc)   | (tipidx)
        clkcon = (ord(self.peek(X_CLKCON)) & 0xc7) | (tickidx<<3)
        
        self.poke(X_T2PR, chr(PR))
        self.poke(X_T2CTL, chr(t2ctl))
        self.poke(X_CLKCON, chr(clkcon))

    def _setMACmode(self, _mode):
        '''
        internal debugging use only
        '''
        macdata = self.getMACdata()
        print repr(macdata)
        macdata = (_mode,) +  macdata[1:]
        print repr(macdata)
        self.setMACdata(macdata)

    def setMACdata(self, data):
        datastr = struct.pack("<BHHHHHHHHBBH", *data)
        return self.send(APP_NIC, FHSS_SET_MAC_DATA, datastr)

    def getMACdata(self):
        datastr, timestamp = self.send(APP_NIC, FHSS_GET_MAC_DATA, '')
        #print (repr(datastr))
        data = struct.unpack("<BHHHHHHHHBBH", datastr)
        return data

    def reprMACdata(self):
        data = self.getMACdata()
        return """\
u8 mac_state                %x
u16 MAC_threshold           %x
u16 MAC_ovcount             %x
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
                
def unittest(dongle):
    import chipcon_usb
    chipcon_usb.unittest(dongle)

    print "\nTesting getValueFromReprString()"
    starry = dongle.reprRadioConfig().split('\n')
    print repr(getValueFromReprString(starry, 'hz'))

    print "\nTesting reprRadioConfig()"
    print dongle.reprRadioConfig()

    print "\nTesting Frequency Get/Setters"
    # FREQ
    freq0,freq0str = dongle.getFreq()

    testfreq = 902000000
    dongle.setFreq(testfreq)
    freq,freqstr = dongle.getFreq()
    if abs(testfreq - freq) < 1024:
        print "  passed: %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)
    else:
        print " *FAILED* %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)

    testfreq = 868000000
    dongle.setFreq(testfreq)
    freq,freqstr = dongle.getFreq()
    if abs(testfreq - freq) < 1024:
        print "  passed: %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)
    else:
        print " *FAILED* %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)

    testfreq = 433000000
    dongle.setFreq(testfreq)
    freq,freqstr = dongle.getFreq()
    if abs(testfreq - freq) < 1024:
        print "  passed: %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)
    else:
        print " *FAILED* %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)
   
    dongle.checkRepr("Frequency:", float(testfreq), 1024)
    dongle.setFreq(freq0)

    # CHANNR
    channr0 = dongle.getChannel()
    for x in range(15):
        dongle.setChannel(x)
        channr = dongle.getChannel()
        if channr != x:
            print " *FAILED* get/setChannel():  %d : %d" % (x, channr)
        else:
            print "  passed: get/setChannel():  %d : %d" % (x, channr)
    dongle.checkRepr("Channel:", channr)
    dongle.setChannel(channr0)

    # IF and FREQ_OFF
    freq_if = dongle.getFsIF()
    freqoff = dongle.getFsOffset()
    for fif, foff in ((164062,1),(140625,2),(187500,3)):
        dongle.setFsIF(fif)
        dongle.setFsOffset(foff)
        nfif  = dongle.getFsIF()
        nfoff = dongle.getFsOffset()
        if abs(nfif - fif) > 5:
            print " *FAILED* get/setFsIFandOffset():  %d : %f (diff: %f)" % (fif,nfif,nfif-fif)
        else:
            print "  passed: get/setFsIFandOffset():  %d : %f (diff: %f)" % (fif,nfif,nfif-fif)

        if foff != nfoff:
            print " *FAILED* get/setFsIFandOffset():  %d : %d (diff: %d)" % (foff,nfoff,nfoff-foff)
        else:
            print "  passed: get/setFsIFandOffset():  %d : %d (diff: %d)" % (foff,nfoff,nfoff-foff)
    dongle.checkRepr("Intermediate freq:", fif, 11720)
    dongle.checkRepr("Frequency Offset:", foff)
    
    dongle.setFsIF(freq_if)
    dongle.setFsOffset(freqoff)

    ### continuing with more simple tests.  add completeness later?
    # Modem tests

    mod = dongle.getMdmModulation(dongle.radiocfg)
    dongle.setMdmModulation(mod, dongle.radiocfg)
    modcheck = dongle.getMdmModulation(dongle.radiocfg)
    if mod != modcheck:
        print " *FAILED* get/setMdmModulation():  %d : %d " % (mod, modcheck)
    else:
        print "  passed: get/setMdmModulation():  %d : %d " % (mod, modcheck)

    chanspc = dongle.getMdmChanSpc(dongle.mhz, dongle.radiocfg)
    dongle.setMdmChanSpc(chanspc, dongle.mhz, dongle.radiocfg)
    chanspc_check = dongle.getMdmChanSpc(dongle.mhz, dongle.radiocfg)
    if chanspc != chanspc_check:
        print " *FAILED* get/setMdmChanSpc():  %d : %d" % (chanspc, chanspc_check)
    else:
        print "  passed: get/setMdmChanSpc():  %d : %d" % (chanspc, chanspc_check)

    chanbw = dongle.getMdmChanBW(dongle.mhz, dongle.radiocfg)
    dongle.setMdmChanBW(chanbw, dongle.mhz, dongle.radiocfg)
    chanbw_check = dongle.getMdmChanBW(dongle.mhz, dongle.radiocfg)
    if chanbw != chanbw_check:
        print " *FAILED* get/setMdmChanBW():  %d : %d" % (chanbw, chanbw_check)
    else:
        print "  passed: get/setMdmChanBW():  %d : %d" % (chanbw, chanbw_check)

    drate = dongle.getMdmDRate(dongle.mhz, dongle.radiocfg)
    dongle.setMdmDRate(drate, dongle.mhz, dongle.radiocfg)
    drate_check = dongle.getMdmDRate(dongle.mhz, dongle.radiocfg)
    if drate != drate_check:
        print " *FAILED* get/setMdmDRate():  %d : %d" % (drate, drate_check)
    else:
        print "  passed: get/setMdmDRate():  %d : %d" % (drate, drate_check)

    deviatn = dongle.getMdmDeviatn(dongle.mhz, dongle.radiocfg)
    dongle.setMdmDeviatn(deviatn, dongle.mhz, dongle.radiocfg)
    deviatn_check = dongle.getMdmDeviatn(dongle.mhz, dongle.radiocfg)
    if deviatn != deviatn_check:
        print " *FAILED* get/setMdmdeviatn():  %d : %d" % (deviatn, deviatn_check)
    else:
        print "  passed: get/setMdmdeviatn():  %d : %d" % (deviatn, deviatn_check)

    syncm = dongle.getMdmSyncMode(dongle.radiocfg)
    dongle.setMdmSyncMode(syncm, dongle.radiocfg)
    syncm_check = dongle.getMdmSyncMode(dongle.radiocfg)
    if syncm != syncm_check:
        print " *FAILED* get/setMdmSyncMode():  %d : %d" % (syncm, syncm_check)
    else:
        print "  passed: get/setMdmSyncMode():  %d : %d" % (syncm, syncm_check)

    mchstr = dongle.getEnableMdmManchester(dongle.radiocfg)
    dongle.setEnableMdmManchester(mchstr, dongle.radiocfg)
    mchstr_check = dongle.getEnableMdmManchester(dongle.radiocfg)
    if mchstr != mchstr_check:
        print " *FAILED* get/setMdmManchester():  %d : %d" % (mchstr, mchstr_check)
    else:
        print "  passed: get/setMdmManchester():  %d : %d" % (mchstr, mchstr_check)

    fec = dongle.getEnableMdmFEC(dongle.radiocfg)
    dongle.setEnableMdmFEC(fec, dongle.radiocfg)
    fec_check = dongle.getEnableMdmFEC(dongle.radiocfg)
    if fec != fec_check:
        print " *FAILED* get/setEnableMdmFEC():  %d : %d" % (fec, fec_check)
    else:
        print "  passed: get/setEnableMdmFEC():  %d : %d" % (fec, fec_check)

    dcf = dongle.getEnableMdmDCFilter(dongle.radiocfg)
    dongle.setEnableMdmDCFilter(dcf, dongle.radiocfg)
    dcf_check = dongle.getEnableMdmDCFilter(dongle.radiocfg)
    if dcf != dcf_check:
        print " *FAILED* get/setEnableMdmDCFilter():  %d : %d" % (dcf, dcf_check)
    else:
        print "  passed: get/setEnableMdmDCFilter():  %d : %d" % (dcf, dcf_check)


    # Pkt tests
    pqt = dongle.getPktPQT(dongle.radiocfg)
    dongle.setPktPQT(pqt, dongle.radiocfg)
    pqt_check = dongle.getPktPQT(dongle.radiocfg)
    if pqt != pqt_check:
        print " *FAILED* get/setEnableMdmFEC():  %d : %d" % (pqt, pqt_check)
    else:
        print "  passed: get/setEnableMdmFEC():  %d : %d" % (pqt, pqt_check)

    # FHSS tests
    print "\nTesting FHSS State set/get"
    fhssstate = dongle.getFHSSstate()
    print repr(fhssstate)
    for stateidx in range(FHSS_LAST_STATE+1):
        print repr(dongle.setFHSSstate(stateidx))
        print repr(dongle.getFHSSstate())

    print repr(dongle.setFHSSstate(fhssstate[1] ))
    print repr(dongle.getFHSSstate())

def getValueFromReprString(stringarray, line_text):
    for string in stringarray:
        if line_text in string:
            idx = string.find(":")
            val = string[idx+1:].strip()
            return (string,val)

def mkFreq(freq=902000000, mhz=24):
    freqmult = (0x10000 / 1000000.0) / mhz
    num = int(freq * freqmult)
    freq2 = num >> 16
    freq1 = (num>>8) & 0xff
    freq0 = num & 0xff
    return (num, freq2,freq1,freq0)



if __name__ == "__main__":
    idx = 0
    if len(sys.argv) > 1:
        idx = int(sys.argv.pop())
    d = FHSSNIC(idx=idx, debug=False)
    unittest(d)
