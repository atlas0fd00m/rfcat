# ccspecan Module (Spectrum Analyzer)

## Overview

The `ccspecan` module implements a spectrum analyzer GUI application using PySide6 (Qt). It visualizes RF signal strength across a frequency range in real-time, leveraging the RfCat dongle in a special spectrum analyzer mode.

**Key features**:
- Waterfall-like display showing signal strength vs. frequency
- Interactive graph with mouse markers and frequency/strength readouts
- Configurable frequency range and channel spacing
- Supports both live dongle data and playback from recorded data

This module was adapted from Project Ubertooth by Jared Boone.

## Architecture

The spectrum analyzer operates by setting the dongle into a continuous transmission mode where it sends a known pattern across all channels. The host measures RSSI on each channel to determine signal strength. The GUI displays this as a graph.

### Main Components

- **`SpecanThread`**: A background thread that continuously fetches spectrum data from the dongle (or from a recorded data file) and triggers UI updates via a callback.
- **`RenderArea`**: A custom `QWidget` that draws the spectrum graph and reticle (grid/labels). It uses double-buffering with `QPixmap` to avoid flicker.
- **`Window`**: The main application window that contains the `RenderArea` and handles keyboard/mouse interaction.

## Class: `SpecanThread`

A thread that pulls spectrum data and reports new frames.

```python
SpecanThread(data, low_frequency, high_frequency, freq_step, delay, new_frame_callback)
```

When `data` is an `rflib.RfCat` instance (live mode), the thread calls `data.recv(APP_SPECAN, SPECAN_QUEUE, 10000)` repeatedly. This receives a block of raw RSSI bytes from the dongle.

When `data` is a list (recorded mode), it iterates through the list of `(rssi_values, timestamp)` tuples, optionally sleeping `delay` seconds between frames to simulate real-time.

**Frame format**: The received `rssi_values` is a byte string where each byte represents an RSSI value in a signed dBm format. The conversion:
```python
rssi_values = [(ord23(x) ^ 0x80) // 2 - 88 for x in rssi_values]
```
This maps the raw 8-bit value to dBm (typical offset -88 dBm floor). The first 4 bytes are skipped (header).

The thread calls `new_frame_callback(frequency_axis, rssi_values)` for each frame. The `frequency_axis` is a NumPy linspace from `low_frequency` to `high_frequency` with length equal to number of bins.

**Stopping**: Call `stop()` to set `_stopping` flag and join the thread.

## Class: `RenderArea`

Displays the spectrum. Paints two layers:
- `_graph`: a black background with the "now" trace (white) and the maximum trace (green) over `_persisted_frames_depth` frames.
- `_reticle`: an overlay with grid lines and labels for dBm and MHz markers.

### Important Methods

- `_new_frame(frequency_axis, rssi_values)`: Called by `SpecanThread` when a new frame arrives. Stores the frame in `_frame` and appends to `_persisted_frames` ring buffer, then calls `update()` to schedule a repaint.

- `_draw_graph()`: Paints the graph layer. It fills with semi-transparent black (fade effect). Then draws:
  - `path_now`: white line connecting current RSSI values.
  - `path_max`: green line for maximum values seen in the persisted history.
  - Markers for peak max (red text with frequency and dBm) and mouse crosshairs (yellow, magenta).

- `_draw_reticle()`: Paints grid lines:
  - Horizontal dBm lines every 20 dBm.
  - Vertical frequency lines every `freq_step * 10` (or *20) MHz.
  - Labels for dBm and frequency (in MHz).

- `paintEvent(event)`: Composites the graph and reticle onto the widget.

### Coordinate Transforms

