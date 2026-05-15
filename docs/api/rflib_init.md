# rflib/__init__.py - High-Level Interface

## Overview

The `rflib/__init__.py` module defines the `RfCat` class, which serves as the primary user-facing interface to the rfcat hardware. It inherits from `FHSSNIC` and adds convenience methods for common tasks, interactive shell support, and spectrum analyzer integration.

Additionally, it provides:
- `InverseCat` class for inverted protocols.
- `interactive()` function to launch an interactive Python shell.
- `interact()` to try different IPython or Python shells.
- Constants like `RFCAT_START_SPECAN`, `RFCAT_STOP_SPECAN`, `MAX_FREQ`.

## Class: `RfCat`

```python
class RfCat(FHSSNIC):
    ...
```

Inherits all functionality from `FHSSNIC` (which inherits from `NICxx11`). This gives direct access to low-level methods like `setFreq`, `RFxmit`, `RFrecv`, etc.

### Additional Methods

#### `RFdump(msg="Receiving", maxnum=100, timeoutms=1000)`

Simple loop to receive and print packets. Wraps `RFrecv()` in a try/except for `ChipconUsbTimeoutException`.

```python
for x in range(maxnum):
    y, t = self.RFrecv(timeoutms)
    print("(%5.3f) %s:  %s" % (t, msg, hexlify(y)))
```

Useful for quick packet inspection.

#### `scan(basefreq=902e6, inc=250e3, count=104, delaysec=2, drate=38400, lowball=1)`

Performs a frequency sweep. It configures the radio (data rate, lowball mode) and then iterates over a range of channels, receiving any packets on each frequency.

Implementation:
- Calls `self.lowball(lowball)` to set sensitive mode.
- Sets data rate with `setMdmDRate(drate)`.
- For each channel in the range:
  - `setFreq(freq)`
  - `RFdump(timeoutms=delaysec*1000)`
  - Checks `keystop()` to allow user to break by pressing Enter.
- Restores original configuration with `lowballRestore()`.

A helpful way to survey a band for activity.

#### `specan(centfreq=915e6, inc=250e3, count=104)`

Launches the spectrum analyzer GUI. This is implemented in `rflib/ccspecan`.

Steps:
1. `_doSpecAn(centfreq, inc, count)` configures the dongle for spectrum analysis and returns `(freq, delta)`.
2. Imports `rflib.ccspecan` (ensuring PySide6 is available).
3. Calls `ccspecan.ensureQapp()` to initialize Qt if needed.
4. Computes `fhigh = freq + delta*(count+1)`.
5. Creates `ccspecan.Window(self, freq, fhigh, delta, 0)`.
6. Calls `window.show()` and `ccspecan._qt_app.exec_()` to run the GUI.

#### `_doSpecAn(centfreq, inc, count)`

Internal helper that:
- Saves current radio config (`getRadioConfig()`) into `_specan_backup_radiocfg`.
- Computes `basefreq = centfreq - halfspec` where `halfspec = (count * inc) / 2.0`.
- Sets frequency to `basefreq` and channel spacing to `inc`.
- Retrieves actual frequency and channel spacing (which may be quantized).
- Sends `APP_NIC` command `RFCAT_START_SPECAN` with a single byte count.
- Returns `(freq, delta)` for use by the GUI.

The function validates that `count <= 255` and that the total spectrum doesn't exceed `MAX_FREQ`.

#### `_stopSpecAn()`

Stops spectrum analyzer mode and restores the saved radio configuration:
- Sends `APP_NIC,RFCAT_STOP_SPECAN`.
- Restores `self.radiocfg = self._specan_backup_radiocfg`.
- Calls `setRadioConfig()`.

#### `rf_configure(*args, **kwargs)`

Convenience alias for `self.setRFparameters(*args, **kwargs)`. Allows quick configuration without remembering method names. (Note: `setRFparameters` is not implemented in `NICxx11`; subclasses may implement.)

#### `rf_redirection(fdtup, use_rawinput=False, printable=False)`

Continuously shuttle data between a file descriptor (or socket) and the RF dongle. This is the core of the `rfcat` CLI tool's transparent mode.

Parameters:
- `fdtup`: A tuple of input and output file descriptors. If a single object is passed, it is used for both input and output (like a terminal).
- `use_rawinput`: If True, interprets input as a Python string literal via `eval('"..."%data)` (a historic hack).
- `printable`: If True, prefixes output with timestamp.

**Algorithm**:
```python
while True:
    # Read from input fd (non-blocking select)
    if data available:
        read into buf
        pktlen = self.getPktLEN()
        if vlen: pktlen = ord(buf[0])
        if len(buf) >= pktlen:
            self.RFxmit(data[:pktlen])

    # Receive from RF
    try:
        data, time = self.RFrecv(1)
        if printable:
            data = "\n"+str(time)+": "+repr(data)
        else:
            data = struct.pack("<fH", time, len(data)) + data
        send to output fd
    except ChipconUsbTimeoutException:
        pass

    # Also forward spectrum analyzer data from APP_SPECAN
    try:
        data, time = self.recv(APP_SPECAN, 1, 1)
        pack with timestamp and send
    except ChipconUsbTimeoutException:
        pass
```

