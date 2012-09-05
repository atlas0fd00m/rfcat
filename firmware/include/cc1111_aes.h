/*************************************************************************************************
 * AES helpers                                                                                   *
 ************************************************************************************************/

#include <cc1111.h>

void setAES(__xdata u8* buf, u8 command);
u16 padAES(__xdata u8* inbuf, u16 len);
void encAES(__xdata u8* inbuf, __xdata u8* outbuf, u16 len);
void decAES(__xdata u8* inbuf, __xdata u8* outbuf, u16 len);
void doAES(__xdata u8* inbuf, __xdata u8* outbuf, u16 len, u8 command);
void getAESblock(__xdata u8* buf, u8 len);
void sendAESblock(__xdata u8* buf, u8 len);

