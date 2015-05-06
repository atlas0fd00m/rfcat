#include "chipcon_usb.h"

/*************************************************************************************************
 * debug stuff.  slows executions.                                                               *
 ************************************************************************************************/
/* sends a debug message up to the python code to be spit out on stderr */
void debugx(__xdata u8* __xdata  text)
{
    u16 len = 0;
    __xdata u8* __xdata  ptr = text;
    while (*ptr++ != 0)
        len ++;
    txdata(0xfe, 0xf0, len, (__xdata u8*)text);
}

void debug(__code u8* __xdata  text)
{
    u16 len = 0;
    __code u8* __xdata  ptr = text;
    while (*ptr++ != 0)
        len ++;
    txdata(0xfe, 0xf0, len, (__xdata u8*)text);
}

void debughex(__xdata u8 num)
{
    txdata(0xfe, DEBUG_CMD_HEX, 1, (__xdata u8*)&num);
}

void debughex16(__xdata u16 num)
{
    txdata(0xfe, DEBUG_CMD_HEX16, 2, (__xdata u8*)&num);
}

void debughex32(__xdata u32 num)
{
    txdata(0xfe, DEBUG_CMD_HEX32, 4, (__xdata u8*)&num);
}
 

