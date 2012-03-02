#ifndef CC1111_H
#define CC1111_H

#include "cc1110-ext.h"
#include <cc1110.h>




SFRX(USBADDR,   0xDE00);        // Function Address
SFRX(USBPOW,    0xDE01);        // Power / Control Register
SFRX(USBIIF,    0xDE02);        // IN Endpoints and EP0 Interrupt Flags
SFRX(USBOIF,    0xDE04);        // OUT Endpoints Interrupt Flags
SFRX(USBCIF,    0xDE06);        // Common USB Interrupt Flags
SFRX(USBIIE,    0xDE07);        // IN Endpoints and EP0 Interrupt Enable Mask
SFRX(USBOIE,    0xDE09);        // Out Endpoints Interrupt Enable Mask
SFRX(USBCIE,    0xDE0B);        // Common USB Interrupt Enable Mask
SFRX(USBFRML,   0xDE0C);        // Current Frame Number (Low byte)
SFRX(USBFRMH,   0xDE0D);        // Current Frame Number (High byte)
SFRX(USBINDEX,  0xDE0E);        // Selects current endpoint. Make sure this register has the required value before any of the following registers are accessed. This register must be set to a value in the range 0 - 5.

SFRX(USBMAXI,   0xDE10);        // Max. packet size for IN endpoint,            1-5
SFRX(USBCS0,    0xDE11);        // EP0 Control and Status (USBINDEX = 0),       0
SFRX(USBCSIL,   0xDE11);        // IN EP{1 - 5} Control and Status Low,         1-5
SFRX(USBCSIH,   0xDE12);        // IN EP{1 - 5} Control and Status High,        1-5
SFRX(USBMAXO,   0xDE13);        // Max. packet size for OUT endpoint,           1-5
SFRX(USBCSOL,   0xDE14);        // OUT EP{1 - 5} Control and Status Low,        1-5
SFRX(USBCSOH,   0xDE15);        // OUT EP{1 - 5} Control and Status High,       1-5
SFRX(USBCNT0,   0xDE16);        // Number of received bytes in EP0 FIFO (USBINDEX = 0), 0
SFRX(USBCNTL,   0xDE16);        // Number of bytes in OUT FIFO Low,             1-5
SFRX(USBCNTH,   0xDE17);        // Number of bytes in OUT FIFO High,            1-5


SFRX(USBF0,     0xDE20);        // Endpoint 0 FIFO
SFRX(USBF1,     0xDE22);        // Endpoint 1 FIFO
SFRX(USBF2,     0xDE24);        // Endpoint 2 FIFO
SFRX(USBF3,     0xDE26);        // Endpoint 3 FIFO
SFRX(USBF4,     0xDE28);        // Endpoint 4 FIFO
SFRX(USBF5,     0xDE2A);        // Endpoint 5 FIFO

  
  

//#define P0IFG_USB_RESUME        0x80    //rw0

//   SBIT(USBIF,    0xE8, 0); // USB Interrupt Flag

#include "chipcon_usb.h"
#include "chipcon_dma.h"

#endif
