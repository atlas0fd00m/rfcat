# RfCat User Guide

## Introduction

The `rfcat` command-line tool is the primary interface to the RfCat dongle. It provides several operation modes:

- **Research Mode** (`-r`): Interactive Python shell with a pre-initialized `d` dongle object.
- **Spectrum Analyzer** (`-s`): GUI spectrum display.
- **Raw RF Redirection** (default): Bidirectional pipe between stdin/stdout and the RF link.
- **Bootloader** (`--bootloader`): Enter firmware flashing mode.

This guide explains each mode and typical usage patterns.

## Installation

Ensure you have Python 3.10+ and dependencies installed:

```bash
cd rfcat
pip install -e .
pip install "PySide6>6.0.0"   # optional, for spectrum analyzer
```

See `README.md` for more details.

## Basic Usage

Run `rfcat` with no arguments to start **raw RF redirection** mode. This connects your terminal (stdin/stdout) directly to the RF dongle.

```
$ rfcat
```

You can now type arbitrary bytes to transmit, and received packets will be printed to the terminal in a raw binary format. Typically you'll want to use a companion tool or script to handle the data.

For a more user-friendly experience, use the `-r` (research) mode.

### Interactive Research Mode

```
$ rfcat -r
```

This launches an embedded IPython (or Python) shell with a global `d` object representing the dongle. You can directly call methods:

```python
>>> d.ping()
>>> d.setFreq(433000000)
>>> d.setMdmModulation(MOD_ASK_OOK)
>>> d.makePktFLEN(250)
>>> d.RFxmit(b"Hello")
>>> d.RFrecv()
>>> d.reprRadioConfig()
```

The shell imports `from rflib import *` so constants like `MOD_ASK_OOK` are available.

You can also explore raw packet reception:

```python
>>> d.RFlisten()
```

Or discover unknown signals:

```python
>>> d.discover(lowball=1, IdentSyncWord=True)
```

To exit, press `Ctrl-D` or type `exit()`. The atexit handler will set the dongle to IDLE mode.

### Spectrum Analyzer Mode

```
$ rfcat -s -f 915e6 -c 250e3 -n 104
```

Parameters:
- `-f`, `--centfreq`: Center frequency in Hz (default: 902e6).
- `-c`, `--inc`: Channel spacing in Hz (default: 250e3).
- `-n`, `--specchans`: Number of channels (default: 104).

A PySide6 window opens, showing a scrolling graph of signal strength across the specified band. The dongle is put into a special mode where it transmits continuously; the RSSI (Received Signal Strength Indicator) of each channel is measured and sent to the host.

**Controls**:
- **Mouse**:
  - Left click: Mark primary frequency/dBm (yellow).
  - Right click: Mark secondary frequency/dBm (magenta).
  - Middle click: Toggle grid visibility / clear markers.
- **Keyboard**:
  - Arrow Left/Right: Pan frequency range by one channel spacing.
  - Arrow Up/Down: Increase/decrease channel spacing by 10%.
  - `H`: Show help.
  - `M`: Simulate middle mouse click.
  - `Q`: Quit.

The spectrum analyzer is useful for finding active channels, measuring signal strength, and visualizing spectrum occupancy.

### Bootloader Mode

To flash new firmware onto the dongle, you must first put it into bootloader mode:

```
$ rfcat --bootloader --force
```

**Important**: This is a destructive operation; the dongle will become unresponsive until a new image is flashed. The `--force` flag confirms you intend to do this. Without `--force`, the program prints a warning and exits.

Once in bootloader mode, you can use the `cc-bootloader` tool (or other TI bootloader utilities) to upload a new firmware image.

### Specifying Dongle Index

If you have multiple RfCat dongles connected, use `-i` or `--index` to select which one:

```
$ rfcat -i 1 -r
```

The default index is 0.

### Safe Mode

For troubleshooting, use `-S` or `--safemode`. This skips automatic radio configuration and some initialization steps, allowing you to manually configure the dongle. Useful if the default setup causes issues with custom hardware.

```
$ rfcat -r -S
```

## Raw RF Redirection Mode

When no special flag is given, `rfcat` runs in "transparent" mode:

```
$ rfcat
```

It calls `d.rf_redirection((sys.stdin, sys.stdout))`. This creates a data path:

- Bytes read from stdin are formed into packets (respecting the configured packet length) and transmitted via `RFxmit`.
- Received packets are written to stdout, prefixed with a timestamp (float, 4 bytes) and length (short, 2 bytes).

This mode is intended to be used with other programs via pipes. For example, you could connect to a network socket using `socat`:

```bash
socat -u TCP-LISTEN:5000,reuseaddr,fork - | rfcat
```

Or capture raw data to a file:

```bash
rfcat > capture.raw
```

Note: The packet boundaries are determined by the current radio configuration (FLEN or VLEN). Ensure you configure the radio appropriately for the protocol you want to talk to. In research mode, you can configure first and then exit to raw mode by pressing Ctrl-D and running `rfcat` again. The raw mode does not allow interactive configuration.

If you need to configure before piping, use research mode to set parameters and then call `rf_redirection` manually:

```python
>>> d.setFreq(433e6)
>>> d.makePktFLEN(64)
>>> d.rf_redirection((sys.stdin, sys.stdout))
```

Now `rflib` script can be modified to do that, or you can create a custom script.

## Advanced Techniques

### Frequency Hopping

To use FHSS (Frequency-hopping spread spectrum: is a method of transmitting radio signals by rapidly changing the carrier frequency among many frequencies occupying a large spectral band.), you can either use the high-level `FHSSNIC` methods or set up the dongle manually.

