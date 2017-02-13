#ifndef GLOBAL_H
#define GLOBAL_H

#include "types.h"

#ifdef CC1111
  #include "cc1111.h"
#elif defined CC2511
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

// lastCode[0]: locations
#define LC_USB_INITUSB                  0x2
#define LC_MAIN_RFIF                    0xd
#define LC_USB_DATA_RESET_RESUME        0xa
#define LC_USB_RESET                    0xb
#define LC_USB_EP5OUT                   0xc

#define LC_RF_VECTOR                    0x10
#define LC_RFTXRX_VECTOR                0x11
#define LC_TXDATA_START                 0x12
#define LC_TXDATA_COMPLETED_FRAME       0x13
#define LC_TXDATA_COMPLETED_MESSAGE     0x14


// lastCode[1]: Errors
#define LCE_NO_ERROR                            0x0

#define LCE_USB_EP5_TX_WHILE_INBUF_WRITTEN      0x1
#define LCE_USB_EP0_SENT_STALL                  0x4
#define LCE_USB_EP5_OUT_WHILE_OUTBUF_WRITTEN    0x5
#define LCE_USB_EP5_LEN_TOO_BIG                 0x6
#define LCE_USB_EP5_GOT_CRAP                    0x7
#define LCE_USB_EP5_STALL                       0x8
#define LCE_USB_DATA_LEFTOVER_FLAGS             0x9

#define LCE_RF_RXOVF                            0x10
#define LCE_RF_TXUNF                            0x11
#define LCE_DROPPED_PACKET                      0x12
#define LCE_RFTX_NEVER_TX                       0x13
#define LCE_RFTX_NEVER_LEAVE_TX                 0x14
#define LCE_RF_MODE_INCOMPAT                    0x15
#define LCE_RF_BLOCKSIZE_INCOMPAT               0x16
#define LCE_RF_MULTI_BUFFER_NOT_INIT            0x17
#define LCE_RF_MULTI_BUFFER_NOT_FREE            0x18

// Return Codes
#define RC_NO_ERROR                             0x0
#define RC_TX_DROPPED_PACKET                    0xec
#define RC_TX_ERROR                             0xed
#define RC_RF_BLOCKSIZE_INCOMPAT                0xee
#define RC_RF_MODE_INCOMPAT                     0xef
#define RC_ERR_BUFFER_NOT_AVAILABLE             0xfe
#define RC_ERR_BUFFER_SIZE_EXCEEDED             0xff

// USB activities
#ifdef CHRONOSDONGLE
    #define USB_ENABLE_PIN              P1_1
#else
    #define USB_ENABLE_PIN              P1_0
#endif
#define NOP()                       __asm; nop; __endasm;

// USB data buffer
#define BUFFER_AVAILABLE		0x00
#define BUFFER_FILLING			0xff
#define ERR_BUFFER_SIZE_EXCEEDED        -1
#define ERR_BUFFER_NOT_AVAILABLE        -2

// Checks
#define IS_XOSC_STABLE()    (SLEEP & SLEEP_XOSC_S)

// AES
// defines for specifying desired crypto operations.
// AES_CRYPTO is in two halves: 
//    upper 4 bits mirror CC1111 mode (ENCCS_MODE_CBC etc.)
//    lower 4 bits are switches
// AES_CRYPTO[7:4]     ENCCS_MODE...
// AES_CRYPTO[3]       OUTBOUND 0 == OFF, 1 == ON
// AES_CRYPTO[2]       OUTBOUND 0 == Decrypt, 1 == Encrypt
// AES_CRYPTO[1]       INBOUND  0 == OFF, 1 == ON
// AES_CRYPTO[0]       INBOUND  0 == Decrypt, 1 == Encrypt
// bitfields
#define AES_CRYPTO_MODE          0xF0
#define AES_CRYPTO_OUT           0x0C
#define AES_CRYPTO_OUT_ENABLE    0x08
#define AES_CRYPTO_OUT_ON        (0x01 << 3)
#define AES_CRYPTO_OUT_OFF       (0x00 << 3)
#define AES_CRYPTO_OUT_TYPE      0x04
#define AES_CRYPTO_OUT_DECRYPT   (0x00 << 2)
#define AES_CRYPTO_OUT_ENCRYPT   (0x01 << 2)
#define AES_CRYPTO_IN            0x03
#define AES_CRYPTO_IN_ENABLE     0x02
#define AES_CRYPTO_IN_ON         (0x01 << 1)
#define AES_CRYPTO_IN_OFF        (0x00 << 1)
#define AES_CRYPTO_IN_TYPE       0x01
#define AES_CRYPTO_IN_DECRYPT    (0x00 << 0)
#define AES_CRYPTO_IN_ENCRYPT    (0x01 << 0)
#define AES_CRYPTO_NONE          0x00
// flags
#define AES_DISABLE              0x00
#define AES_ENABLE               0x01
#define AES_DECRYPT              0x00
#define AES_ENCRYPT              0x01

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
void usbIntHandler(void) __interrupt P2INT_VECTOR;
void p0IntHandler(void) __interrupt P0INT_VECTOR;

    #if defined DONSDONGLES
        // CC1111 USB Dongle with breakout debugging pins (EMK?) - 24mhz
        #define LED_RED   P1_1
        #define LED_GREEN P1_1
        #define CC1111EM_BUTTON P1_2

    #elif defined YARDSTICKONE
        #define LED1          P1_1
        #define LED_GREEN     P1_1
        #define LED2          P1_2
        #define LED_RED       P1_2
        #define LED3          P1_3
        #define LED_YELLOW    P1_3
        #define TX_AMP_EN     P2_0
        #define RX_AMP_EN     P2_4
        #define AMP_BYPASS_EN P2_3

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
#define ASCII_LONG(x) '0' + x / 1000 % 10,'0' + x / 100 % 10, '0' + x / 10 % 10, '0' + x % 10
#define QUOTE(x) XQUOTE(x)
#define XQUOTE(x) #x

/* function declarations */
void sleepMillis(int ms);
void sleepMicros(int us);
void t1IntHandler(void) __interrupt T1_VECTOR;  // interrupt handler should trigger on T1 overflow
void clock_init(void);
void io_init(void);
//void blink(u16 on_cycles, u16 off_cycles);
void blink_binary_baby_lsb(u16 num, char bits);
int strncmp(const char * __xdata s1, const char * __xdata s2, u16 n);
#endif
