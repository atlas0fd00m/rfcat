from .rflib_defs import *
from .chipcondefs import *
from .rflib_version import *

#### supporting chipcon_usb.py
DEFAULT_USB_TIMEOUT = 1000

EP_TIMEOUT_IDLE     = 400
EP_TIMEOUT_ACTIVE   = 10

USB_MAX_BLOCK_SIZE  = 512
USB_RX_WAIT         = 1000
USB_TX_WAIT         = 10000

USB_BM_REQTYPE_TGTMASK          =0x1f
USB_BM_REQTYPE_TGT_DEV          =0x00
USB_BM_REQTYPE_TGT_INTF         =0x01
USB_BM_REQTYPE_TGT_EP           =0x02

USB_BM_REQTYPE_TYPEMASK         =0x60
USB_BM_REQTYPE_TYPE_STD         =0x00
USB_BM_REQTYPE_TYPE_CLASS       =0x20
USB_BM_REQTYPE_TYPE_VENDOR      =0x40
USB_BM_REQTYPE_TYPE_RESERVED    =0x60

USB_BM_REQTYPE_DIRMASK          =0x80
USB_BM_REQTYPE_DIR_OUT          =0x00
USB_BM_REQTYPE_DIR_IN           =0x80

USB_GET_STATUS                  =0x00
USB_CLEAR_FEATURE               =0x01
USB_SET_FEATURE                 =0x03
USB_SET_ADDRESS                 =0x05
USB_GET_DESCRIPTOR              =0x06
USB_SET_DESCRIPTOR              =0x07
USB_GET_CONFIGURATION           =0x08
USB_SET_CONFIGURATION           =0x09
USB_GET_INTERFACE               =0x0a
USB_SET_INTERFACE               =0x11
USB_SYNCH_FRAME                 =0x12

APP_GENERIC                     = 0x01
APP_DEBUG                       = 0xfe
APP_SYSTEM                      = 0xff


SYS_CMD_PEEK                    = 0x80
SYS_CMD_POKE                    = 0x81
SYS_CMD_PING                    = 0x82
SYS_CMD_STATUS                  = 0x83
SYS_CMD_POKE_REG                = 0x84
SYS_CMD_GET_CLOCK               = 0x85
SYS_CMD_BUILDTYPE               = 0x86
SYS_CMD_BOOTLOADER              = 0x87
SYS_CMD_RFMODE                  = 0x88
SYS_CMD_COMPILER                = 0x89
SYS_CMD_PARTNUM                 = 0x8e
SYS_CMD_RESET                   = 0x8f
SYS_CMD_CLEAR_CODES             = 0x90
SYS_CMD_DEVICE_SERIAL_NUMBER    = 0x91
SYS_CMD_LED_MODE                = 0x93

EP0_CMD_GET_DEBUG_CODES         = 0x00
EP0_CMD_GET_ADDRESS             = 0x01
EP0_CMD_POKEX                   = 0x01
EP0_CMD_PEEKX                   = 0x02
EP0_CMD_PING0                   = 0x03
EP0_CMD_PING1                   = 0x04
EP0_CMD_RESET                   = 0xfe


DEBUG_CMD_STRING                = 0xf0
DEBUG_CMD_HEX                   = 0xf1
DEBUG_CMD_HEX16                 = 0xf2
DEBUG_CMD_HEX32                 = 0xf3
DEBUG_CMD_INT                   = 0xf4

EP5OUT_MAX_PACKET_SIZE          = 64
EP5IN_MAX_PACKET_SIZE           = 64
# EP5OUT_BUFFER_SIZE must match firmware/include/chipcon_usb.h definition
EP5OUT_BUFFER_SIZE              = 516

LC_USB_INITUSB                = 0x2
LC_MAIN_RFIF                  = 0xd
LC_USB_DATA_RESET_RESUME      = 0xa
LC_USB_RESET                  = 0xb
LC_USB_EP5OUT                 = 0xc
LC_RF_VECTOR                  = 0x10
LC_RFTXRX_VECTOR              = 0x11

LCE_USB_EP5_TX_WHILE_INBUF_WRITTEN    = 0x1
LCE_USB_EP0_SENT_STALL                = 0x4
LCE_USB_EP5_OUT_WHILE_OUTBUF_WRITTEN  = 0x5
LCE_USB_EP5_LEN_TOO_BIG               = 0x6
LCE_USB_EP5_GOT_CRAP                  = 0x7
LCE_USB_EP5_STALL                     = 0x8
LCE_USB_DATA_LEFTOVER_FLAGS           = 0x9
LCE_RF_RXOVF                          = 0x10
LCE_RF_TXUNF                          = 0x11

