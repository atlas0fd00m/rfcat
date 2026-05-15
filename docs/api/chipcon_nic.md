# chipcon_nic Module

## Overview

The `chipcon_nic` module implements a Network Interface Controller (NIC) abstraction for the CC1111/CC2511 radio chip. It provides two main classes:

- **`NICxx11`**: Implements radio configuration and packet transmit/receive for CCxx11 family chips.
- **`FHSSNIC`**: Extends `NICxx11` with frequency hopping spread spectrum (FHSS) capabilities.

This is the core of the RfCat library, exposing high-level radio control methods.

## Class: `NICxx11`

Inherits from `USBDongle` (from `chipcon_usb`). Implements the radio-specific operations.

### Radio Configuration

The radio is configured via a set of hardware registers mapped into memory at addresses 0xDF00-0xDF3B. These registers are represented by the `RadioConfig` VStruct (see `chipcondefs.py`). `NICxx11` provides getter/setter methods that read or write these registers using `peek()`/`poke()` or bulk transfers.

#### `getRadioConfig()`

Reads the entire radio configuration from hardware into `self.radiocfg`. It sends a `SYS_CMD_PEEK` request for each register address, compiling the 60-byte configuration.

#### `setRadioConfig(radiocfg=None)`

Writes the configuration stored in `self.radiocfg` (or a provided `radiocfg`) to hardware registers using `poke()`. The radio is temporarily set to IDLE mode if needed, then restored.

#### `getRadioState(radiocfg=None)`

Returns the current MARCSTATE (Main Radio Control state machine) as a human-readable string from `MODES` mapping.

### Frequency Control

#### `getFreq(mhz=24, radiocfg=None)`

Reads the current frequency in Hz and the raw frequency word. Calculates:
```python
freqmult = (0x10000 / 1000000.0) / mhz
num = (radiocfg.freq2<<16) + (radiocfg.freq1<<8) + radiocfg.freq0
freq = num / freqmult
```

#### `setFreq(freq, mhz=24, applyConfig=True)`

Sets the radio frequency. The frequency word is computed as:
```python
num = int(freq * freqmult)
```

The method also selects appropriate VCO calibration settings (`fscal2`) based on frequency band (low, mid, high). The configuration is optionally applied immediately; if `applyConfig` is False, only `radiocfg` fields are modified.

#### `getChannel(radiocfg=None)` / `setChannel(channr, radiocfg=None)`

Channel number (0-255) is a simple register that the radio interprets relative to base frequency and channel spacing.

### Modulation and Demodulation

#### `getMdmModulation(radiocfg=None)` / `setMdmModulation(mod, radiocfg=None, invert=False)`

Gets or sets the modulation format. `mod` should be one of the `MOD_*` constants:

- `MOD_2FSK`
- `MOD_GFSK`
- `MOD_4FSK`
- `MOD_ASK_OOK`
- `MOD_MSK`

The code comment warns: "we may be only changing PA_POWER, not power levels" because ASK/OOK requires different power table configuration. The `invert` flag toggles inversion for OOK.

#### `getMdmDRate(mhz=24, radiocfg=None)` / `setMdmDRate(drate, mhz=24, radiocfg=None)`

Data rate (baud) configuration. The CC1111 uses mantissa/exponent representation; `setMdmDRate` searches for suitable `drate_e` and `drate_m` that produce the desired baud within hardware limits.

The formula is:
```
drate = 1000000.0 * mhz * (256 + drate_m) * pow(2, drate_e) / pow(2,28)
```

#### `getMdmDeviatn(mhz=24, radiocfg=None)` / `setMdmDeviatn(deviatn, mhz=24, radiocfg=None)`

Frequency deviation for FSK/MSK. Computes exponent `dev_e` and mantissa `dev_m` such that the resulting deviation approximates the requested value.

Deviation formula:
```
dev = 1000000.0 * mhz * (8 + dev_m) * pow(2, dev_e) / pow(2,17)
```

