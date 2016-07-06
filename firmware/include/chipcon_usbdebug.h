#include "global.h"

#ifndef CC1111USBDEBUG_H
#define CC1111USBDEBUG_H

void debugEP0Req(u8 *pReq);
void debug(__code u8* text);
void debughex(__xdata u8 num);
void debughex16(__xdata u16 num);
void debughex32(__xdata u32 num);

#endif

