# rfcat_msfrelay Tool

## Overview

`rfcat_msfrelay` is a modified version of `rfcat_server` that implements a JSON-based HTTP API for integration with **Metasploit's Hardware Bridge**. This allows Metasploit modules to control a RfCat dongle remotely over HTTP/REST.

The tool provides endpoints for:
- Radio configuration (frequency, modulation, data rate, etc.)
- Transmitting and receiving packets
- Querying hardware/firmware versions and status
- Spectrum analyzer data

It runs an embedded HTTP server (using `http.server.BaseHTTPRequestHandler`) on port 8080 by default.

## Architecture

- **Global NIC**: A single `RfCat` instance (`nic`) is created at module load and reused for all requests.
- **HTTP Server**: Listens for HTTP requests, parses query parameters, and dispatches to methods that call the RfCat API.
- **JSON Responses**: All responses are JSON objects, including status codes and data.

The server inherits from the same command functionality as `rfcat_server` but presents it as HTTP methods instead of a telnet CLI.

## Starting the Relay

```bash
$ ./rfcat_msfrelay [options]
```

It binds to all interfaces (`0.0.0.0`) on port 8080. There is no authentication; the entire API is open.

## API Reference

All endpoints are `GET` requests (though they may change state). Parameters are passed via query string.

### Status

- **Endpoint**: `/status`
- **Parameters**: none
- **Returns**: JSON object with fields:
  - `operational`: always 1 (could be ping-based)
  - `hw_specialty`: `{ "rftransceiver": true }`
  - `hw_capabilities`: `{ "cc11xx": true }`
  - `last_10_errors`: error count (TODO)
  - `api_version`: e.g., `"0.0.2"`
  - `fw_version`: firmware version string
  - `hw_version`: hardware version (from build info)
  - `device_name`: device name from build info

Example:
```json
{
  "operational": 1,
  "hw_specialty": { "rftransceiver": true },
  "hw_capabilities": { "cc11xx": true },
  "last_10_errors": 0,
  "api_version": "0.0.2",
  "fw_version": "1.9.1",
  "hw_version": "r1.0",
  "device_name": "RfCat"
}
```

### Statistics

- **Endpoint**: `/statistics`
- **Returns**:
  - `uptime`: seconds since server start
  - `packet_stats`: number of packets sent (or processed?) - may be updated in transmit endpoint
  - `last_request`: timestamp of last request
  - `voltage`: placeholder (always `"0.0v"`)

### Supported Indexes

- **Endpoint**: `/supported_idx`
- **Returns**: `{ "indexes": [nic.idx] }` - list of dongle indices available (normally just `[0]`).

### Reset

- **Endpoint**: `/reset`
- **Action**: Calls `nic.resetup()` to reinitialize the dongle (useful after USB hiccup).
- **Returns**: `{ "status": "Resetting" }`

### Set Frequency

- **Endpoint**: `/set_freq`
- **Parameters**:
  - `freq` (required): frequency in Hz (integer).
  - `mhz` (optional): crystal frequency in MHz (default 24). Rarely needed.
- **Action**: `nic.setFreq(int(freq), mhz)`
- **Returns**: `{ "success": true }` or `{ "success": false }` on error.

### Get Modulations

- **Endpoint**: `/get_modulations`
- **Returns**: List of supported modulation strings: `["2FSK", "GFSK", "4FSK", "ASK/OOK", "MSK", "2FSK/Manchester", "GFSK/Manchester", "ASK/OOK/Manchester", "MSK/Manchester"]`

### Set Modulation

- **Endpoint**: `/set_modulation`
- **Parameters**:
  - `mod` (required): modulation name (e.g., `"GFSK"`, must match one from `get_modulations` without the "/Manchester" part for plain).
- **Action**: Looks up the modulation constant in `MODULATIONS` dict, then calls `nic.setMdmModulation(modvalue)`. The radio is set to IDLE then RX afterward.
- **Returns**: `{ "success": true }` or failure.

### Fixed Packet Length

- **Endpoint**: `/make_packet_flen`
- **Parameters**:
  - `len` (required): packet length (bytes).
