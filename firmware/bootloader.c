#include "global.h"
#include "bootloader.h"

void run_bootloader(void)
{
    // check that our bootloader is present & if so, tell it we want it to run...
    // we use the otherwise unused I2S SFRs as semaphores. 
    if(I2SCLKF0 == 0xf0 && I2SCLKF1 == 0x0d)
        I2SCLKF2= 0x69;
    // disable all interrupts
    EA = 0;
    IEN0 = IEN1 = IEN2 = 0;
    usb_down();
    // reset USB controller
    SLEEP &= ~SLEEP_USB_EN;
    // abort and disarm all DMA
    DMAARM = 0x9F;
    LED = 0;
    // Jump to bootloader (if there isn't one this will just cause a reset)
    __asm
      ljmp 0x00
    __endasm;
}