#### `getMdmChanBW(mhz=24, radiocfg=None)` / `setMdmChanBW(bw, mhz=24, radiocfg=None)`

Channel filter bandwidth. Determines receiver bandwidth. There is an extensive comment about selecting BW to occupy at most 80% of the channel filter while accounting for frequency uncertainty. The code includes a table of typical settings and also configures `FREND1` and `TEST2/TEST1` registers based on BW thresholds.

#### `getMdmChanSpc(mhz=24, radiocfg=None)` / `setMdmChanSpc(chanspc, ...)`

Channel spacing for frequency-hopping or channelized systems. The calculation:
```
chanspc = 1000000.0 * mhz / pow(2,18) * (256 + chanspc_m) * pow(2, chanspc_e)
```

### Synchronization

#### `getMdmSyncWord(radiocfg=None)` / `setMdmSyncWord(word, radiocfg=None)`

The 16-bit sync word used to detect packet start. Stored in `SYNC1` (MSB) and `SYNC0` (LSB) registers.

#### `getMdmSyncMode(radiocfg=None)` / `setMdmSyncMode(syncmode=SYNCM_15_of_16, radiocfg=None)`

Controls the sync detection algorithm. Modes (from `const.py`):
- `SYNCM_NONE`
- `SYNCM_15_of_16`
- `SYNCM_16_of_16`
- `SYNCM_30_of_32`
- `SYNCM_CARRIER` (carrier sense only)
- `SYNCM_CARRIER_15_of_16`, etc.

### Preamble

#### `getMdmNumPreamble(radiocfg=None)` / `setMdmNumPreamble(preamble=MFMCFG1_NUM_PREAMBLE_4, radiocfg=None)`

Sets the minimum number of preamble bytes transmitted before the sync word. Values are `NUM_PREAMBLE` array (2,3,4,6,8,12,16,24 bytes).

### Packet Configuration

#### `makePktFLEN(flen=RF_MAX_TX_BLOCK, radiocfg=None)`

Configures **fixed-length packet** mode. `flen` is the packet length (0-255). This sets `PKTCTRL0` length config to 0 (fixed) and writes `PKTLEN`. If `flen` is larger than `RF_MAX_TX_BLOCK` (255), it uses "infinite" mode (pktlen=0) with firmware handling.

#### `makePktVLEN(maxlen=RF_MAX_TX_BLOCK, radiocfg=None)`

Configures **variable-length packet** mode. The first byte after the sync word indicates the packet length. `maxlen` is the maximum allowed length.

#### `getPktLEN()`

Returns tuple `(pktlen, pktctrl0)` where `pktctrl0` contains the length configuration bits.

#### `setEnablePktCRC(enable=True, radiocfg=None)` / `getEnablePktCRC(radiocfg=None)`

Enable/disable CRC (cyclic redundancy check) on transmitted and received packets.

#### `setEnablePktDataWhitening(enable=True, radiocfg=None)` / `getEnablePktDataWhitening(radiocfg=None)`

Enable/disable data whitening (scrambling) to avoid long runs of zeros/ones.

#### `setPktPQT(num=3, radiocfg=None)` / `getPktPQT(radiocfg=None)`

Preamble Quality Threshold. The number of preamble bytes required before sync word checking begins. Values 0-7, representing 0-7.

#### `setEnablePktAppendStatus(enable=True, radiocfg=None)` / `getEnablePktAppendStatus(radiocfg=None)`

When enabled, two status bytes (RSSI and LQI) are appended to received packets.

#### `setPktAddr(addr)` / `getPktAddr()`

Set or get the packet address byte. Used for address filtering.

### Encoder/Decoder

The class supports pluggable EnDeCode objects (encoders/decoders). Set via `setEnDeCoder(endec=None)`. When transmitting (`RFxmit`) or receiving (`RFrecv`), data is passed through the encoder/decoder if set.

The `EnDeCode` base class defines `encode(msg)` and `decode(msg)` methods. Subclasses can implement specific coding (e.g., differential Manchester).

### Transmit and Receive

