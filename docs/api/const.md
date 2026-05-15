# const Module

## Overview

The `const` module defines all hardware-specific constants used throughout the RfCat project. It imports definitions from `rflib_defs.py`, `chipcondefs.py`, and `rflib_version.py`, and adds USB and application-level constants.

Think of this as the central header file for the library.

## USB Constants

### USB Request Types

- `USB_BM_REQTYPE_TGTMASK` = 0x1F
- `USB_BM_REQTYPE_TGT_DEV` = 0x00
- `USB_BM_REQTYPE_TGT_INTF` = 0x01
- `USB_BM_REQTYPE_TGT_EP` = 0x02

- `USB_BM_REQTYPE_TYPEMASK` = 0x60
- `USB_BM_REQTYPE_TYPE_STD` = 0x00
- `USB_BM_REQTYPE_TYPE_CLASS` = 0x20
- `USB_BM_REQTYPE_TYPE_VENDOR` = 0x40

- `USB_BM_REQTYPE_DIRMASK` = 0x80
- `USB_BM_REQTYPE_DIR_OUT` = 0x00
- `USB_BM_REQTYPE_DIR_IN` = 0x80

These masks construct the `bmRequestType` field for USB control transfers. `chipcon_usb` uses `USB_BM_REQTYPE_TGT_EP | USB_BM_REQTYPE_TYPE_VENDOR | USB_BM_REQTYPE_DIR_OUT` for sending data, and with `DIR_IN` for receiving.

### Standard USB Requests

- `USB_GET_STATUS` = 0x00
- `USB_CLEAR_FEATURE` = 0x01
- `USB_SET_FEATURE` = 0x03
- `USB_SET_ADDRESS` = 0x05
- `USB_GET_DESCRIPTOR` = 0x06
- `USB_SET_DESCRIPTOR` = 0x07
- `USB_GET_CONFIGURATION` = 0x08
- `USB_SET_CONFIGURATION` = 0x09
- `USB_GET_INTERFACE` = 0x0A
- `USB_SET_INTERFACE` = 0x11
- `USB_SYNCH_FRAME` = 0x12

These are standard USB chapter 9 request codes, though not all are used by RfCat (some are just defined from the USB spec).

### Application IDs

Communication with the dongle uses an application ID byte to route messages to different firmware components:

- `APP_GENERIC` = 0x01
- `APP_DEBUG` = 0xFE
- `APP_SYSTEM` = 0xFF

Also from `chipcondefs.py`:
- `APP_NIC` = 0x42 (radio NIC)
- `APP_SPECAN` = 0x43 (spectrum analyzer)

### System Commands (SYS_CMD_*)

Sent to `APP_SYSTEM` via control endpoint:

- `SYS_CMD_PEEK` = 0x80
- `SYS_CMD_POKE` = 0x81
- `SYS_CMD_PING` = 0x82
- `SYS_CMD_STATUS` = 0x83
- `SYS_CMD_POKE_REG` = 0x84
- `SYS_CMD_GET_CLOCK` = 0x85
- `SYS_CMD_BUILDTYPE` = 0x86
- `SYS_CMD_BOOTLOADER` = 0x87
- `SYS_CMD_RFMODE` = 0x88
- `SYS_CMD_COMPILER` = 0x89
- `SYS_CMD_PARTNUM` = 0x8E
- `SYS_CMD_RESET` = 0x8F
- `SYS_CMD_CLEAR_CODES` = 0x90
- `SYS_CMD_DEVICE_SERIAL_NUMBER` = 0x91
- `SYS_CMD_LED_MODE` = 0x93

These commands are used by `USBDongle` for low-level operations like peeking/poking registers, getting firmware version, and putting the device into bootloader mode.

### EP0 Commands

- `EP0_CMD_GET_DEBUG_CODES` = 0x00
- `EP0_CMD_GET_ADDRESS` = 0x01
- `EP0_CMD_POKEX` = 0x01
- `EP0_CMD_PEEKX` = 0x02
- `EP0_CMD_PING0` = 0x03
- `EP0_CMD_PING1` = 0x04
- `EP0_CMD_RESET` = 0xFE

These are vendor-specific commands on endpoint 0 for alternative access patterns.

### USB Timeouts

- `DEFAULT_USB_TIMEOUT` = 1000  (ms)
- `EP_TIMEOUT_IDLE` = 400
- `EP_TIMEOUT_ACTIVE` = 10

Active transfers have a shorter timeout; idle (e.g., waiting for packet) uses longer timeout.

### USB Packet Sizes

- `USB_MAX_BLOCK_SIZE` = 512  (maximum transfer size)
- `EP5OUT_MAX_PACKET_SIZE` = 64 (USB FS packet size)
- `EP5IN_MAX_PACKET_SIZE` = 64
- `EP5OUT_BUFFER_SIZE` = 516  (firmware buffer size, includes some overhead)

## Radio Control Constants

### Frequency Bands

From `chipcondefs.py` / `const.py`:

