#ifndef CC1111RF_H
#define CC1111RF_H

#include "cc1111.h"
#include "global.h"

// use DMA for RF?
//#define RFDMA  - nope.  this has now died for InfiniteMode TX/RX.  we need to 
//                  switch buffers mid-stream

#define DMA_CFG_SIZE 8
// BUFFER size must match RF_MAX_RX_BLOCK defined in rflib/cc1111client.py 
#define BUFFER_SIZE 512
#define BUFFER_AMOUNT 2

#define PKTCTRL0_LENGTH_CONFIG_INF        (0x02)
#define RF_MAX_TX_BLOCK                   (u16) 255

#define RSSI_TIMEOUT_US 1500

#define RF_STATE_RX 1
#define RF_STATE_TX 2
#define RF_STATE_IDLE 3

#define RF_SUCCESS 0

#define RF_DMA_VLEN_1       1<<5
#define RF_DMA_VLEN_3       4<<5
#define RF_DMA_LEN          0xfe
#define RF_DMA_WORDSIZE16   1<<7
#define RF_DMA_WORDSIZE8    0<<7
#define RF_DMA_TMODE        0
#define RF_DMA_TRIGGER      19
#define RF_DMA_DST_INC      1<<4
#define RF_DMA_SRC_INC      1<<6
#define RF_DMA_IRQMASK_DI   0<<3
#define RF_DMA_IRQMASK_EN   1<<3
#define RF_DMA_M8           0<<2
#define RF_DMA_M7           1<<2
#define RF_DMA_PRIO_LOW     0<<1
#define RF_DMA_PRIO_NOR     1<<1
#define RF_DMA_PRIO_HIGH    1<<2

#define FIRST_BUFFER 0
#define SECOND_BUFFER 1
#define RX_UNPROCESSED 0
#define RX_PROCESSED 1

/* Type for registers:
    NORMAL: registers are configured by client
    RECV: registers are set for receive
    XMIT: registers are set for transmit
*/
typedef enum{NORMAL,RECV,XMIT} register_e;

/* Rx buffers */
extern volatile __xdata u8 rfRxCurrentBuffer;
extern volatile __xdata u8 rfrxbuf[BUFFER_AMOUNT][BUFFER_SIZE];
extern volatile __xdata u16 rfRxCounter[BUFFER_AMOUNT];
extern volatile __xdata u8 rfRxProcessed[BUFFER_AMOUNT];
extern volatile __xdata u8 rfRxInfMode;
extern volatile __xdata u16 rfRxTotalRXLen;
extern volatile __xdata u16 rfRxLargeLen;
/* Tx buffers */
extern volatile __xdata u8 *__xdata rftxbuf;
extern volatile __xdata u8 rfTxBufCount;
extern volatile __xdata u8 rfTxCurBufIdx;
extern volatile __xdata u16 rfTxCounter;
extern volatile __xdata u16 rfTxRepeatCounter;
extern volatile __xdata u16 rfTxBufferEnd;
extern volatile __xdata u16 rfTxRepeatLen;
extern volatile __xdata u16 rfTxRepeatOffset;
extern volatile __xdata u16 rfTxTotalTXLen;
extern volatile __xdata u8 rfTxInfMode;

extern volatile __xdata u16 rf_MAC_timer;
extern volatile __xdata u16 rf_tLastRecv;

// AES
extern volatile __xdata u8 rfAESMode;

extern volatile __xdata u8 rfAmpMode;
extern __xdata u16 txTotal; // debugger

extern volatile u8 rfif;

void rfTxRxIntHandler(void) __interrupt RFTXRX_VECTOR; // interrupt handler should transmit or receive the next byte
void rfIntHandler(void) __interrupt RF_VECTOR; // interrupt handler should trigger on rf events

// set semi-permanent states
void RxMode(void);          // set defaults to return to RX and calls RFRX
void TxMode(void);          // set defaults to return to TX and calls RFTX
void IdleMode(void);        // set defaults to return to IDLE and calls RFOFF