#### `RFxmit(data, repeat=0, offset=0)`

Transmits a packet. Parameters:
- `data`: bytes to transmit
- `repeat`: number of repetitions (for long packets)
- `offset`: offset into data for repeating (for selective repeats)

If `len(data)` exceeds `RF_MAX_TX_BLOCK` (255), and `repeat`/`offset` are not set, it calls `RFxmitLong()` for extended transmission.

**Encoding**: If an encoder is set, data is encoded before transmission.

**Timing**: The method calculates a wait time based on packet length and uses `send(APP_NIC, NIC_XMIT, ...)` with that timeout.

#### `RFxmitLong(data, doencoding=True)`

Transmit arbitrarily long data (up to `RF_MAX_TX_LONG` = 65535). The data is split into chunks of `RF_MAX_TX_CHUNK` (240) bytes. The firmware supports streaming multiple chunks via `NIC_LONG_XMIT` and `NIC_LONG_XMIT_MORE`. This function handles the chunking and flow control (retrying if buffer not available).

#### `RFrecv(timeout=USB_RX_WAIT, blocksize=None)`

Receives a packet. Blocks up to `timeout` milliseconds. Returns `(data, timestamp)` where `timestamp` is a float representing seconds (actually from `struct.unpack("<fH", ...)` in the higher layer).

The method optionally sets a larger receive buffer by calling `send(APP_NIC, NIC_SET_RECV_LARGE, ...)` if `blocksize` is provided.

If a decoder is set, the data portion is decoded.

#### `RFlisten()`

An interactive loop that dumps received packets to the console with timestamps and ASCII representation. Runs until Enter is pressed.

```python
while not keystop():
    try:
        y, t = self.RFrecv()
        print("(%5.3f) Received:  %s  | %s" % (t, hexlify(y), makeFriendlyAscii(y)))
    except ChipconUsbTimeoutException:
        pass
```

#### `RFcapture()`

Similar to `RFlisten()` but collects packets in a list and returns it after user exits.

#### `RFdump(msg="Receiving", maxnum=100, timeoutms=1000)`

Receive up to `maxnum` packets, printing each with `msg` and timing.

### Discovery and Analysis

#### `discover(lowball=1, debug=None, length=30, IdentSyncWord=False, ISWsensitivity=4, ISWminpreamble=2, SyncWordMatchList=None, Search=None, RegExpSearch=None)`

A powerful method for exploring unknown signals. It configures the radio in "lowball" mode (high sensitivity, minimal filtering) and then dumps received packets. Features:

- `lowball`: level (0-3) of filtering; 0=most permissive (SYNCM_NONE), 1=carrier detect, 2=15/16 sync, 3=16/16 sync.
- `IdentSyncWord`: analyze packets to guess sync words.
- `SyncWordMatchList`: list of sync words to specifically look for.
- `Search`: byte string to search within raw packet (may need bit shifts).
- `RegExpSearch`: regex to match packet bytes.

The method saves radio config, calls `lowball()`, then loops receiving packets. It prints hex dumps and optionally accumulates sync word statistics.

#### `lowball(level=1, sync=0xaaaa, length=250, pqt=0, crc=False, fec=False, datawhite=False)`

Sets the radio to a very sensitive configuration, ideal for capturing raw RF noise that might contain packets. It:

- Saves current radio config in `_last_radiocfg` (so `lowballRestore()` can restore).
- Configures packet length, CRC, FEC, data whitening, sync word, and Preamble Quality Threshold.
- Sets sync mode based on `level` (0 -> SYNCM_NONE, 1 -> SYNCM_CARRIER, 2 -> SYNCM_15_of_16, 3 -> SYNCM_16_of_16).

#### `lowballRestore()`

Restores the radio configuration saved by `lowball()`. Raises exception if called without prior `lowball`.

### Frequency Hopping Support

Although `NICxx11` does not implement hopping, it does provide some helpers:

