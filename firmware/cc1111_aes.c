#include "cc1110-ext.h"
#include "cc1111_aes.h"
#include "cc1111rf.h"

/*************************************************************************************************
 * AES helpers                                                                                   *
 ************************************************************************************************/

__xdata DMA_DESC * __xdata aesdmai, * __xdata aesdmao;
__xdata u8 aesdmachani, aesdmaarmi, aesdmachano, aesdmaarmo;

// initialise DMA
void initAES(void)
{
    // input to crypto co-processor
    // note that to save code memory we don't bother setting anything to 0
    // as it's initialised to 0 anyway
    aesdmachani= getDMA();                    // allocate a DMA channel
    aesdmaarmi= (DMAARM0 << aesdmachani);     // pre-calculate arming bit
    aesdmai= &dma_configs[aesdmachani];       // point our DMA descriptor at allocated channel descriptor
    aesdmai->destAddrH = 0xdf;                // ENCDI == 0xdfb1 - AES Input SFR
    aesdmai->destAddrL = 0xb1;
    aesdmai->lenL = 16;                       // always 128 bit operations
    aesdmai->trig = DMA_CFG0_TRIGGER_ENC_DW;  // trigger when co-processor requests data
    aesdmai->srcInc = 1;
    aesdmai->priority = 1;

    // output from crypto co-processor
    aesdmachano= getDMA();
    aesdmaarmo= (DMAARM0 << aesdmachano);
    aesdmao= &dma_configs[aesdmachano];
    aesdmao->srcAddrH = 0xdf;                 // ENCDO == 0xdfb2 - AES Output SFR
    aesdmao->srcAddrL = 0xb2;
    aesdmao->lenL = 16;
    aesdmao->trig = DMA_CFG0_TRIGGER_DNC_UP;  // trigger when co-processor signals upload ready
    aesdmao->destInc = 1;
    aesdmao->priority = 1;

    // set interrupt priority for group 4 to "11" (3 - highest)
    IP0 |= BIT4;
    IP1 |= BIT4;
}

// set the AES 128 bit key or IV
void setAES(__xdata u8* __xdata buf, __xdata u8 command, __xdata u8 mode)
{
    // wait for co-processor to be ready
    while(!(ENCCS & ENCCS_RDY))
        ;

    // prepare DMA for transfer
    aesdmai->srcAddrH = (u8) ((u16) buf >> 8);
    aesdmai->srcAddrL = (u8) ((u16) buf & 0xff);
    DMAARM |= aesdmaarmi;
    NOP();

    // start co-processor
    ENCCS = mode | command | ENCCS_ST;

    // wait for co-processor to finish
    while(!(ENCCS & ENCCS_RDY))
        ;
}

// pad a buffer to multiple of 16 bytes. caller must ensure
// enough space exists in buffer. returns new length.
__xdata u16 padAES(__xdata u8* __xdata buf, __xdata u16 len)
{
    while(len % 16)
        buf[len++]= '\0';

    return len;
}

// encrypt a buffer
void encAES(__xdata u8* __xdata inbuf, __xdata u8* __xdata outbuf, __xdata u16 len, __xdata u8 mode)
{
    doAES(inbuf, outbuf, len, ENCCS_CMD_ENC, mode);
}

// decrypt a buffer
void decAES(__xdata u8* __xdata inbuf, __xdata u8* __xdata outbuf, __xdata u16 len, __xdata u8 mode)
{
    doAES(inbuf, outbuf, len, ENCCS_CMD_DEC, mode);
}

// process a buffer
void doAES(__xdata u8* __xdata inbuf, __xdata u8* __xdata outbuf, __xdata u16 len, __xdata u8 command, __xdata u8 mode)
{
    __xdata u16 bufp;

    // wait for co-processor to be ready
    while(!(ENCCS & ENCCS_RDY))
        ;

    for(bufp= 0 ; bufp < len ; bufp += 16)
    {
        // prepare DMA for transfer
        aesdmai->srcAddrH = (u8) ((u16) (inbuf + bufp) >> 8);
        aesdmai->srcAddrL = (u8) ((u16) (inbuf + bufp) & 0xff);
        aesdmao->destAddrH = (u8) ((u16) (outbuf + bufp) >> 8);
        aesdmao->destAddrL = (u8) ((u16) (outbuf + bufp) & 0xff);
        DMAARM |= (aesdmaarmi | aesdmaarmo);
        NOP(); NOP();

        // start co-processor
        // CBC-MAC is special - do last block as CBC to generate the final MAC
        // (note that all preceding blocks do not generate any output, so only
        // the first output block is significant. care should also be taken not
        // to transmit any other blocks as they may contain original plaintext
        // e.g. if encryption is being done in-place).
        // for clarity: the output of CBC-MAC will always only be the initial
        // 128 bits of the output buffer, regardless of message length.
        if((mode & ENCCS_MODE_CBCMAC) && bufp == len - 16)
            ENCCS = ENCCS_MODE_CBC | command | ENCCS_ST;
        else
            ENCCS = mode | command | ENCCS_ST;

        // wait for co-processor to finish
        while(!(ENCCS & ENCCS_RDY))
            ;
    }
}