- **Action**: `nic.makePktFLEN(int(len))`
- **Returns**: `{ "success": true }`

### Variable Packet Length

- **Endpoint**: `/make_packet_vlen`
- **Parameters**:
  - `maxlen` (required): maximum variable packet length.
- **Action**: `nic.makePktVLEN(int(maxlen))`
- **Returns**: `{ "success": true }`

### Transmit Packet

- **Endpoint**: `/transmit`
- **Parameters**:
  - `data` (required): hex string of packet bytes (e.g., `"48656c6c6f"` for "Hello").
- **Action**: `nic.RFxmit(bytes.fromhex(data))`
- **Returns**: `{ "success": true }` (no ACK of actual transmission; Only checks that call didn't error).

### Set Sync Word

- **Endpoint**: `/set_sync`
- **Parameters**:
  - `sync` (required): hex string of 2-byte sync word (e.g., `"abcd"`).
- **Action**: `nic.setMdmSyncWord(int(sync, 16))`
- **Returns**: `{ "success": true }`

### Set Channel Spacing

- **Endpoint**: `/set_chan_spc`
- **Parameters**:
  - `spc` (required): channel spacing in Hz.
- **Action**: `nic.setMdmChanSpc(int(spc))`
- **Returns**: `{ "success": true }`

### Set Data Rate

- **Endpoint**: `/set_baud`
- **Parameters**:
  - `baud` (required): data rate in baud.
- **Action**: `nic.setMdmDRate(int(baud))`
- **Returns**: `{ "success": true }`

### Set Frequency Deviation

- **Endpoint**: `/set_deviation`
- **Parameters**:
  - `dev` (required): deviation in Hz.
- **Action**: `nic.setMdmDeviatn(int(dev))`
- **Returns**: `{ "success": true }`

### Set Channel Bandwidth

- **Endpoint**: `/set_chan_bw`
- **Parameters**:
  - `bw` (required): bandwidth in Hz.
- **Action**: `nic.setMdmChanBW(int(bw))`
- **Returns**: `{ "success": true }`

### Receive Packet

- **Endpoint**: `/receive`
- **Parameters**:
  - `timeout` (optional): timeout in ms (default 5000).
- **Action**: Calls `nic.RFrecv(timeout)`.
- **Returns**: JSON object with:
  - `data`: hex string of received packet (may be empty on timeout)
  - `timestamp`: float timestamp

If timeout occurs and no packet, returns `{ "data": "", "timestamp": 0 }` (subject to exception handling).

### Radio Configuration

- **Endpoint**: `/get_radio_config`
- **Action**: `nic.getRadioConfig()` and returns a representation (maybe a dict? The code not fully shown). In practice, this may return the `reprRadioConfig()` string? Actually I'd need to check implementation.

Given the truncated snippet, the actual endpoints include many more. But the above gives a flavor.

### Utility Endpoints

- `/set_preamble`: set number of preamble bytes.
- `/set_pqt`: set preamble quality threshold.
- `/enable_crc`, `/enable_whitening`: toggle features.
- `/set_address`: set packet address.

They follow similar patterns.

## Integration with Metasploit

Metasploit's hardware bridge expects an HTTP service that implements a specific set of endpoints. `rfcat_msfrelay` is designed to fulfill that contract. In Metasploit, you can configure a HWBridge session with:

```
set RHOST <rfcat_server_ip>
set RPORT 8080
```

Then use auxiliary or exploit modules that talk to the RfCat dongle.

## Security Warning

Just like `rfcat_server`, this tool provides no authentication. Anyone who can connect can transmit and receive. Use only on trusted networks or behind a VPN.

## Development Notes

- The code is based on `rfcat_server` but uses HTTP instead of raw Telnet.
- Global `nic` object persists for the life of the server.
- Some endpoints may be incomplete; refer to the source for exact behavior.

## See Also

- `rfcat_server` for the TCP-based configuration.
- Metasploit documentation on Hardware Bridge.
- `rflib/__init__.py` for the underlying API.