RCS = {}
LCS = {}
LCES = {}
lcls = locals()
for lcl in list(lcls.keys()):
    if lcl.startswith("LCE_"):
        LCES[lcl] = lcls[lcl]
        LCES[lcls[lcl]] = lcl
    if lcl.startswith("LC_"):
        LCS[lcl] = lcls[lcl]
        LCS[lcls[lcl]] = lcl
    if lcl.startswith("RC_"):
        RCS[lcl] = lcls[lcl]
        RCS[lcls[lcl]] = lcl

CHIPS = {
    0x91: "CC2511",
    0x81: "CC2510",
    0x11: "CC1111",
    0x01: "CC1110",
    0x40: "FakeDongle",
    }


#### supporting chipcon_nic.py
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
NIC_LONG_XMIT =                 0xc
NIC_LONG_XMIT_MORE =            0xd

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
for key,val in list(globals().items()):
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
MOD_4FSK                        = 0x40
MOD_MSK                         = 0x70
MANCHESTER                      = 0x08

MODULATIONS = {
        MOD_2FSK    : "2FSK",
        MOD_GFSK    : "GFSK",
        MOD_4FSK    : "4FSK",   # note: radio doesn't support Manchester encoding in 4FSK
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


# RFST (0xE1) - RF Strobe Commands
RFST_SFSTXON                    = 0x00
RFST_SCAL                       = 0x01
RFST_SRX                        = 0x02
RFST_STX                        = 0x03
RFST_SIDLE                      = 0x04
RFST_SNOP                       = 0x05

# 0xDF3B: MARCSTATE - Main Radio Control State Machine State
MARCSTATE_MARC_STATE            = 0x1F

MARC_STATE_SLEEP                = 0x00
MARC_STATE_IDLE                 = 0x01
MARC_STATE_VCOON_MC             = 0x03
MARC_STATE_REGON_MC             = 0x04
MARC_STATE_MANCAL               = 0x05
MARC_STATE_VCOON                = 0x06
MARC_STATE_REGON                = 0x07
MARC_STATE_STARTCAL             = 0x08
MARC_STATE_BWBOOST              = 0x09
MARC_STATE_FS_LOCK              = 0x0A
MARC_STATE_IFADCON              = 0x0B
MARC_STATE_ENDCAL               = 0x0C
MARC_STATE_RX                   = 0x0D
MARC_STATE_RX_END               = 0x0E
MARC_STATE_RX_RST               = 0x0F
MARC_STATE_TXRX_SWITCH          = 0x10
MARC_STATE_RX_OVERFLOW          = 0x11
MARC_STATE_FSTXON               = 0x12
MARC_STATE_TX                   = 0x13
MARC_STATE_TX_END               = 0x14
MARC_STATE_RXTX_SWITCH          = 0x15
MARC_STATE_TX_UNDERFLOW         = 0x16


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

CHIPmhz = {
    0x91: 24,
    0x81: 26,
    0x11: 24,
    0x01: 26,
}

# FAKE DONGLE settings. mostly used for unittests.
FAKE_PARTNUM = 0x40
FAKE_DEBUG_CODES = (0x41, 0x42)
FAKE_DONGLE_BUILDDATA = b'DONS BROKEN FAKE DONGLE r0001\0'
FAKE_DONGLE_COMPILER = b'ATLASv100'
FAKE_DONGLE_SERIALNUM = b'0x47145'
FAKE_INTERRUPT_REGISTERS = {
        'IEN0': b'\xff',
        'IEN1': b'\x01',
        'IEN2': b'\xe0',
        'TCON': b'\xff',
        'S0CON': b'\x05',
        'IRCON': b'\x02',
        'IRCON2': b'\t',
        'S1CON': b'\x02',
        'RFIF': b'\x04',
        'DMAIE': b'\x01',
        'DMAIF': b'\x01',
        'DMAIRQ': b'\x10'}
# initial radio config
FAKE_MEM_DF00 = b'\x0cN\xff@\x00\x00\x00\x0c\x00%\x95U\xca\xa3\x01#\x116\x07\x0f\x18\x17l\x03@\x91\xb6\x10\xef*+\x1fY??\x881\t\x00\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x00\x11\x03\x12\x80\xaa\r\x90\xfd'
