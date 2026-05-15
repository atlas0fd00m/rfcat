# rfcat_server Tool

## Overview

`rfcat_server` is a TCP server that exposes a RfCat dongle over the network. It provides two separate ports:
- **Data port** (default: 1900): Raw RF data stream (bidirectional), similar to `rfcat`'s raw mode.
- **Configuration port** (default: 1899): Command-line interface to configure the radio, similar to using the Python API interactively.

This allows remote clients to connect and control the dongle, making it useful for distributed testing or when the dongle is attached to a headless machine.

## Architecture

The server spawns:
- A **data listener** that accepts TCP connections on the NIC port. For each connection, it calls `nic.rf_redirection((socket,))` to shuttle data between the socket and the RF dongle.
- A **configuration listener** that runs in its own thread and presents a `cmd.Cmd`-based REPL over the TCP connection. Clients can type commands like `freq 433000000`, `modulation GFSK`, etc.

Both listeners run simultaneously.

### FileSocket Wrapper

The configuration connection expects a file-like object for stdin/stdout. `FileSocket` wraps a TCP socket to provide `read`, `readline`, and `write` methods, and it manages an internal buffer for line-oriented reading.

## Starting the Server

Run the script directly:

```bash
$ ./rfcat_server
```

By default it binds to all interfaces (`0.0.0.0`) on ports 1900 (data) and 1899 (config). You can change these via command-line arguments (run with `--help` to see options; the script accepts `nicidx`, `ip`, `nicport`, `cfgport` as arguments).

Example:

```bash
$ ./rfcat_server --ip 127.0.0.1 --nicport 5000 --cfgport 5001
```

## Client Usage

### Connecting for RF Data

Use `nc` (netcat) or any TCP client to connect to the data port. Data will flow in both directions. Remember to set the radio configuration first via the config port, because the raw data mode respects the current radio settings (frequency, modulation, packet length).

```bash
$ nc server.example.com 1900
```

### Connecting for Configuration

You can connect via `telnet` or `nc` to the config port and get an interactive command prompt:

```bash
$ telnet server.example.com 1899
```

Or:

```bash
$ nc server.example.com 1899
```

Once connected, you can type commands:

```
welcome to the cc1111usb interactive config tool.  hack fun!
(RfCat) help

Documented commands (type help <topic>):
========================================
baud        calibrate  foffset    help       m         resources  stop
cal         exit       frequency  Key        modeFSTXON specan
calibrate   file       id         kill       modes     start

(RfCat) freq 433920000
[...]
```

The commands are implemented as methods prefixed with `do_` in the `CC1111NIC_Server` class.

### Important Commands

- `freq <Hz>`: Set frequency (e.g., `freq 433920000`).
- `modulation <type>`: Set modulation (`2FSK`, `GFSK`, `4FSK`, `MSK`, `ASK_OOK`).
- `baud <rate>`: Set data rate (e.g., `baud 19200`). Recalculates related parameters.
- `modeRX`, `modeTX`, `modeIDLE`: Force radio state.
- `specan`: Enter spectrum analyzer mode (same as `rfcat -s`). Takes optional parameters.
- `stopspecan`: Leave spectrum analyzer mode.
- `calibrate`: Force a calibration cycle.

Many other commands exist (like `chan`, `pktlen`, `sync`, etc.) as inherited from the `cmd` shell; not all are implemented.

You can also execute Python expressions? Probably not; it's a limited command set.

## Data Flow

1. A client connects to the config port to set up the radio (frequency, modulation, etc.). The server holds a single `RfCat` instance.
2. The client then connects to the data port. The server calls `nic.rf_redirection((socket,))`. This begins streaming raw RF packets over the socket.
3. Multiple data connections could be accepted sequentially, but not concurrently (the `start()` method loops; each connection replaces the previous). For multiple clients, you'd need to modify the code to fan out.

## Security Considerations

- The server does not implement authentication. Anyone who can connect to the ports can control the dongle and transmit/receive.
- It binds to all interfaces by default. On a public network, this is a risk. Use a firewall or bind to localhost if only local access is needed.

## Use Cases

- Remote spectrum analysis on a Raspberry Pi attached to a dongle.
- Sharing a dongle among multiple developers on a network.
- Integrating with other tools via TCP (e.g., custom Python scripts using `socket`).
- As a bridge between GUI frontends and the dongle.

## Comparison to rfcat

`rfcat` is the standalone command-line tool that either runs interactive, raw, or specan. `rfcat_server` decouples the data plane from the control plane, allowing network access. It's less featureful than the full `rfcat` script but can be handy.

## Extending

The `CC1111NIC_Server` class inherits from `cmd.Cmd`. To add new commands, subclass and implement `do_<command>(self, line)` methods. Many radio configuration methods are already available from the `nic` object (`RfCat`). For example:

```python
def do_mypower(self, line):
    """Set power level (hex)"""
    self.nic.setPower(eval(line))
```

## See Also

- `rfcat` for the main CLI.
- `rflib/__init__.py` for the RfCat API.
