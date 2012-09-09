#include "cc1110-ext.h"
#include "chipcon_dma.h"
#include "global.h"

// Because the CC1111 only has two sets of SFRs for pointing at DMA configs (DMA0CFG for DMA channel 0
// and DMA1CFG for DMA channels 1-4), 1-4 must be allocated in contiguous memory so the DMA controller
// can find them based on their offsets. We therefore allocate memory for the desired number of channels
// here and then point at them in the main code. For consistency we include channel 0 even though this
// isn't strictly necessary. 
//
// e.g.
//
// xdata u8 my_dma_usb_chan;
// xdata DMA_DESC *my_dma_usb_desc;
//
// my_dma_usb_chan= getDMA();
// my_dma_usb_desc= &dma_configs[my_dma_usb_chan];
// my_dma_usb_desc->srcAddrH= 0xde;     //USBF5 == 0xde2a
// my_dma_usb_desc->srcAddrL= 0x2a;
// etc.
//

xdata DMA_DESC dma_configs[DMA_CHANNELS];
xdata dma_channels= 0;

void initDMA(void)
{
    if(DMA_CHANNELS)
    {
        DMA0CFGH = ((u16)(&dma_configs[0]))>>8;
        DMA0CFGL = ((u16)(&dma_configs[0]))&0xff;
    }
    if(DMA_CHANNELS > 1)
    {
        DMA1CFGH = ((u16)(&dma_configs[1]))>>8;
        DMA1CFGL = ((u16)(&dma_configs[1]))&0xff;
    }
}

// allocate next DMA channel. return 0xff if none left.
u8 getDMA(void)
{
    if(dma_channels == DMA_CHANNELS)
        return 0xff;
    else
        return dma_channels++;
}
