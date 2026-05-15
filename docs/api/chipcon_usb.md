# chipcon_usb Module

## Overview

The `chipcon_usb` module provides the low-level USB communication layer between the host computer and the RfCat dongle. It handles device enumeration, USB endpoint I/O, and threading for asynchronous operations.

## Key Classes

### `USBDongle`

The `USBDongle` class is the base class for all dongle communication. It manages three dedicated threads:

- **Control thread**: Handles reset events and reconnection
- **Receive thread**: Continuously reads from EP5 IN endpoint
- **Send thread**: Manages transmission queue to EP5 OUT endpoint

#### Initialization

```python
USBDongle(idx=0, debug=False, copyDongle=None, RfMode=RFST_SRX, safemode=False)
```

Parameters:
- `idx`: Index of dongle to open (if multiple are connected)
- `debug`: Enable debug output
- `copyDongle`: For thread-safe copying of dongle state
- `RfMode`: Initial RF mode (default: `RFST_SRX` - receive)
- `safemode`: Skip automatic radio configuration

#### USB Device Selection

The `_internal_select_dongle()` method uses `getRfCatDevices()` to find connected RfCat dongles. It looks for USB devices with:

- Vendor ID `0x0451` (TI) with product ID `0x4715`
- Or vendor ID `0x1d50` (OpenMoko) with product IDs `0x6047`, `0x6048`, `0x605b`, `0xecc1`

If a dongle is found in bootloader mode (product IDs `0x6049`, `0x604a`, `0xecc0`), the program exits to allow flashing.

The device is opened and interface `0` is claimed for exclusive use.

#### Threading Model

Three threads are started during initialization:

1. **`run_ctrl`**: Waits for `reset_event`, then calls `resetup()` to reconnect the dongle if USB was unplugged/replugged.
2. **`runEP5_recv`**: Reads incoming data from the dongle, populating `recv_queue` and `recv_mbox` by application (`APP_NIC`, `APP_SPECAN`, etc.).
3. **`runEP5_send`**: Processes `xmit_queue`, sending data buffers to the dongle.

Synchronization is done with `rsema` (receive semaphore) and `xsema` (transmit semaphore) locks, and events (`recv_event`, `xmit_event`) to signal data availability.

#### Core USB Transfers

- **`_sendEP0`**: Control transfer on endpoint 0 (vendor-specific)
  ```python
  _sendEP0(request=0, buf=None, value=0x200, index=0, timeout=DEFAULT_USB_TIMEOUT)
  ```
  Used for commands like peeking/poking registers.

- **`_recvEP0`**: Receive from control endpoint
  ```python
  _recvEP0(request=0, length=64, value=0, index=0, timeout=100)
  ```

- **`_sendEP5`**: Bulk write to EP5 OUT (host-to-dongle)
  Data is split into chunks of `_usbmaxo` ( typically 64 bytes). If a write fails, the buffer is re-queued.

- **`_recvEP5`**: Bulk read from EP5 IN (dongle-to-host)
  Returns up to 512 bytes (or `_usbmaxi`). Called by receive thread.

#### Buffer Management

- **`_clear_buffers(clear_recv_mbox=False)`**: Flushes receive queues and trash data. Used during reset to discard stale data.

- **`resetup(console=True, copyDongle=None)`**: Re-establishes USB connection after a reset event. Calls `_internal_select_dongle()` and `finish_setup()`, then configures radio parameters if not in safemode.

#### Ping

```python
ping(times=3, wait=1000, silent=False)
```

Sends a ping command (`SYS_CMD_PING`) to verify dongle responsiveness. The dongle echoes back a byte. Used for testing connectivity.

#### Peek/Poke

Low-level register access:

```python
peek(addr)           # Read a byte from hardware register at address `addr`
poke(addr, val)      # Write a byte `val` to register `addr`
```

These use `SYS_CMD_PEEK` and `SYS_CMD_POKE`.

#### Radio Configuration

- **`getRadioConfig()`**: Reads all 60 radio configuration registers (0xDF00-0xDF3B) into `self.radiocfg` (a `RadioConfig` instance defined in `chipcondefs.py`). The registers are read using a series of peek commands.

- **`setRadioConfig(radiocfg=None)`**: Writes the current `self.radiocfg` to hardware registers using poke commands. If `radiocfg` is provided, that configuration is written instead.

- **`setRFparameters()`**: Intended to be overridden by subclasses to set application-specific radio parameters (like modulation, frequency, etc.). In `NICxx11` this is not implemented; subclasses call configuration methods.

#### Reconnection Handling

If the dongle is unplugged, the control thread detects it via `reset_event`. The next call to `resetup()` will attempt to reconnect. This ensures robustness.

## Constants

### USB-related

- `DEFAULT_USB_TIMEOUT`: 1000 ms
- `EP_TIMEOUT_IDLE`: 400 ms
- `EP_TIMEOUT_ACTIVE`: 10 ms
- `USB_MAX_BLOCK_SIZE`: 512 bytes
- `EP5OUT_BUFFER_SIZE`: 516 bytes (must match firmware)
- `USB_GET_STATUS`, `USB_CLEAR_FEATURE`, etc.: Standard USB request codes.

### Application IDs

- `APP_GENERIC` = 0x01
- `APP_DEBUG` = 0xFE
- `APP_SYSTEM` = 0xFF

These IDs distinguish which firmware application should handle a message on EP5.

### System Commands (SYS_CMD_*)

Used with `_sendEP0` to perform device-level operations:
- `SYS_CMD_PING`
- `SYS_CMD_PEEK` / `SYS_CMD_POKE`
- `SYS_CMD_STATUS`
- `SYS_CMD_BOOTLOADER`
- `SYS_CMD_RFMODE`
- `SYS_CMD_PARTNUM`
- etc.

## Error Handling

- `ChipconUsbTimeoutException`: Raised when USB transfer times out.
- Exceptions during USB operations are caught and may cause reconnection attempts.

## Device Discovery

`getRfCatDevices()` returns a list of `usb.device` objects for connected RfCat dongles. It iterates through all USB buses and devices, matching the vendor/product IDs. Note: If any dongles are in bootloader mode, it prints a message and exits, because bootloader mode is intended for flashing.

## Subclassing

`USBDongle` is designed to be subclassed. The `NICxx11` class in `chipcon_nic.py` inherits from `USBDongle` and adds radio-specific methods.

Subclasses can override `setRFparameters()` to set up the radio during `finish_setup()`.

## Thread Safety

The class is thread-safe for concurrent access via the semaphore-protected queues. The `reset_event` ensures only one reconnection occurs at a time.

## Debugging

Set `debug=True` to print USB transfers to stderr. The `_debug` flag controls this output.

## Internals: Firmware Interaction

The dongle firmware implements a simple messaging protocol:
- Control endpoint (EP0) for register access and system commands.
- Bulk endpoints EP5 IN/OUT for application data.

Messages on EP5 are prefixed with an application ID (`APP_NIC`, `APP_SPECAN`, etc.) and a command byte. The `send()` method (implemented in `NICxx11`) builds these messages.

## See Also

- `chipcon_nic.py` for higher-level radio operations.
- `const.py` for constant definitions.
- `chipcondefs.py` for register layout.
