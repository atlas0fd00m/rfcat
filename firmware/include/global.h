#ifndef GLOBAL_H
#define GLOBAL_H

#include "types.h"

#ifdef CC1111
  #include "cc1111.h"
#elif defined CC2531
  #include "cc2531.h"
#elif defined IMME
  #include <cc1110.h>
  #include "cc1110-ext.h"
#endif

#include "bits.h"

// used for debugging and tracing execution.  see client's ".getDebugCodes()"
extern __xdata u8 lastCode[2];
extern __xdata u32 clock;

//////////////  DEBUG   //////////////
//#define VIRTUAL_COM
//#define RADIO_EU 
//#define TRANSMIT_TEST
//#define RECEIVE_TEST
//////////////////////////////////////
#define LC_USB_INITUSB                  0x2
#define LC_MAIN_RFIF                    0xd
#define LC_USB_DATA_RESET_RESUME        0xa
#define LC_USB_RESET                    0xb
#define LC_USB_EP5OUT                   0xc
#define LC_RF_VECTOR                    0x10
#define LC_RFTXRX_VECTOR                0x11

#define LCE_USB_EP5_TX_WHILE_INBUF_WRITTEN      0x1
#define LCE_USB_EP0_SENT_STALL                  0x4
#define LCE_USB_EP5_OUT_WHILE_OUTBUF_WRITTEN    0x5
#define LCE_USB_EP5_LEN_TOO_BIG                 0x6
#define LCE_USB_EP5_GOT_CRAP                    0x7
#define LCE_USB_EP5_STALL                       0x8
#define LCE_USB_DATA_LEFTOVER_FLAGS             0x9
#define LCE_RF_RXOVF                            0x10
#define LCE_RF_TXUNF                            0x11

// USB activities
#define USB_ENABLE_PIN              P1_0
//#define USB_ENABLE_PIN              P1_1
#define NOP()                       __asm; nop; __endasm;

// Checks
#define IS_XOSC_STABLE()    (SLEEP & SLEEP_XOSC_S)


/* board-specific defines */
#ifdef IMME
    // CC1110 IMME pink dongle - 26mhz
    #define LED_RED   P2_3
    #define LED_GREEN P2_4
    #define SLEEPTIMER  1200
    #define PLATFORM_CLOCK_FREQ 26
    
 #include "immedisplay.h"
 #include "immekeys.h"
 #include "immeio.h"
 //#include "pm.h"

#else
    #define SLEEPTIMER  1100
    #define PLATFORM_CLOCK_FREQ 24
void usbIntHandler(void) interrupt P2INT_VECTOR;
void p0IntHandler(void) interrupt P0INT_VECTOR;

    #if defined DONSDONGLES
        // CC1111 USB Dongle with breakout debugging pins (EMK?) - 24mhz
        #define LED_RED   P1_1
        #define LED_GREEN P1_1
        #define CC1111EM_BUTTON P1_2

    #elif defined CHRONOSDONGLE
        // CC1111 USB Chronos watch dongle - 24mhz
        #define LED_RED   P1_0
        #define LED_GREEN P1_0

    #elif defined CC2531
        // CC2531 USB 802.15.4 emk - 24mhz
        #define LED_RED   P1_0      //??
        #define LED_GREEN P1_0      //??
    #endif
#endif

#define LED     LED_GREEN


#define REALLYFASTBLINK()        { LED=1; sleepMillis(2); LED=0; sleepMillis(10); }
#define blink( on_cycles, off_cycles)  {LED=1; sleepMillis(on_cycles); LED=0; sleepMillis(off_cycles);}
#define BLOCK()     { while (1) { REALLYFASTBLINK() ; usbProcessEvents(); }  }
#define LE_WORD(x) ((x)&0xFF),((u8) (((u16) (x))>>8))

/* function declarations */
void sleepMillis(int ms);
void sleepMicros(int us);
void t1IntHandler(void) interrupt T1_VECTOR;  // interrupt handler should trigger on T1 overflow
void clock_init(void);
void io_init(void);
//void blink(u16 on_cycles, u16 off_cycles);
void blink_binary_baby_lsb(u16 num, char bits);
int strncmp(const char *s1, const char *s2, u16 n);
#endif