Example hopping script:

```python
#!/usr/bin/env python3
from rflib import *

d = FHSSNIC()
channels = [902e6 + i*200e3 for i in range(25)]
fchans = [int(d.setFreq(f) and d.getChannel() or f) for f in channels]  # calculate channel numbers
d.setChannels(fchans)
d.setMACperiod(10)  # 10 ms per channel
d.startHopping()
print("Hopping...")
try:
    while True:
        y, t = d.RFrecv()
        print("Got packet on channel", d.getChannel(), hexlify(y))
except KeyboardInterrupt:
    d.stopHopping()
```

### Low-Level Access

All low-level methods from `chipcon_nic` are available. For example, to directly poke a hardware register:

```python
>>> d.poke(0xDF01, b'\xab')  # write to SYNC0 register
>>> d.peek(0xDF01)          # read it back
b'\xab'
```

But careful: invalid register values can cause unpredictable behavior.

### AES Encryption

```python
>>> d.setAESkey(b'\x01'*16)
>>> d.setAESiv(b'\x00'*16)
>>> d.setAESmode(ENCCS_MODE_CTR | AES_CRYPTO_OUT_ON | AES_CRYPTO_OUT_ENCRYPT | AES_CRYPTO_IN_ON | AES_CRYPTO_IN_DECRYPT)
>>> d.setEnablePktCRC(False)  # often used with AES
```

The AES engine operates on 16-byte blocks.

### Discovery of Unknown Protocols

The `discover()` method is a powerful reverse-engineering tool:

```python
>>> d.discover(lowball=1, IdentSyncWord=True)
```

It will print received packets and attempt to deduce the sync word(s) used. You can also specify a list of candidate sync words to match:

```python
>>> d.discover(SyncWordMatchList=[0xabcd, 0x1234])
```

For deeper inspection, use regular expression search on the bit-level data (note that the regex operates on the byte string; you may need to shift bits to align):

```python
>>> d.discover(RegExpSearch=b'\x01\x02\x03\x04')
```

### Saving and Loading Packets

Capture packets with timestamps:

```python
>>> packets = d.RFcapture()
>>> import pickle
>>> pickle.dump(packets, open('capture.pkl', 'wb'))
```

Later, you can replay them:

```python
>>> data = pickle.load(open('capture.pkl', 'rb'))
>>> for pkt, t in data:
...     print(t, hexlify(pkt))
```

The spectrum analyzer can also load recorded data by passing a filename to `Window`.

## Tips and Tricks

- **Avoid busy loops**: When using `RFrecv()` in a script, use a reasonable timeout and handle `ChipconUsbTimeoutException`.
- **Restore radio state**: If you change settings and want to go back, save the config first:
  ```python
  d.getRadioConfig()
  saved = d.radiocfg
  # ... make changes ...
  d.setRadioConfig(saved)
  ```
- **Check radio state**: Use `d.getRadioState()` to see if the radio is RX, TX, IDLE, etc.
- **Set max power**: Often you want maximum transmission power. Use `d.setMaxPower()` after setting frequency.
- **USB buffer overflow**: If you miss packets, try decreasing packet rate or increasing the USB receive buffer with `send(APP_NIC, NIC_SET_RECV_LARGE, ...)`.

## Troubleshooting

- **"No Dongle Found"**: Ensure the dongle is plugged in and not in bootloader mode. Check USB permissions.
- **Dongle disconnects**: The library includes automatic reconnection. If the thread dies, try resetting the dongle.
- **No packets received**: Verify frequency, modulation, and packet settings match the transmitter. Use `lowball()` or `discover()` to increase sensitivity.
- **PySide6 import errors**: Install PySide6 (`pip install pyside6`). The `specan` mode requires it.

## Scripting Examples

### Simple Transmitter

```python
#!/usr/bin/env python3
from rflib import *
import time

d = RfCat()
d.setFreq(433920000)  # 433.92 MHz
d.setMdmModulation(MOD_ASK_OOK)
d.setMdmDRate(19200)
d.makePktFLEN(32)
d.setPower(0xC0)  # max power for 900MHz band

while True:
    d.RFxmit(b"PING")
    time.sleep(1)
```

### Simple Receiver

```python
#!/usr/bin/env python3
from rflib import *

d = RfCat()
d.setFreq(433920000)
d.setMdmModulation(MOD_ASK_OOK)
d.setMdmDRate(19200)
d.makePktFLEN(32)

try:
    while True:
        data, t = d.RFrecv(timeout=5000)
        print(f"[{t:.3f}] {hexlify(data)}")
except ChipconUsbTimeoutException:
    print("No packet received")
```

### Packet Replay

Record a series of packets with timestamps and then replay them at the same relative timing:

```python
# Record
d = RfCat()
packets = []
print("Recording, Ctrl-C to stop")
try:
    while True:
        pkt, t = d.RFrecv()
        packets.append((pkt, t))
        print(t, hexlify(pkt))
except KeyboardInterrupt:
    pass
pickle.dump(packets, open('recorded.pkl', 'wb'))

# Replay
d = RfCat()
# configure to match original settings ...
pkts = pickle.load(open('recorded.pkl', 'rb'))
last = 0
for pkt, t in pkts:
    dt = t - last
    if dt > 0:
        time.sleep(dt)
    d.RFxmit(pkt)
    last = t
```

## Next Steps

- Explore the API reference in `docs/api/` for a complete list of methods and constants.
- Read the inline code comments for deeper insights into hardware behavior.
- Join the RfCat community on GitHub for examples and support.

Enjoy hacking sub-GHz!
