/*************************************************************************************************
 * AES helpers                                                                                   *
 ************************************************************************************************/

#include <cc1111.h>

void initAES(void);
void setAES(__xdata u8* buf, u8 command, u8 mode);
u16 padAES(__xdata u8* inbuf, u16 len);
void encAES(__xdata u8* inbuf, __xdata u8* outbuf, u16 len, u8 mode);
void decAES(__xdata u8* inbuf, __xdata u8* outbuf, u16 len, u8 mode);
void doAES(__xdata u8* inbuf, __xdata u8* outbuf, u16 len, u8 command, u8 mode);