Four utility methods map between screen pixels and physical units:
- `_hz_to_x(frequency_hz)`: frequency -> horizontal pixel position.
- `_x_to_hz(x)`: horizontal pixel -> frequency.
- `_dbm_to_y(dbm)`: dBm (negative) -> vertical pixel position (lower on screen means stronger signal? Actually `_dbm_to_y` maps high dBm (e.g., 0) to lower y? Check: delta = high_dbm - dbm; normalized = delta / range; return normalized * height. So high dBm (close to high_dbm) yields low y, low dBm yields high y. So y increases downward (screen coordinates) corresponds to lower signal.
- `_y_to_dbm(y)`: vertical pixel -> dBm.

### Interaction

Mouse clicks set markers:
- **Left click**: sets primary marker (yellow crosshair) at pointer.
- **Right click**: sets secondary marker (magenta crosshair).
- **Middle click**: clears markers or toggles reticle visibility.

Markers display:
- Frequency in MHz.
- Signal strength in dBm.
- Difference between the two markers in frequency.

Keyboard: Handled by parent `Window`.

## Class: `Window`

Main application window. Inherits `QtWidgets.QWidget`.

### Initialization

```python
Window(data, low_freq, high_freq, spacing, delay=0.01, parent=None)
```

- `data`: Can be:
  - A string `"-"` meaning use live dongle: creates `rflib.RfCat()`, calls `_doSpecAn()` to start streaming.
  - A filename to load pickled data.
  - An `RfCat` instance directly? Actually `_open_data` handles these.
- `low_freq`, `high_freq`: Frequency range in Hz.
- `spacing`: Channel spacing in Hz (typically 250e3).
- `delay`: For playback; ignored in live mode.

The `RenderArea` is created and placed in a grid layout.

Window title is "RfCat Spectrum Analyzer (thanks Ubertooth!)".

### Event Handlers

- `closeEvent`: Stops the `SpecanThread` gracefully.

- `mousePressEvent`: Delegates to `RenderArea` markers as described.

- `keyPressEvent`: Handles:
  - Arrow keys to pan/zoom frequency range:
    - Left/Right: shift range by `spacing`.
    - Up/Down: multiply/divide `spacing` by 1.1.
    - When these change, a new `RenderArea` is created with new parameters (simplified restart).
  - 'H': print help text (same as help text from original Ubertooth).
  - 'M': simulate middle mouse (toggle markers).
  - 'Q': quit.

These allow keyboard-only operation.

### Standalone Main

When run as a script:
```bash
python ccspecan.py <data> <fbase> <fhigh> <fdelta> [delay]
```
It creates a `QApplication` and `Window` with the given parameters.

## Functions

### `ensureQapp()`

Creates a global `_qt_app` `QApplication` if one does not exist. Used by `RfCat.specan()` in `__init__.py` to ensure Qt is initialized before creating the window.

## Integration with rflib

The high-level method `RfCat.specan(centfreq=915e6, inc=250e3, count=104)` in `rflib/__init__.py` prepares the dongle:

1. Calls `_doSpecAn(centfreq, inc, count)` which:
   - Saves current radio configuration.
   - Sets the base frequency to `centfreq - (inc*count)/2`.
   - Sets channel spacing to `inc`.
   - Sends `APP_NIC` command `RFCAT_START_SPECAN` with the count byte.
   - Returns `(freq, delta)`.

2. Imports `rflib.ccspecan` and calls `ensureQapp()`.

3. Creates a `Window(self, freq, fhigh, delta, 0)` where `fhigh = freq + delta*(count+1)`.

4. Shows the window and enters Qt event loop (`_qt_app.exec_()`).

When the window closes, the dongle's specan mode should be stopped (via `_stopSpecAn` in `RfCat`).

## Data Flow

1. Dongle in specan mode continuously sends spectrum data packets on `APP_SPECAN` endpoint.
2. `SpecanThread` receives them.
3. Each frame updates the `RenderArea`'s ring buffer.
4. `paintEvent` draws the latest graph and max trace.

The "max trace" is useful to see which frequencies have had the strongest signal over time.

## Dependencies

- **PySide6**: Required for Qt bindings.
- **NumPy**: For numeric operations and fast arrays.
- **rflib**: The core library to communicate with the dongle.

## Performance Notes

- The `_draw_graph` method uses `QtGui.QPainterPath` to draw lines. It converts NumPy values to Python floats because of compatibility with older PySide versions.
- The persisted frames ring buffer avoids storing unlimited history; it keeps a fixed depth (350 frames).
- The fade effect is achieved by drawing a semi-transparent black rectangle over the previous graph (alpha 10/255). This gives a trailing effect.

## Known Limitations

- The GUI is not particularly optimized; for very fast updates, it might struggle.
- The spectrum analyzer relies on the dongle sending a continuous stream; if packets are dropped, the display may show gaps.
- The coordinate transforms assume linear frequency-axis mapping; they do not account for any non-linearities (but the hardware is linear).

## Customization

- `_persisted_frames_depth`: How many frames to keep for max trace.
- `_delay`: In recorded playback, delay between frames.
- Colors and fonts are hard-coded.

## See Also

- `__init__.py`: `RfCat.specan()` method.
- `chipcon_nic.py`: The `_doSpecAn()` and `_stopSpecAn()` commands.
- `bits.py`: Not directly used, but for bit-level processing.