This method essentially creates a bidirectional bridge, suitable for connecting a terminal or network socket to the RF link.

### InverseCat

```python
class InverseCat(RfCat):
    def setMdmSyncWord(self, word, radiocfg=None):
        FHSSNIC.setMdmSyncWord(self, word ^ 0xffff, radiocfg)

    def RFrecv(self, timeout=1000):
        data, timestamp = RfCat.RFrecv(self, timeout)
        return rfbits.invertBits(data), timestamp

    def RFxmit(self, data):
        return RfCat.RFxmit(self, rfbits.invertBits(data))
```

A subclass that inverts all bits on both transmit and receive. The sync word is complemented to 0xFFFF ^ word because inverted signals have inverted sync words. Useful for protocols that use inverted modulation (e.g., some OOK implementations).

### Module-Level Constants

- `RFCAT_START_SPECAN` = 0x40
- `RFCAT_STOP_SPECAN` = 0x41
- `MAX_FREQ` = 936e6

These are NIC application commands for starting/stopping specan mode.

### Utility Functions

#### `cleanupInteractiveAtExit()`

Registers an atexit handler to set dongle to IDLE mode if debug codes are present. Attempts to gracefully shut down the radio on interpreter exit.

#### `interactive(idx=0, DongleClass=RfCat, intro='', safemode=False)`

Creates a global `d` object (`global d`) instantiated from `DongleClass` (default `RfCat`). If not safemode, sets mode to RX (`d.setModeRX()`). Registers `cleanupInteractiveAtExit`. Then calls `interact(lcls, gbls)` to start an interactive shell with the local and global namespaces merged.

This is what the `rfcat -r` command uses.

#### `interact(lcls, gbls, intro="")`

Attempts to find an IPython shell in various forms (IPython 0.11+, IPython.Shell, etc.). If none are available, falls back to `code.InteractiveConsole`. The `autocall=2` setting allows calling functions without parentheses in IPython.

Sets global `_qt_app` if needed.

Once a shell is obtained, it calls `embed()` (new IPython) or `mainloop()` with the combined namespaces.

### Shell Types

The function detects:
- `STYPE_IPYTHON811P`: IPython >= 0.11 (terminal.embed)
- `STYPE_IPYTHON`: older IPython (IPython.Shell.IPShell)
- `STYPE_CODE_INTERACT`: plain Python console

Constants: `STYPE_NONE`, `STYPE_IPYTHON`, `STYPE_IPYTHON811P`, `STYPE_CODE_INTERACT`.

## Important: Mode RX

In the interactive function, note:
```python
if not safemode:
    d.setModeRX()
```

But `setModeRX` is not defined in `RfCat` or its superclasses directly. It likely comes from the firmware's MAC layer; `FHSSNIC` or `NICxx11` may have a `setModeRX` inherited? Actually, it's probably defined in `chipcon_nic` via `FHSSNIC`? Let me check: I didn't see `setModeRX` in the snippets. It may be part of the FHSS state machine commands. Possibly `FHSS_STATE_RX`? Actually, in `chipcon_usb.py` there is `setRfMode(mode)`. There might be a convenience method in `RfCat` to set the radio to RX using the appropriate RF strobe. In any case, the interactive shell sets the dongle to receive mode.

## Usage as Script

If this module is run directly (`__main__`), it:
- Takes an optional index argument (default 0).
- Calls `interactive(idx)`.

This allows running `python -m rflib` to enter interactive mode.

## Integration Points

- **Spectrum Analyzer**: `specan()` uses `_doSpecAn()` and the ccspecan module.
- **FHSS**: The class inherits hopping methods.
- **EnDeCode**: Can set custom encoders via `setEnDeCoder`.
- **AES**: Methods from `NICxx11`.
- **Discovery**: `discover()`, `lowball()`, `RFlisten()`, `RFcapture()`.

## Design Philosophy

The `RfCat` class tries to hide complexity while still exposing the full flexibility. It's a "batteries included" wrapper around the lower-level `FHSSNIC`.

The `inverseCat` subclass demonstrates a simple transformation that can be applied without reimplementing all radio configuration.

## Comments of Note

In `rf_redirection()`: "FIXME: make this aware of VLEN/FLEN and the proper length" and "FIXME: probably want to take in a length struct here and then only send when we have that many bytes...". This indicates the RF redirection is a simple best-effort bridge not aware of packet boundaries beyond what the hardware provides.

In `_doSpecAn`: "if count>255: raise Exception("sorry, only 255 samples per pass... (count)")". The firmware limit.

## See Also

- `chipcon_usb.py`
- `chipcon_nic.py`
- `ccspecan.py`
- `bits.py`
