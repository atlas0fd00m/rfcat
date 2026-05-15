# bits Module

## Overview

The `bits` module provides low-level bit manipulation and signal processing utilities used by the RfCat library. These functions are essential for handling binary data, synchronization detection, encoding/decoding, and whitening. They operate on Python bytes objects (byte strings) and produce byte strings.

Many functions are implemented in pure Python and may use bit-level arithmetic or struct packing/unpacking.

## Important Functions

### `correctbytes(val)`

Converts an integer `val` (0-255) to a single-byte bytes object. Handles Python 2/3 compatibility:

- In Python 2: returns `chr(val)`
- In Python 3: returns `bytes([val])`

Used throughout the codebase whenever a byte needs to be constructed from an integer for USB transfers or register writes.

### `ord23(thing)`

Returns the integer ordinal of a byte character. In Python 2, it directly calls `ord()`. In Python 3, bytes indexing already returns an integer, so it returns the value directly. This simplifies cross-version compatibility.

### `strBitReverse(string)`

Reverses the bits within each byte of `string`. Example: `0b10110001` becomes `0b10001101`. The function first converts the string to a big integer, calls `bitReverse(num, bits)`, then converts back.

The implementation is noted as being dependent on Python's number system and may not work well for large strings; it suggests breaking into an array of 8-bit numbers for efficiency.

### `bitReverse(num, bitcnt)`

Reverses the order of the lowest `bitcnt` bits in `num`. It shifts one bit at a time:
```python
newnum = 0
for idx in range(bitcnt):
    newnum <<= 1
    newnum |= num & 1
    num >>= 1
return newnum
```

### `shiftString(string, bits)`

Shifts the entire bitstream left by `bits` (0-7). This is a cross-byte shift: the high bits of each byte become the low bits of the next byte. The function treats the string as a continuous stream of bits. It carries over bits between bytes.

Implementation detail: It iterates through the string, computing `((string[x] << bits) + (string[x+1] >> (8-bits))) & 0xff`.

### `strXorMSB(string, xorval, size)`

XORs the given `string` with `xorval` using MSB-first ordering. The `size` parameter determines how many bytes to read at a time (1,2,4,8). The string is padded with zeros to size multiples. It uses struct format strings from `fmtsMSB`. This is used for whitening linear feedback shift register operations.

### `wtfo(string)`

A diagnostic function that produces 16 different shifted/bit-reversed variations of the input string. Used for testing.

### `getNextByte_feedbackRegister7bitsMSB()` / `getNextByte_feedbackRegister7bitsLSB()`

These implement a linear feedback shift register (LFSR) for data whitening. They return the next byte from the LFSR in MSB or LSB orientation. The comments note they come from the CC1111 datasheet.

### `whitenData(data)`

Applies data whitening (scrambling) to the packet bytes using a 7-bit LFSR. The CC1111 uses a specific polynomial. The function:
- Initializes LFSR to `0x7F`.
- For each byte, it XORs the byte with the high byte of the LFSR (MSB first).
- Advances the LFSR one bit per transmitted bit (total of 8 advances per byte).

**Comment**: "This is a 7-bit LFSR, all polynomials are from the CC1111 specs."

Whitening removes DC bias and helps with spectrum shaping.

### `dewhitenData(data)`

The same as `whitenData` because whitening is symmetric.

### `findSyncWord(array, sensitivity=4, minpreamble=2)`

Detects potential 16-bit sync words within a bitstream. Parameters:
- `sensitivity`: Number of mismatched bits allowed (typically 0-4).
- `minpreamble`: Minimum number of preamble bytes (0xAAAA) expected before sync word.

The function operates on a byte string, converting it to a bit stream and looking for patterns where at least `16 - sensitivity` bits match a candidate sync word. It also checks for preamble (alternating 1,0 pattern) preceding the sync word to increase confidence.

Returns a list of possible sync words (as integers) found in the packet.

**Important**: The code comments discuss handling of lowball modes where preamble may be omitted.

### `findSyncWordDoubled(array, sensitivity=4, minpreamble=2)`

Similar to `findSyncWord` but handles cases where the sync word is transmitted twice (doubled) due to Manchester encoding or other effects. This function looks for two consecutive sync words.

### `getBit(string, index)`

Extracts a single bit from the bitstream (big-endian within the string). Returns 0 or 1.

### `detectRepeatPatterns(array, maxpattern=24)`

Attempts to find repeated patterns in the bitstream, useful for analyzing periodic signals. It groups bits into patterns of length 1 to `maxpattern` and counts occurrences. Returns a dictionary mapping patterns to counts.

The algorithm tries to detect if there is a dominant repeating pattern, which could indicate a clock or encoding.

**Comment**: "This is for analyzing signals to see if they are periodic."

### `bitSectString(string, start, count)`

Extracts `count` bits from `string` starting at bit index `start` (0-indexed from MSB of first byte). Returns the bits as a byte string, right-aligned (LSB of the result contains the last extracted bit). This is useful for extracting arbitrary bit fields.

### `genBitArray(bitstream)`

Converts a byte string into an array of bits (list of 0/1). Used for easier manipulation.

### `reprBitArray(bits)`

Converts a list of bits back to a string of '0' and '1' characters for printing.

### `invertBits(data)`

Bitwise inversion of each bit in the byte string: `0xFF ^ byte`. Used by the `InverseCat` class to invert bits on transmit and receive (for inverted protocols).

### Manchester Encoding/Decoding

Manchester encoding represents each data bit as a transition: 0 -> high-to-low, 1 -> low-to-high. The CC1111 can do Manchester in hardware, but software fallback exists.

- `manchester_encode(data)`: Encodes each byte's bits into two bits each. Output length is double input.
- `manchester_decode(data)`: Decodes Manchester-encoded bitstream. It detects edges and maps to bits. Returns a tuple `(decoded, remainder)`.
- `diff_manchester_decode(data)`: Differential Manchester decoding.
- `biphase_mark_coding_encode(data)`: Alternative encoding.

### `findManchesterData(array)`

Attempts to locate Manchester-encoded data within a bitstream by looking for the expected pattern of transitions. Used in discovery mode.

### Encoding Selection

The `EnDeCode` class in `chipcon_nic.py` can be subclassed to provide custom encoding/decoding. Some predefined encoding strategies might exist, but the module mainly provides the bit primitives.

## Constants

- `fmtsLSB` and `fmtsMSB`: Lists of struct format strings for little-endian and big-endian packing of 1,2,4,8 byte integers.
- `sizes`: Corresponding sizes: `[0,1,2,4,4,8,8,8,8]`.
- `masks`: Bit masks for those sizes: `(1<<(8*i))-1`.
- `PYVER`: Python major version (2 or 3).

## Design Notes

- The bit manipulation functions assume continuous bitstreams; they do not respect byte boundaries except where specified.
- Functions like `findSyncWord` are computationally intensive; they are used in `discover()` and may be called for each received packet.
- Whitening uses a 7-bit polynomial (x^7 + x^4 + 1) typical for CC1111.
- Many functions contain Python 2/3 compatibility code because the project originally supported Python 2.7 and now Python 3.
- The module was originally written for interactive use with IPython; it includes debugging outputs when printed (like `print(hex(num))` inside `strBitReverse`) - these could be removed for production.

## See Also

- `chipcon_nic.py`: Uses `bits.findSyncWord`, `bits.invertBits`, `bits.shiftString` extensively.
- `ccspecan.py`: May use bit utilities for signal processing.
- `chipcondefs.py`: For understanding register layout.