- `FREQ_MIN_300` = 281_000_000 Hz
- `FREQ_MAX_300` = 361_000_000 Hz
- `FREQ_MIN_400` = 378_000_000 Hz
- `FREQ_MAX_400` = 481_000_000 Hz
- `FREQ_MIN_900` = 749_000_000 Hz
- `FREQ_MAX_900` = 962_000_000 Hz

These define the valid frequency ranges for the CC1111 radio using different crystal frequencies.

### Frequency Transition Edges

- `FREQ_EDGE_400` = 369_000_000 Hz
- `FREQ_EDGE_900` = 615_000_000 Hz

When setting frequency, the VCO calibration value (`fscal2`) changes at these boundaries.

### VCO Mid Points

- `FREQ_MID_300` = 318_000_000 Hz
- `FRED_MID_400` = 424_000_000 Hz
- `FREQ_MID_900` = 848_000_000 Hz

Used in `setFreq()` to select high or low VCO.

### Chip Types

- `CHIPS` dictionary maps part numbers to strings:
  - 0x91: "CC2511"
  - 0x81: "CC2510"
  - 0x11: "CC1111"
  - 0x01: "CC1110"
  - 0x40: "FakeDongle" (for unit testing)

The part number is read from `PARTNUM` register (0xDF36).

### Modulation Constants

