#include "global.h"

#ifndef CC1111USBDEBUG_H
#define CC1111USBDEBUG_H

void debugEP0Req(u8 *pReq);
void debug(code u8* text);
void debughex(xdata u8 num);
void debughex16(xdata u16 num);
void debughex32(xdata u32 num);

#endif

