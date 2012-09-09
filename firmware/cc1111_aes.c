#include "cc1110-ext.h"
#include "cc1111_aes.h"
#include "cc1111rf.h"

/*************************************************************************************************
 * AES helpers                                                                                   *
 ************************************************************************************************/

// set the AES 128 bit key or IV
void setAES(__xdata u8* buf, u8 command, u8 mode)
{
    // wait for co-processor to be ready
    while(!(ENCCS & ENCCS_RDY))
        ;

    // start co-processor
    ENCCS = mode | command | ENCCS_ST;
    sendAESblock(buf, 16);

    // wait for co-processor to finish
    while(!(ENCCS & ENCCS_RDY))
        ;
}

// pad a buffer to multiple of 128 bits. caller must ensure
// enough space exists in buffer.
u16 padAES(__xdata u8* buf, u16 len)
{
    while(len % 16)
        buf[len++]= '\0';

    return len;
}

// encrypt a buffer
void encAES(__xdata u8* inbuf, __xdata u8* outbuf, u16 len, u8 mode)
{
    doAES(inbuf, outbuf, len, ENCCS_CMD_ENC, mode);
}

// decrypt a buffer
void decAES(__xdata u8* inbuf, __xdata u8* outbuf, u16 len, u8 mode)
{
    doAES(inbuf, outbuf, len, ENCCS_CMD_DEC, mode);
}

// process a buffer
void doAES(__xdata u8* inbuf, __xdata u8* outbuf, u16 len, u8 command, u8 mode)
{
    u16 bufp;
    u8 blocklen;

    switch(mode)
    {
        case ENCCS_MODE_CBC:
        case ENCCS_MODE_CBCMAC:
        case ENCCS_MODE_ECB:
            blocklen= 16;
            break;
        default:
            blocklen= 4;
            break;
    }
    for(bufp= 0 ; bufp < len ; bufp += blocklen)
    {
        // wait for co-processor to be ready
        while(!(ENCCS & ENCCS_RDY))
            ;

        // start co-processor
        // CBC-MAC is special - do last block as CBC to generate the final MAC
        // (note that all preceding blocks will be output '\0' filled)
        if((mode & ENCCS_MODE_CBCMAC) && bufp == len - 16)
            ENCCS = ENCCS_MODE_CBC | command | ENCCS_ST;
        else
            ENCCS = mode | command | ENCCS_ST;

        // send & receive data
        sendAESblock(inbuf + bufp, blocklen);
        // wait for crypto operation
        sleepMicros(40);
        getAESblock(outbuf + bufp, blocklen);
    }
    // wait for co-processor to finish
    while(!(ENCCS & ENCCS_RDY))
        ;
}

// write data to the co-processor
void sendAESblock(__xdata u8* buf, u8 len)
{
    while(len--)
        ENCDI= *(buf++);
}

// read data from the co-processor
void getAESblock(__xdata u8* buf, u8 len)
{
    while(len--)
        *(buf++)= ENCDO;
}