- `adjustFreqOffset()`: auto-correct frequency offset using the radio's frequency estimator (for FSK/MSK). This uses the `freq_offset_accumulator`.
- `calculateMdmDeviatn()`, `calculatePktChanBW()`, `calculateFsIF()`, `calculateFsOffset()`: experimental helper methods that attempt to derive optimal radio settings based on data rate (from SmartRF Studio examples).

### Power Control

#### `setPower(power=None, radiocfg=None, invert=False)`

Sets output power levels. For ASK/OOK, power table configuration differs. The method writes `PA_TABLE0` and `PA_TABLE1` registers and updates `FREND0` to select the correct PA power.

#### `setMaxPower(radiocfg=None, invert=False)`

Sets maximum possible power based on frequency band. Uses pre-tuned power levels from SmartRF Studio:
- <= 400 MHz: 0xC2
- 401-464 MHz: 0xC0
- 465-900 MHz: 0xC2
- > 900 MHz: 0xC0

### AES Encryption

The CC1111 has an AES coprocessor. `NICxx11` provides methods to configure it:

- `setAESmode(aesmode)`: Sets AES mode (CBC, ECB, CFB, CTR, OFB, CBC-MAC) and enables/disables inbound/outbound encryption/decryption.
- `getAESmode()`: Returns current AES mode byte.
- `setAESiv(iv)`: Sets initialization vector (16 bytes).
- `setAESkey(key)`: Sets AES key (16 bytes).

These methods send messages to the firmware's `APP_NIC` with commands `NIC_SET_AES_MODE`, etc.

### Amplifier Control

- `setAmpMode(ampmode)`: Sets external amplifier mode (via `NIC_SET_AMP_MODE`).
- `getAmpMode()`: Returns amplifier mode.

### Status and Diagnostics

- `reprRadioConfig()`: Returns a multi-line human-readable representation of the entire radio configuration (hardware, software, frequency, modem, packet, AES, test signals, radio state, client state).
- `printRadioConfig()`: Prints the above.
- `reprMdmModulation(radiocfg)`: String like "GFSK".
- `reprRadioState(radiocfg)`: MARCSTATE and dongle error codes.
- `getRSSI()`: Reads RSSI register.
- `getLQI()`: Reads LQI register.

Many `repr*` helpers exist to format specific subsections.

### Testing

The `unittest(dongle)` function at the end of the file exercises many getter/setter pairs to ensure they round-trip correctly. It also tests FHSS state manipulation.

## Class: `FHSSNIC`

Inherits from `NICxx11`. Adds frequency hopping support.

### FHSS Control

#### `FHSSxmit(data)`

Transmits a packet using the FHSS (frequency hopping) firmware application. It sends `APP_NIC, FHSS_XMIT` with the data.

#### `changeChannel(chan)`

Immediately change the hopping channel to `chan` (0-255). Sends `FHSS_CHANGE_CHANNEL`.

#### `getChannels()` / `setChannels(channels=[])`

Get or set the list of channels (up to 256). `channels` is a list of channel numbers. The firmware keeps a channel table; `setChannels` sends the list as `length (H) + bytes`.

#### `nextChannel()`

Advance to the next channel in the table (wraps). Sends `FHSS_NEXT_CHANNEL`.

#### `startHopping()` / `stopHopping()`

Begin or end frequency hopping. Commands `FHSS_START_HOPPING` and `FHSS_STOP_HOPPING`.

### MAC Configuration

The FHSS firmware includes a Medium Access Control (MAC) layer that can automatically hop based on timer thresholds.

#### `setMACperiod(dwell_ms, mhz=24)`

Set the dwell time per channel (milliseconds). This calculates timer settings (`T2CTL`, `CLKCON`, `T2PR`) to achieve the desired period. It uses the `calculateT2()` function (defined earlier in the module) to find the best tick size and prescaler.

#### `getMACdata()` / `setMACdata(data)` / `reprMACdata()`

