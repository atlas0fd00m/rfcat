/*************************************************************************************************
 * AES helpers                                                                                   *
 ************************************************************************************************/

#include <cc1111.h>

void initAES(void);
void setAES(__xdata u8* buf, __xdata u8 command, __xdata u8 mode);
__xdata u16 padAES(__xdata u8* inbuf, __xdata u16 len);
void encAES(__xdata u8* inbuf, __xdata u8* outbuf, __xdata u16 len, __xdata u8 mode);
void decAES(__xdata u8* inbuf, __xdata u8* outbuf, __xdata u16 len, __xdata u8 mode);
void doAES(__xdata u8* inbuf, __xdata u8* outbuf, __xdata u16 len, __xdata u8 command, __xdata u8 mode);
