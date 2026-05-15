# RfCat Documentation

## Overview

**RfCat** (Radio Frequency Category) is a versatile wireless research tool that combines hardware (a USB dongle based on the Texas Instruments CC1111/CC2511 sub-GHz transceiver) with a powerful Python software library. It serves as the "Swiss Army knife of subGHz" for research, testing, and reverse engineering of wireless protocols.

The project provides:

- **Command-line tools** for interactive radio exploration (`rfcat`), spectrum analysis, and packet transmission/reception
- **Python library (`rflib`)** for low-level radio control, packet handling, and frequency hopping
- **Spectrum Analyzer GUI** built with PySide6 for visualizing spectrum data
- **Server and relay tools** for distributed operations

## Key Features

- **Frequency Range**: 281-961 MHz (depending on hardware)
- **Modulations**: 2FSK, GFSK, 4FSK, MSK, ASK/OOK with Manchester encoding support
- **Packet Handling**: Fixed and variable length packets, CRC, data whitening, AES encryption
- **Frequency Hopping**: Built-in support for FHSS (Frequency Hopping Spread Spectrum) with MAC layer coordination
- **USB Interface**: High-speed USB communication with threaded receive/transmit
- **Research Mode**: Interactive Python shell with direct access to the `d` dongle object

## Project Structure

```
rfcat/
├── rfcat              # Main CLI tool entry point
├── rfcat_server       # Server component for remote dongle management
├── rfcat_msfrelay     # Metasploit relay integration
├── rflib/              # Core Python library
│   ├── __init__.py    # RfCat class defines high-level interface
│   ├── chipcon_usb.py # USB communication layer (USBDongle)
│   ├── chipcon_nic.py # NIC implementation (NICxx11, FHSSNIC)
│   ├── bits.py        # Bit manipulation utilities (whitening, sync detection, Manchester)
│   ├── const.py       # Hardware constants and register definitions
│   ├── chipcondefs.py # Radio register map (RadioConfig VStruct)
│   ├── ccspecan.py    # Spectrum Analyzer GUI (PySide6)
│   ├── intelhex.py    # Intel HEX file parser
│   ├── vstruct/       # Structure library for binary data
│   └── ...
├── tests/             # Unit tests
└── firmware/          # Dongle firmware source
```

## Hardware

The RfCat dongle uses a TI CC1111 or CC2510/CC2511 microcontroller operating in sub-GHz ISM bands. The firmware runs on the dongle and handles low-level radio timing and USB communication.

Supported chip versions (from `const.py`):
- `CC1111` (0x11)
- `CC1110` (0x01)
- `CC2511` (0x91)
- `CC2510` (0x81)

The dongle enumerates as a USB device with vendor ID 0x0451 (TI) or 0x1d50 (OpenMoko), and product IDs 0x6047, 0x6048, 0x605b, 0xecc1 for RfCat mode.

## Software Architecture

The software is organized in layers:

1. **USB Layer** (`chipcon_usb.py`): `USBDongle` handles USB device enumeration, endpoint I/O, and threading. Three threads manage:
   - Control messages (EP0)
   - Receive data (EP5 IN)
   - Transmit data (EP5 OUT)

2. **NIC Layer** (`chipcon_nic.py`): `NICxx11` and `FHSSNIC` classes implement radio-specific operations. They abstract the hardware registers and provide methods like `setFreq()`, `setMdmModulation()`, `RFxmit()`, `RFrecv()`. The `FHSSNIC` subclass adds frequency hopping capabilities.

3. **High-Level Interface** (`__init__.py`): The `RfCat` class inherits from `FHSSNIC` and provides convenience methods (`scan()`, `specan()`, `rf_redirection()`) and an interactive shell.

4. **Utilities**: `bits.py` supplies bit-level operations including sync word detection, Manchester encoding/decoding, data whitening, and bit inversion.

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/atlas0fd00m/rfcat.git
cd rfcat

# Install dependencies (Python 3.10+)
pip install -r requirements.txt

# Optional: spectrum analyzer GUI
pip install "PySide6>6.0.0"

# Install the package (development mode)
pip install -e .
```

### Basic Usage

Start an interactive research shell:
```bash
$ rfcat -r
```

This gives you a `d` object representing the dongle:

```python
>>> d.ping()
>>> d.setFreq(433000000)          # Set frequency in Hz
>>> d.setMdmModulation(MOD_ASK_OOK)
>>> d.makePktFLEN(250)
>>> d.RFxmit(b"HALLO")           # Transmit
>>> d.RFrecv()                   # Receive
>>> print(d.reprRadioConfig())  # Print full radio configuration
```

Start spectrum analyzer:
```bash
$ rfcat -s -f 915e6 -c 250e3 -n 104
```

This launches a PySide6 GUI showing real-time spectrum data.

### Bootloader Mode

To flash new firmware:
```bash
$ rfcat --bootloader --force
```

This puts the dongle into bootloader mode, ready for a new image.

## Advanced Usage

### Frequency Hopping

The `FHSSNIC` class supports hopping across multiple channels:

```python
d = FHSSNIC()
channels = [freq0, freq1, freq2, ...]
d.setChannels(channels)
d.startHopping()
```

The dongle's internal MAC automates channel changes based on a configurable timer (`setMACperiod()`).

### Low-Level Packet Injection

For custom protocols, use `RFxmit()` and `RFrecv()` directly. You can also enable/disable CRC, Manchester encoding, data whitening, and AES encryption.

### Discovery Mode

The `discover()` method configures a very sensitive receiver to dump raw packets, optionally identifying sync words:

```python
d.discover(lowball=1, IdentSyncWord=True)
```

## Spectrum Analyzer

The spectrum analyzer (`-s`) shows a waterfall display and graph of RF energy across a range of frequencies. It works by setting the dongle to transmit continuous data while the host measures RSSI per channel. The GUI is implemented in `rflib/ccspecan.py`.

## Tools

- **`rfcat`**: Main CLI with interactive, raw RF redirection, and specan modes.
- **`rfcat_server`**: TCP server to share a dongle among multiple clients.
- **`rfcat_msfrelay`**: Integration with Metasploit as a relay for pentesting.

## Documentation Contents

- [User Guide](user_guide.md): Practical usage of the `rfcat` tool and techniques.
- [Bootloader Guide](bootloader.md): Flashing new firmware onto the dongle.
- [API Reference](api/): Detailed documentation of the Python library modules.
  - [chipcon_usb](api/chipcon_usb.md) – USB communication layer
  - [chipcon_nic](api/chipcon_nic.md) – NIC implementation and radio control
  - [rflib init](api/rflib_init.md) – High-level `RfCat` class
  - [bits](api/bits.md) – Bit manipulation utilities
  - [const](api/const.md) – Hardware constants
  - [ccspecan](api/ccspecan.md) – Spectrum analyzer GUI
  - [vstruct](api/vstruct.md) – Binary structure library
  - [rflib_defs](api/rflib_defs.md) – Error codes
- [Tools](tools/):
  - [rfcat_server](tools/rfcat_server.md) – TCP server for remote control
  - [rfcat_msfrelay](tools/rfcat_msfrelay.md) – HTTP API for Metasploit integration

## Contributing

The project is open source under BSD license. Contributions welcome!

## Credits

Created by atlas0fd00m. Built on Project Ubertooth (Jared Boone).
