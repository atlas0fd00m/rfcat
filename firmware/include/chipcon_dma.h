#ifndef CHIPCON_DMA_H
#define CHIPCON_DMA_H

#include "types.h"
#include "cc1111.h"
#include "cc1111rf.h"

// define number of required DMA channels here
// RF (maybe)
// USB
// AES x 2
#ifdef RFDMA
#define DMA_CHANNELS    4
#else
#define DMA_CHANNELS    3
#endif

// prototypes

void initDMA(void);
u8 getDMA(void);

// defines

typedef union
{
    u16 ui16;
    u8  ui8[2];
} U16_U8;

// sdcc requires this bit ordering.  this struct appears differently from the IAR version, which uses "#pragma bitfields=reversed"
typedef struct DMA_DESC_S {
    uint8 srcAddrH;
    uint8 srcAddrL;
    uint8 destAddrH;
    uint8 destAddrL;
    uint8 lenH      : 5;
    uint8 vlen      : 3;
    uint8 lenL      : 8;
    uint8 trig      : 5;
    uint8 tMode     : 2;
    uint8 wordSize  : 1;

    uint8 priority  : 2;
    uint8 m8        : 1;
    uint8 irqMask   : 1;
    uint8 destInc   : 2;
    uint8 srcInc    : 2;
} DMA_DESC;

#define DMA_LEN_HIGH_VLEN_MASK     (7 << 5)
#define DMA_LEN_HIGH_VLEN_LEN      (0 << 5)
#define DMA_LEN_HIGH_VLEN_PLUS_1   (1 << 5)
#define DMA_LEN_HIGH_VLEN      (2 << 5)
#define DMA_LEN_HIGH_VLEN_PLUS_2   (3 << 5)
#define DMA_LEN_HIGH_VLEN_PLUS_3   (4 << 5)
#define DMA_LEN_HIGH_MASK      (0x1f)
extern __xdata DMA_DESC dma_configs[DMA_CHANNELS];
 
#define DMA_CFG0_WORDSIZE_8        (0 << 7)
#define DMA_CFG0_WORDSIZE_16       (1 << 7)
#define DMA_CFG0_TMODE_MASK        (3 << 5)
#define DMA_CFG0_TMODE_SINGLE      (0 << 5)
#define DMA_CFG0_TMODE_BLOCK       (1 << 5)
#define DMA_CFG0_TMODE_REPEATED_SINGLE (2 << 5)
#define DMA_CFG0_TMODE_REPEATED_BLOCK  (3 << 5)
#define DMA_CFG0_TRIGGER_ENC_DW	    29
#define DMA_CFG0_TRIGGER_DNC_UP	    30


#endif