- `MOD_2FSK` = 0x00
- `MOD_GFSK` = 0x10
- `MOD_ASK_OOK` = 0x30
- `MOD_4FSK` = 0x40
- `MOD_MSK` = 0x70
- `MANCHESTER` = 0x08  (can be OR'd with modulation)

These values correspond to the `MDMCFG2.MOD_FORMAT` field.

### Sync Modes

- `SYNCM_NONE` = 0
- `SYNCM_15_of_16` = 1
- `SYNCM_16_of_16` = 2
- `SYNCM_30_of_32` = 3
- `SYNCM_CARRIER` = 4
- `SYNCM_CARRIER_15_of_16` = 5
- `SYNCM_CARRIER_16_of_16` = 6
- `SYNCM_CARRIER_30_of_32` = 7

Specifies how many bits of the sync word must match and whether carrier detection is required. These constants map directly to the hardware `MDMCFG2.SYNC_MODE` bits.

### Packet Length Configs

`LENGTH_CONFIGS` list:
- 0: "Fixed Packet Mode"
- 1: "Variable Packet Mode (len=first byte after sync word)"
- 2,3: reserved

Controlled by `PKTCTRL0.LENGTH_CONFIG`.

### Address Check Types

`ADR_CHK_TYPES`:
- 0: "No address check"
- 1: "Address Check, No Broadcast"
- 2: "Address Check, 0x00 is broadcast"
- 3: "Address Check, 0x00 and 0xff are broadcast"

From `PKTCTRL1.ADR_CHK`.

### Packet Formats

`PKT_FORMATS`:
- 0: "Normal mode"
- 1: reserved
- 2: "Random TX mode"
- 3: reserved

From `PKTCTRL0.PKT_FORMAT`.

### BSC Limits (Data Rate Offset Compensation)

- `BSCFG_BS_LIMIT_0` = 0  (no compensation)
- `BSCFG_BS_LIMIT_3` = 1  (+/- 3.125%)
- `BSCFG_BS_LIMIT_6` = 2  (+/- 6.25%)
- `BSCFG_BS_LIMIT_12` = 3 (+/- 12.5%)

`BSCFG.BS_LIMIT` field.

### Preamble Counts

`NUM_PREAMBLE = [2,3,4,6,8,12,16,24]` (bytes). Indexed by `MDMCFG1.NUM_PREAMBLE` field (0-7).

### RF Strobes (RFST)

Commands to change radio state:
- `RFST_SFSTXON` = 0x00
- `RFST_SCAL` = 0x01
- `RFST_SRX` = 0x02  (enter receive)
- `RFST_STX` = 0x03  (enter transmit)
- `RFST_SIDLE` = 0x04 (enter idle)
- `RFST_SNOP` = 0x05

### MARC States

The radio's main state machine (MARCSTATE) can be one of many values (see `MARC_STATE_MAPPINGS`). Important states:
- `MARC_STATE_SLEEP` = 0x00
- `MARC_STATE_IDLE` = 0x01
- `MARC_STATE_RX` = 0x0D
- `MARC_STATE_TX` = 0x13

The mapping also provides which RF strobe returns the state to a known safe condition.

`MODES` dictionary maps numbers to state names and back.

### NIC Commands (APP_NIC)

Commands for the radio NIC application (0x42):
- `NIC_RECV` = 0x01
- `NIC_XMIT` = 0x02
- `NIC_SET_ID` = 0x03
- `NIC_SET_RECV_LARGE` = 0x05
- `NIC_SET_AES_MODE` = 0x06
- `NIC_GET_AES_MODE` = 0x07
- `NIC_SET_AES_IV` = 0x08
- `NIC_SET_AES_KEY` = 0x09
- `NIC_SET_AMP_MODE` = 0x0A
- `NIC_GET_AMP_MODE` = 0x0B
- `NIC_LONG_XMIT` = 0x0C
- `NIC_LONG_XMIT_MORE` = 0x0D

### FHSS Commands

Used with `APP_NIC` to control frequency hopping:
- `FHSS_SET_CHANNELS` = 0x10
- `FHSS_NEXT_CHANNEL` = 0x11
- `FHSS_CHANGE_CHANNEL` = 0x12
- `FHSS_SET_MAC_THRESHOLD` = 0x13
- `FHSS_GET_MAC_THRESHOLD` = 0x14
- `FHSS_SET_MAC_DATA` = 0x15
- `FHSS_GET_MAC_DATA` = 0x16
- `FHSS_XMIT` = 0x17
- `FHSS_GET_CHANNELS` = 0x18
- `FHSS_SET_STATE` = 0x20
- `FHSS_GET_STATE` = 0x21
- `FHSS_START_SYNC` = 0x22
- `FHSS_START_HOPPING` = 0x23
- `FHSS_STOP_HOPPING` = 0x24

### FHSS States

Defined in `FHSS_STATES`:
- `FHSS_STATE_NONHOPPING` = 0
- `FHSS_STATE_DISCOVERY` = 1
- `FHSS_STATE_SYNCHING` = 2
- `FHSS_STATE_SYNCHED` = 3
- `FHSS_STATE_SYNC_MASTER` = 4
- `FHSS_STATE_SYNCINGMASTER` = 5

### AES Modes

Defined in `chipcondefs.py` / `const.py`:
- `ENCCS_MODE_CBC` = 0x???
- `ENCCS_MODE_CBCMAC`
- `ENCCS_MODE_CFB`
- `ENCCS_MODE_CTR`
- `ENCCS_MODE_ECB`
- `ENCCS_MODE_OFB`

Also operational bits:
- `AES_CRYPTO_IN_ENABLE`
- `AES_CRYPTO_IN_OFF`
- `AES_CRYPTO_IN_ENCRYPT`
- `AES_CRYPTO_IN_DECRYPT`
- `AES_CRYPTO_OUT_ENABLE`
- `AES_CRYPTO_OUT_OFF`
- `AES_CRYPTO_OUT_ENCRYPT`
- `AES_CRYPTO_OUT_DECRYPT`

### Limits

- `RF_MAX_TX_BLOCK` = 255  (max bytes per USB packet)
- `RF_MAX_TX_CHUNK` = 240  (chunk size for long transmits)
- `RF_MAX_TX_LONG` = 65535 (max bytes with long transmit)
- `RF_MAX_RX_BLOCK` = 512  (max receive block size)

### Clock and Timer

- `TIP` tuple: `(64, 128, 256, 1024)` - tick increments for T2 timer.
- `T2SETTINGS_24MHz` and `T2SETTINGS_26MHz`: Precomputed (tickidx, tipidx, PR) for common dwell times (100,150,200,250 ms) at those crystal frequencies.

## Structure Definitions

`chipcondefs.py` imports `vstruct` and defines `RadioConfig` as a sequence of `v_uint8` fields, exactly matching the hardware register order from 0xDF00 to 0xDF3B.

Each field includes a comment with its address, e.g.:
- `sync1` at DF00
- `sync0` at DF01
- `pktlen` at DF02
- ...
- `marcstate` at DF3B

This VStruct allows reading/writing the entire configuration in one USB transaction by passing the binary representation.

## Mapping Dictionaries

The module builds reverse-lookup dictionaries for many constant groups:

```python
RCS = {}  # for RC_* constants
LCS = {}  # for LC_* constants
LCES = {} # for LCE_* constants
FHSS_STATES = {}  # for FHSS_STATE_*
MODES = {}  # for MARCSTATE numbers and names
```

These are created by iterating over `globals()` and matching prefix patterns. They allow converting between numeric codes and symbolic names, e.g., `MODES[0x0D]` -> `"MARC_STATE_RX"` and `MODES["MARC_STATE_RX"]` -> `0x0D`.

## Import Chain

- `const.py` imports:
  - `from .rflib_defs import *` (defines some generic constants like `RC_SUCCESS`, `RC_TEMP_ERR_BUFFER_NOT_AVAILABLE`, etc.)
  - `from .chipcondefs import *` (register addresses, modulation values, etc.)
  - `from .rflib_version import *` (version information)

Thus `const.py` is typically imported by other modules to get all needed constants in one place.

## Usage Pattern

Typical usage in `chipcon_nic.py`:

```python
from .const import *
...
self.poke(FREQ2, struct.pack("3B", self.radiocfg.freq2, self.radiocfg.freq1, self.radiocfg.freq0))
```

Constants like `FREQ2`, `APP_NIC`, `NIC_XMIT` are used extensively.

## See Also

- `chipcondefs.py` for the VStruct definitions and radio register map.
- `rflib_defs.py` for return codes and error constants.
- `chipcon_usb.py` for how these constants are used in USB transfers.
