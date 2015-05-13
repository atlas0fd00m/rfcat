/*
 * CC Bootloader - USB CDC class (serial) driver
 *
 * Adapted from AltOS code by Fergus Noble (c) 2011
 * AltOS code Copyright © 2009 Keith Packard <keithp@keithp.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; version 2 of the License.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
 */

#ifndef _USB_H_
#define _USB_H_

#include "cc1111.h"
#include "types.h"

// External interface

void initUSB();
void usbProcessEvents();
void vcom_disable();
void vcom_enable();
char vcom_getchar();
void vcom_putchar(char c);
void vcom_flush();

void vcom_putstr(char* __xdata  buff);
void vcom(char* __xdata  buff);
//void vcom_up();
//void vcom_down();
void usb_up(void);
void usb_down(void);

//void txdata(u8 app, u8 cmd, u16 len, __xdata u8* dataptr);

// End external interface

#define USB_SETUP_DIR_MASK    (0x01 << 7)
#define USB_SETUP_TYPE_MASK   (0x03 << 5)
#define USB_SETUP_RECIP_MASK  (0x1f)

#define USB_DIR_OUT 0
#define USB_DIR_IN  (1 << 7)

#define USB_TYPE_STANDARD 0
#define USB_TYPE_CLASS    (1 << 5)
#define USB_TYPE_VENDOR   (2 << 5)
#define USB_TYPE_RESERVED (3 << 5)

#define USB_RECIP_DEVICE    0
#define USB_RECIP_INTERFACE 1
#define USB_RECIP_ENDPOINT  2
#define USB_RECIP_OTHER     3

// Standard requests
#define USB_REQ_GET_STATUS        0x00
#define USB_REQ_CLEAR_FEATURE     0x01
#define USB_REQ_SET_FEATURE       0x03
#define USB_REQ_SET_ADDRESS       0x05
#define USB_REQ_GET_DESCRIPTOR    0x06
#define USB_REQ_SET_DESCRIPTOR    0x07
#define USB_REQ_GET_CONFIGURATION 0x08
#define USB_REQ_SET_CONFIGURATION 0x09
#define USB_REQ_GET_INTERFACE     0x0A
#define USB_REQ_SET_INTERFACE     0x0B
#define USB_REQ_SYNCH_FRAME       0x0C

//#define USB_DESC_DEVICE           1
#define USB_DESC_CONFIGURATION    2
//#define USB_DESC_STRING           3
//#define USB_DESC_INTERFACE        4
//#define USB_DESC_ENDPOINT         5
//#define USB_DESC_DEVICE_QUALIFIER 6
#define USB_DESC_OTHER_SPEED      7
#define USB_DESC_INTERFACE_POWER  8

#define USB_GET_DESC_TYPE(x)  (((x)>>8)&0xFF)
#define USB_GET_DESC_INDEX(x) ((x)&0xFF)

#define USB_CONTROL_EP    0
#define USB_INT_EP        1
#define USB_OUT_EP        4
#define USB_IN_EP         5
#define USB_CONTROL_SIZE  32

// Double buffer IN and OUT EPs, so each
// gets half of the available space
//
// Ah, but USB bulk packets can only come in 8, 16, 32 and 64
// byte sizes, so we'll use 64 for everything
#define USB_IN_SIZE   64
#define USB_OUT_SIZE  64

#define USB_EP0_IDLE      0
#define USB_EP0_DATA_IN   1
#define USB_EP0_DATA_OUT  2

#define LE_WORD(x) ((x)&0xFF),((u8) (((u16) (x))>>8))

// CDC definitions
#define CS_INTERFACE  0x24
#define CS_ENDPOINT   0x25

#define SET_LINE_CODING         0x20
#define GET_LINE_CODING         0x21
#define SET_CONTROL_LINE_STATE  0x22

// Data structure for GET_LINE_CODING / SET_LINE_CODING class requests
struct usb_line_coding {
  unsigned long  rate;
  unsigned char   char_format;
  unsigned char   parity;
  unsigned char   data_bits;
};

#define USB_READ_AGAIN    ((char) -1)

#define USB_VID 0xFFFE
#define USB_PID 0x000A

// iManufacturer
#define USB_iManufacturer_LEN 0x10
#define USB_iManufacturer_STRING "JobyGPS"
#define USB_iManufacturer_UCS2 'J', 0, 'o', 0, 'b', 0, 'y', 0, 'G', 0, 'P', 0, 'S', 0
// iProduct
#define USB_iProduct_LEN 0x1C
#define USB_iProduct_STRING "CC Bootloader"
#define USB_iProduct_UCS2 'C', 0, 'C', 0, ' ', 0, 'B', 0, 'o', 0, 'o', 0, 't', 0, 'l', 0, 'o', 0, 'a', 0, 'd', 0, 'e', 0, 'r', 0
// iSerial
#define USB_iSerial_LEN 0x0e
#define USB_iSerial_STRING "000001"
#define USB_iSerial_UCS2 '0', 0, '0', 0, '0', 0, '0', 0, '0', 0, '1', 0

extern __code __at(0x00aa) unsigned char usb_descriptors[];

#endif // _USB_H_
