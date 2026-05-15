# rflib_defs Module

## Overview

The `rflib_defs` module defines status and error codes used in communication between the host software and the dongle firmware. These constants are imported by `const.py` and used throughout the codebase to interpret return values.

## Error Classes

The module defines two sets of error codes:

### Last Code Errors (LCE_*)

These represent the last code or status from various operations, typically set by the firmware in a status register or returned in a response. They indicate why an operation failed or an exceptional condition occurred.

- `LCE_NO_ERROR` = 0x00: No error.
- `LCE_USB_EP5_TX_WHILE_INBUF_WRITTEN` = 0x01: A transmit was attempted while input buffer was being written.
- `LCE_USB_EP0_SENT_STALL` = 0x04: USB control endpoint stalled.
- `LCE_USB_EP5_OUT_WHILE_OUTBUF_WRITTEN` = 0x05: Conflict in EP5 out buffer.
- `LCE_USB_EP5_LEN_TOO_BIG` = 0x06: Packet length exceeds allowed size.
- `LCE_USB_EP5_GOT_CRAP` = 0x07: Received garbage data.
- `LCE_USB_EP5_STALL` = 0x08: Endpoint stalled.
- `LCE_USB_DATA_LEFTOVER_FLAGS` = 0x09: Unexpected leftover data flags.

Radio-specific errors:
- `LCE_RF_RXOVF` = 0x10: Receive overflow (packet dropped due to buffer overrun).
- `LCE_RF_TXUNF` = 0x11: Transmit underflow (data not provided fast enough).
- `LCE_DROPPED_PACKET` = 0x12: Packet was dropped.
- `LCE_RFTX_NEVER_TX` = 0x13: Transmit never started.
- `LCE_RFTX_NEVER_LEAVE_TX` = 0x14: Transmit never completed.
- `LCE_RF_MODE_INCOMPAT` = 0x15: Radio mode incompatible with operation.
- `LCE_RF_BLOCKSIZE_INCOMPAT` = 0x16: Block size incompatible.
- `LCE_RF_MULTI_BUFFER_NOT_INIT` = 0x17: Multi-buffer not initialized.
- `LCE_RF_MULTI_BUFFER_NOT_FREE` = 0x18: Multi-buffer not free.

### Return Codes (RC_*)

Returned by the firmware's application interface (APP_NIC) to indicate operation results.

- `RC_NO_ERROR` = 0x00: Success.
- `RC_TX_DROPPED_PACKET` = 0xec: Packet transmitted but dropped (maybe radio not ready).
- `RC_TX_ERROR` = 0xed: General transmit error.
- `RC_RF_BLOCKSIZE_INCOMPAT` = 0xee: Block size incompatible (likely too large without long transmit mode).
- `RC_RF_MODE_INCOMPAT` = 0xef: Radio mode incompatible (e.g., not in TX/RX).
- `RC_TEMP_ERR_BUFFER_NOT_AVAILABLE` = 0xfe: Temporary error; buffer not available, retry.
- `RC_ERR_BUFFER_SIZE_EXCEEDED` = 0xff: Buffer size exceeded.
- `RC_FAIL_TRANSMIT_LONG` = 0xffff: Long transmit failed.

### Python Client Only Errors (PY_*)

These are error codes used within the host-side Python library to indicate client-side issues.

- `PY_NO_ERROR` = 0x00.
- `PY_TX_BLOCKSIZE_INCOMPAT` = 0xd0: Packet >255 bytes with repeat/offset specified (incompatible with short transmit).
- `PY_TX_BLOCKSIZE_TOO_LARGE` = 0xda: Packet >65535 bytes (exceeds long transmit limit).

## Usage

These codes are checked in methods like `RFxmit` and `RFxmitLong`. For example, in `chipcon_nic.py`:

```python
error = RC_TEMP_ERR_BUFFER_NOT_AVAILABLE
while error == RC_TEMP_ERR_BUFFER_NOT_AVAILABLE:
    retval, ts = self.send(APP_NIC, NIC_LONG_XMIT_MORE, ...)
    error = struct.unpack("<b", retval[0:1])[0]
```

The `unittest` function in `chipcon_nic.py` also exercises error conditions (though minimally).

## Mapping to Strings

The `const.py` module builds dictionaries `RCS`, `LCS`, `LCES` by scanning its own globals for names starting with `RC_`, `LC_`, `LCE_` respectively. This allows converting numeric codes to symbolic names:

```python
from .const import RCS
print(RCS[0xfe])  # -> 'RC_TEMP_ERR_BUFFER_NOT_AVAILABLE'
```

These mappings are used in debugging to print human-readable error codes when the dongle returns an unexpected value.

## See Also

- `chipcon_usb.py`: Uses these return codes.
- `chipcon_nic.py`: Checks error codes after sending commands.
