#ifndef CC2531_H
#define CC2531_H

#include <cc2430.h>
#include "cc2530-ext.h"



SFRX(USBADDR,   0x6200);        // Function Address
SFRX(USBPOW,    0x6201);        // Power / Control Register
SFRX(USBIIF,    0x6202);        // IN Endpoints and EP0 Interrupt Flags
SFRX(USBOIF,    0x6204);        // OUT Endpoints Interrupt Flags
SFRX(USBCIF,    0x6206);        // Common USB Interrupt Flags
SFRX(USBIIE,    0x6207);        // IN Endpoints and EP0 Interrupt Enable Mask
SFRX(USBOIE,    0x6209);        // Out Endpoints Interrupt Enable Mask
SFRX(USBCIE,    0x620B);        // Common USB Interrupt Enable Mask
SFRX(USBFRML,   0x620C);        // Current Frame Number (Low byte)
SFRX(USBFRMH,   0x620D);        // Current Frame Number (High byte)
SFRX(USBINDEX,  0x620E);        // Selects current endpoint. Make sure this register has the required value before any of the following registers are accessed. This register must be set to a value in the range 0 - 5.

SFRX(USBMAXI,   0x6210);        // Max. packet size for IN endpoint,            1-5
SFRX(USBCS0,    0x6211);        // EP0 Control and Status (USBINDEX = 0),       0
SFRX(USBCSIL,   0x6211);        // IN EP{1 - 5} Control and Status Low,         1-5
SFRX(USBCSIH,   0x6212);        // IN EP{1 - 5} Control and Status High,        1-5
SFRX(USBMAXO,   0x6213);        // Max. packet size for OUT endpoint,           1-5
SFRX(USBCSOL,   0x6214);        // OUT EP{1 - 5} Control and Status Low,        1-5
SFRX(USBCSOH,   0x6215);        // OUT EP{1 - 5} Control and Status High,       1-5
SFRX(USBCNT0,   0x6216);        // Number of received bytes in EP0 FIFO (USBINDEX = 0), 0
SFRX(USBCNTL,   0x6216);        // Number of bytes in OUT FIFO Low,             1-5
SFRX(USBCNTH,   0x6217);        // Number of bytes in OUT FIFO High,            1-5


SFRX(USBF0,     0x6220);        // Endpoint 0 FIFO
SFRX(USBF1,     0x6222);        // Endpoint 1 FIFO
SFRX(USBF2,     0x6224);        // Endpoint 2 FIFO
SFRX(USBF3,     0x6226);        // Endpoint 3 FIFO
SFRX(USBF4,     0x6228);        // Endpoint 4 FIFO
SFRX(USBF5,     0x622A);        // Endpoint 5 FIFO

  

//#define P0IFG_USB_RESUME        0x80    //rw0

//   SBIT(USBIF,    0xE8, 0); // USB Interrupt Flag

// USB activities
#define USB_ENABLE_PIN              P1_0
//#define USB_ENABLE_PIN              P1_1
#define NOP()                       __asm; nop; __endasm;
#define USB_DISABLE()               SLEEP &= ~SLEEP_USB_EN;
#define USB_ENABLE()                SLEEP |= SLEEP_USB_EN;
#define USB_RESET()                 USB_DISABLE(); NOP(); USB_ENABLE();
#define USB_INT_ENABLE()            IEN2|= 0x02;
#define USB_INT_DISABLE()           IEN2&= ~0x02;
#define USB_INT_CLEAR()             P2IFG= 0; P2IF= 0;

#define USB_PULLUP_ENABLE()         USB_ENABLE_PIN = 1;
#define USB_PULLUP_DISABLE()        USB_ENABLE_PIN = 0;

#define USB_RESUME_INT_ENABLE()     P0IE= 1
#define USB_RESUME_INT_DISABLE()    P0IE= 0
#define USB_RESUME_INT_CLEAR()      P0IFG= 0; P0IF= 0
#define PM1()                       SLEEP |= 1

#include "chipcon_usb.h"
#include "chipcon_dma.h"
#endif
