# RfCat Bootloader

## Overview

The RfCat dongle includes a bootloader that allows firmware updates via a serial connection. When the dongle is in bootloader mode, it enumerates as a different USB device and accepts Intel HEX records to reprogram the flash.

The bootloader utility is `CC-Bootloader/rfcat_bootloader`, a Python script that communicates with the dongle over its serial interface.

## Entering Bootloader Mode

Before flashing, put the dongle into bootloader mode using `rfcat`:

```bash
$ rfcat --bootloader --force
```

This changes the USB product ID to the bootloader ID (0x6049/0x604a/0xecc0). The dongle will appear as a serial port (e.g., `/dev/ttyACM0` on Linux or `COM3` on Windows).

**Important**: The bootloader does not contain the normal RF firmware. After flashing, you must reset the dongle to run the new image.

## Bootloader Protocol

The bootloader communicates using simple ASCII commands based on Intel HEX record syntax. Each command is a line ending with `\n`. The bootloader responds with a single character status code:

- `'0'`: Success
- `'1'`: Intel HEX Invalid
- `'2'`: Bad Checksum
- `'3'`: Bad Address
- `'4'`: Bad Record Type
- `'5'`: Record Too Long

## Using rfcat_bootloader

The script takes a serial port and a command:

```bash
python rfcat_bootloader <serial_port> <command> [options]
```

Serial port may be something like `/dev/ttyACM0` (Linux) or `COM3` (Windows).

### Commands

#### `download <hex_file>`

Download an Intel HEX file to the dongle's flash.

Example:
```bash
$ python rfcat_bootloader /dev/ttyACM0 download firmware.ihx
```

The script reads the HEX file line by line and sends data records (`:00...`) to the bootloader. It prints each line and the response code.

#### `verify <hex_file>`

Verify that the contents of flash memory match the given Intel HEX file.

The script reads the HEX file, then for each data record it performs a flash read and compares bytes.

#### `run`

Tell the bootloader to jump to the user code entry point. Sends the EOF record (`:00000001FF`) to trigger execution.

After this command, the dongle should reboot into the new firmware and enumerate as an RfCat device again.

#### `reset`

Reset the bootloader's internal state (e.g., clear the "pages already written" map). Useful if you need to re-download code without power cycling.

#### `erase_all`

Erase the entire user flash area. Use before a fresh download if you want to ensure all memory is cleared.

#### `erase <page>`

Erase a specific 1024-byte flash page. The bootloader resides in the first few pages; erasing those has no effect. Determine page number from address (address // 1024).

#### `read <start_addr> <len> [hex_file]`

Read `len` bytes from flash starting at `start_addr` (hex). If `hex_file` is provided, the data is written as Intel HEX records to that file. Otherwise, it's printed to stdout (in a raw hexdump-like format).

## Practical Flashing Workflow

1. Build or obtain a new firmware image in Intel HEX format (`.ihx`).
2. Put dongle into bootloader mode:
   ```bash
   rfcat --bootloader --force
   ```
3. Determine the serial port device.
   - On Linux: usually `/dev/ttyACM0` or `/dev/ttyUSB0` (check `dmesg`).
   - On Windows: check Device Manager for a new COM port under "Ports (COM & LPT)".
4. Download the image:
   ```bash
   python CC-Bootloader/rfcat_bootloader /dev/ttyACM0 download new_firmware.ihx
   ```
5. (Optional) Verify:
   ```bash
   python CC-Bootloader/rfcat_bootloader /dev/ttyACM0 verify new_firmware.ihx
   ```
6. Run the new firmware:
   ```bash
   python CC-Bootloader/rfcat_bootloader /dev/ttyACM0 run
   ```
7. The dongle should reappear as an RfCat USB device. Test with:
   ```bash
   rfcat -r
   ```

## Troubleshooting

- **Port busy**: Another process (like ModemManager) may have claimed the serial port. The script attempts to retry after 5 seconds. You may need to stop interfering services:
  ```bash
  sudo systemctl stop ModemManager
  ```
- **Checksum errors**: Ensure the HEX file is correct and not corrupted. Verify with the `verify` command after download.
- **Bootloader stuck**: Power-cycle the dongle; it should start in bootloader mode if you held the button? Actually the bootloader mode persists until a new image is run. Use `reset` command via serial.
- **Write failures**: Some flash pages may be protected. The bootloader should skip writing bootloader pages. Ensure you are writing to the correct region.

## Bootloader Implementation

The bootloader firmware is separate from the main RF firmware. It resides in the first flash pages and is resistant to erasure. Its responsibilities:
- Receive Intel HEX records over UART.
- Validate address ranges (only allow writes to user flash region).
- Perform flash programming and verification.
- Provide commands for read/erase.
- On success, jump to user code.

The protocol uses a simple line-oriented format. The bootloader acknowledges each record with a single-byte status.

## Differences from TI Bootloader

The CC1111 has an official TI bootloader that works with the SmartRF Flash Programmer. However, the RfCat bootloader is custom and tailored for easy use with Python scripts. It accepts the same Intel HEX format but runs over the USB CDC ACM serial interface.

## See Also

- `rfcat` script for entering bootloader mode.
- Intel HEX format specification.
- CC1111 datasheet for memory map.