Access the firmware MAC data structure. The data is packed as:
```c
struct {
    u8 mac_state;
    u16 MAC_threshold;    // T2 overflow count before hopping
    u16 MAC_ovcount;
    u16 NumChannels;
    u16 NumChannelHops;
    u16 curChanIdx;
    u16 tLastStateChange;
    u16 tLastHop;
    u16 desperatelySeeking;
    u8 txMsgIdx;
    u8 txMsgIdxDone;
    u16 synched_chans;
}
```

#### `getMACthreshold()` / `setMACthreshold(value)`

Get or set the MAC threshold (number of timer overflows before changing channel).

#### `getFHSSstate()` / `setFHSSstate(state)`

Retrieve or set the FHSS state machine state. States are defined in `FHSS_STATES` from `const.py`:
- `FHSS_STATE_NONHOPPING` (0)
- `FHSS_STATE_DISCOVERY` (1)
- `FHSS_STATE_SYNCHING` (2)
- `FHSS_STATE_SYNCHED` (3)
- `FHSS_STATE_SYNC_MASTER` (4)
- `FHSS_STATE_SYNCINGMASTER` (5)

#### `mac_SyncCell(CellID=0x0000)`

Start synchronization to a FHSS cell with given ID. Sends `FHSS_START_SYNC`.

### Utility Functions

- `makeFriendlyAscii(instring)`: Converts a byte string to printable ASCII, replacing non-printables with `.`.
- `calculateT2(tick_ms, mhz=24)`: Computes T2 timer settings (tickidx, tipidx, PR) to achieve `tick_ms` interval.

## Constants (from const.py)

Many constants are imported from `const.py` for register addresses and bit masks:

- Register addresses: `FREQ2`, `FREQ1`, `FREQ0`, `MDMCFG0`...`MDMCFG4`, `PKTCTRL0`, `PKTCTRL1`, `FREND0`, `FSCAL2`, etc.
- Bit masks: `MDMCFG2_MOD_FORMAT`, `PKTCTRL0_LENGTH_CONFIG`, `MDMCFG4_CHANBW_E`, etc.
- Modulation constants: `MOD_2FSK`, `MOD_GFSK`, etc.
- Sync mode constants: `SYNCM_NONE`, `SYNCM_15_of_16`, etc.
- Packet length configs: `LENGTH_CONFIGS` (fixed, variable)
- MARC states: `MARC_STATE_SLEEP`, `MARC_STATE_RX`, `MARC_STATE_TX`, etc.
- App commands: `APP_NIC`, `NIC_XMIT`, `NIC_RECV`, `NIC_LONG_XMIT`, `NIC_SET_AES_MODE`, etc.
- FHSS commands: `FHSS_XMIT`, `FHSS_SET_CHANNELS`, `FHSS_START_HOPPING`, etc.

## Comments and Design Notes

The code contains many comments that reveal design decisions:

- The `lowball()` method comment: "this configures the radio to the lowest possible level of filtering, potentially allowing complete radio noise to come through as data. very useful in some circumstances."
- The `discover()` method is for reverse engineering unknown protocols: "discover() sets lowball mode to the mode requested (length too), and begins to dump packets to the screen. press <enter> to quit..."
- The `setFreq()` method includes a note about VCO calibration: when changing frequency across VCO boundaries, the `fscal2` register must be set appropriately (0x0A for low VCO, 0x2A for high VCO).
- Many getter/setter pairs follow a pattern: if `radiocfg` is None, they call `getRadioConfig()` to populate `self.radiocfg`, then use that. This allows caching the entire config to minimize round trips, but each setter writes the register immediately.
- The `RFxmitLong` method includes a comment: "calculate wait time ..." and uses retry logic with `RC_TEMP_ERR_BUFFER_NOT_AVAILABLE`.
- The `adjustFreqOffset` method references a TI design note about permanent frequency offset compensation.

## See Also

- `chipcon_usb.py` for the underlying USB transport.
- `const.py` for constant definitions.
- `bits.py` for bit-level utilities used in packet processing (e.g., `findSyncWord`, `invertBits`).
- `rflib/__init__.py` for the high-level `RfCat` class that uses these primitives.