// set transient RF mode (like.  NOW!)
#ifdef YARDSTICKONE
// enable or disable front-end amplifiers on YARD Stick One
#define SET_TX_AMP_ON do { TX_AMP_EN = 1; RX_AMP_EN = 0; AMP_BYPASS_EN = 0; } while (0)
#define SET_RX_AMP_ON do { TX_AMP_EN = 0; RX_AMP_EN = 1; AMP_BYPASS_EN = 0; } while (0)
#define SET_AMP_OFF do { TX_AMP_EN = 0; RX_AMP_EN = 0; AMP_BYPASS_EN = 1; } while (0)
#define SET_TX_AMP do { TX_AMP_EN = rfAmpMode; RX_AMP_EN = 0; AMP_BYPASS_EN = rfAmpMode^1; } while (0)
#define SET_RX_AMP do { TX_AMP_EN = 0; RX_AMP_EN = rfAmpMode; AMP_BYPASS_EN = rfAmpMode^1; } while (0)
// set RF mode to RX and wait until MARCSTATE shows it's there
#define RFTX do { SET_TX_AMP; RFST = RFST_STX; while ((MARCSTATE) != MARC_STATE_TX); } while (0)
// set RF mode to TX and wait until MARCSTATE shows it's there
#define RFRX do { SET_RX_AMP; RFST = RFST_SRX; while ((MARCSTATE) != MARC_STATE_RX); } while (0)
// set RF mode to CAL and wait until MARCSTATE shows it's done (in IDLE)
#define RFCAL do { SET_AMP_OFF; RFST=RFST_SCAL; while ((MARCSTATE) != MARC_STATE_IDLE); } while (0)
// set RF mode to IDLE and wait until MARCSTATE shows it's there
#define RFOFF do { SET_AMP_OFF; RFST=RFST_SIDLE; while ((MARCSTATE) != MARC_STATE_IDLE); } while (0)
#else
// set RF mode to RX and wait until MARCSTATE shows it's there
#define RFTX do { RFST = RFST_STX; while ((MARCSTATE) != MARC_STATE_TX); } while (0)
// set RF mode to TX and wait until MARCSTATE shows it's there
#define RFRX do { RFST = RFST_SRX; while ((MARCSTATE) != MARC_STATE_RX); } while (0)
// set RF mode to CAL and wait until MARCSTATE shows it's done (in IDLE)
#define RFCAL do { RFST = RFST_SCAL; while ((MARCSTATE) != MARC_STATE_IDLE); } while (0)
// set RF mode to IDLE and wait until MARCSTATE shows it's there
#define RFOFF do { RFST = RFST_SIDLE; while ((MARCSTATE) != MARC_STATE_IDLE); } while (0)
#endif


int waitRSSI(void);

u8 transmit(__xdata u8* __xdata buf, __xdata u16 len, __xdata u16 repeat, __xdata u16 offset);   // sends data out the radio using the current RF settings
void appInitRf(void);       // in application.c  (provided by the application and called from init_RF()
void init_RF(void);
void byte_shuffle(__xdata u8* __xdata buf, __xdata u16 len, __xdata u16 offset);
void startRX(void);
void resetRFSTATE(void);

typedef struct MAC_DATA_s 
{
    u8 mac_state;
    // MAC parameters (FIXME: make this all cc1111fhssmac.c/h?)
    u16 MAC_threshold;              // when the T2 clock as overflowed this many times, change channel
    u16 MAC_timer;                  // this tracks how many times it's overflowed (really?  32-bits for these two?!?)
    u16 NumChannels;                // in case of multiple paths through the available channels 
    u16 NumChannelHops;             // total number of channels in pattern (>= g_MaxChannels)
    u16 curChanIdx;                 // indicates current channel index of the hopping pattern
    u16 tLastStateChange;
    u16 tLastHop;
    u16 desperatelySeeking;         // this should be unnecessary, and should instead use mac_state?
    u8  txMsgIdx;
    u8  txMsgIdxDone;
    u16 synched_chans;
} MAC_DATA_t;

extern __xdata MAC_DATA_t macdata;

#endif
