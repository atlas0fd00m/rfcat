#include "cc1111rf.h"
#include "cc1111_aes.h"
#include "chipcon_dma.h"
#include "global.h"


#ifdef IMME
    #include "immefont.h"
#else
 #ifdef VIRTUAL_COM
    #include "cc1111.h"
    #include "cc1111_vcom.h"
 #else
    #include "cc1111usb.h"
 #endif
#endif

/*************************************************************************************************
 * welcome to the cc1111usb application.
 * this lib was designed to be the basis for your usb-app on the cc1111 radio.  hack fun!
 *
 * 
 * best way to start is to look over the library and get a little familiar with it.
 * next, put code as follows:
 * * any initialization code that should happen at power up goes in appMainInit()
 * * the main application loop code should go in appMainLoop()
 * * usb interface code should go into appHandleEP5.  this includes a switch statement for any 
 *      verbs you want to create between the client on this firmware.
 *
 * if you should need to change anything about the USB descriptors, do your homework!  particularly
 * keep in mind, if you change the IN or OUT max packetsize, you *must* change it in the 
 * EPx_MAX_PACKET_SIZE define, the desciptor definition (be sure to get the right one!) and should 
 * correspond to the setting of MAXI and MAXO.
 * 
 * */


#define APP_NIC 0x42
#define NIC_RECV 0x1
#define NIC_XMIT 0x2
#define SNIFF_RECV 0x1

/*************************************************************************************************
 * Application Code - these first few functions are what should get overwritten for your app     *
 ************************************************************************************************/

__xdata u32 recvCnt;

/* appMainInit() is called *before Interrupts are enabled* for various initialization things. */
void appMainInit(void)
{
    recvCnt = 0;

    RxMode();
}

/* appMain is the application.  it is called every loop through main, as does the USB handler code.
 * do not block if you want USB to work.                                                           */
void appMainLoop(void)
{
    __xdata u8 processbuffer;

#ifdef IMME
    immeLCDUpdateState();
    //SSN=LOW;
    //drawhex(6, 0, MARCSTATE);
    //drawhex(6,10, rfif);
    //SSN=HIGH;

#endif
    if (rfif)
    {
        lastCode[0] = 0xd;
        //IEN2 &= ~IEN2_RFIE;

        if(rfif & RFIF_IRQ_DONE)
        {
            processbuffer = !rfRxCurrentBuffer;
            if(rfRxProcessed[processbuffer] == RX_UNPROCESSED)
            {   // we've received a packet.  deliver it.
#ifdef IMME
                LED_RED = !LED_RED;
                ++recvCnt;
                immeLCDShowPacket();
#else
                txdata(APP_NIC, SNIFF_RECV, (u8)rfrxbuf[processbuffer][0], (u8*)&rfrxbuf[processbuffer]);
#endif  // imme
                /* Set receive buffer to processed so it can be used again */
                rfRxProcessed[processbuffer] = RX_PROCESSED;
            }
        }

        rfif = 0;
        //IEN2 |= IEN2_RFIE;
    }
}

#ifdef IMME
void immeLCDInitialState(void)
    /* SSN=LOW already */
{
    drawstr(0,0, "IMME SNIFF v0.1");
}
#else   // not an IMME

/* appHandleEP5 gets called when a message is received on endpoint 5 from the host.  this is the 
 * main handler routine for the application as endpoint 0 is normally used for system stuff.
 *
 * important things to know:
 *  * your data is in ep5.OUTbuf, the length is ep5.OUTlen, and the first two bytes are
 *      going to be \x40\xe0.  just craft your application to ignore those bytes, as i have ni
 *      puta idea what they do.  
 *  * transmit data back to the client-side app through txdatai().  this function immediately 
 *      xmits as soon as any previously transmitted data is out of the buffer (ie. it blocks 
 *      while (ep5.flags & EP_INBUF_WRITTEN) and then transmits.  this flag is then set, and 
 *      cleared by an interrupt when the data has been received on the host side.                */
int appHandleEP5()
{   // not used by VCOM
#ifndef VIRTUAL_COM
    __xdata u8 *ptr = &ep5.OUTbuf[0];

    switch (ep5.OUTapp)
    {
        default:
    }
    ep5.flags &= ~EP_OUTBUF_WRITTEN;                       // this allows the OUTbuf to be rewritten... it's saved until now.
#endif
    return 0;
}

/* in case your application cares when an OUT packet has been completely received on EP0.       */
void appHandleEP0OUTdone(void)
{
}

/* called each time a usb OUT packet is received */
void appHandleEP0OUT(void)
{
#ifndef VIRTUAL_COM
    u16 loop;
    __xdata u8* dst;
    __xdata u8* src;

    // we are not called with the Request header as is appHandleEP0.  this function is only called after an OUT packet has been received,
    // which triggers another usb interrupt.  the important variables from the EP0 request are stored in ep0req, ep0len, and ep0value, as
    // well as ep0.OUTlen (the actual length of ep0.OUTbuf, not just some value handed in).

    // for our purposes, we only pay attention to single-packet transfers.  in more complex firmwares, this may not be sufficient.
    switch (ep0req)
    {
        case 1:     // poke
            
            src = (__xdata u8*) &ep0.OUTbuf[0];
            dst = (__xdata u8*) ep0value;

            for (loop=ep0.OUTlen; loop>0; loop--)
            {
                *dst++ = *src++;
            }
            break;
    }

    // must be done with the buffer by now...
    ep0.flags &= ~EP_OUTBUF_WRITTEN;
#endif  // not VIRTUAL_COM
}

/* this function is the application handler for endpoint 0.  it is called for all VENDOR type    *
 * messages.  currently it implements a simple debug, ping, and peek functionality.              *
 * data is sent back through calls to either setup_send_ep0 or setup_sendx_ep0 for xdata vars    *
 * theoretically you can process stuff without the IN-direction bit, but we've found it is better*
 * to handle OUT packets in appHandleEP0OUTdone, which is called when the last packet is complete*/
int appHandleEP0(USB_Setup_Header* pReq)
{
#ifdef VIRTUAL_COM
    pReq = 0;
#else
    if (pReq->bmRequestType & USB_BM_REQTYPE_DIRMASK)       // IN to host
    {
        switch (pReq->bRequest)
        {
            case 0:
                setup_send_ep0(&lastCode[0], 2);
                break;
            case 1:
                setup_sendx_ep0((__xdata u8*)USBADDR, 40);
                break;
            case 2:
                setup_sendx_ep0((__xdata u8*)pReq->wValue, pReq->wLength);
                break;
            case 3:     // ping
                setup_send_ep0((u8*)pReq, pReq->wLength);
                break;
            case 4:     // ping
                setup_sendx_ep0((__xdata u8*)&ep0.OUTbuf[0], 16);//ep0.OUTlen);
                break;
        }
    }
#endif  // not VIRTUAL_COM
    return 0;
}

#endif //  not IMME

/*************************************************************************************************
 *  here begins the initialization stuff... this shouldn't change much between firmwares or      *
 *  devices.                                                                                     *
 *************************************************************************************************/

static void appInitRf(void)
{
    IOCFG2      = 0x00;
    IOCFG1      = 0x00;
    IOCFG0      = 0x00;
    SYNC1       = 0x0c;
    SYNC0       = 0x4e;
    PKTLEN      = 0xff;
    PKTCTRL1    = 0x20;//0x40; // PQT threshold  - was 0x00
    PKTCTRL0    = 0x00;//0x01; // Fixed LEN:0, Variable LEN:1, CRC:4
    ADDR        = 0x00;
    CHANNR      = 0x00;
#ifdef IMME
    //PKTCTRL1    = 0xe5;  - has PQT/SYNC/blah and ADDRESS CHECK and APPEND_STATUS
    //PKTCTRL0    = 0x05;  - has CRC enabled.
    FREQ2       = 0x21;
    FREQ1       = 0x65;//0x71;
    FREQ0       = 0x6a;//0x7c;
    FSCTRL1     = 0x06;
    FSCTRL0     = 0x00;
#else
    FREQ2       = 0x24;
    FREQ1       = 0x3a;
    FREQ0       = 0xf1;
    FSCTRL1     = 0x06;
    FSCTRL0     = 0x00;
#endif
    MDMCFG4     = 0xca;
    MDMCFG3     = 0x83;//0xa3;//0x83;
    MDMCFG2     = 0x04;//0x03;//0x10;  // SYNC_MODE - 000-nopreamble/syncbits...111-30/32+carriersense
    MDMCFG1     = 0x23;//0x22;
    MDMCFG0     = 0x11;//0xf8;
    DEVIATN     = 0x35;
    MCSM2       = 0x07;             // RX_TIMEOUT
    MCSM1       = 0x3f;//0x30;             // CCA_MODE RSSI below threshold unless currently recvg pkt - always end up in RX mode
    MCSM0       = 0x18;             // fsautosync when going from idle to rx/tx/fstxon
    FOCCFG      = 0x16;
    BSCFG       = 0x6c;
    AGCCTRL2    = 0x43;
    AGCCTRL1    = 0x40;
    AGCCTRL0    = 0x91;
    FREND1      = 0x56;
    FREND0      = 0x10;
    FSCAL3      = 0xe9;
    FSCAL2      = 0x2a;
    FSCAL1      = 0x00;
    FSCAL0      = 0x1f;
    TEST2       = 0x81; // low data rates, increased sensitivity - was 0x88
    TEST1       = 0x35; // always 0x31 in tx-mode, for low data rates, increased sensitivity - was 0x31
    TEST0       = 0x09;
    PA_TABLE0   = 0x50;


#ifndef RADIO_EU
    // this is the NA radio freqs 902-928MHz
    PA_TABLE0   = 0x8e;
#ifdef IMME
    FREQ2       = 0x22;
    FREQ1       = 0xb1;
    FREQ0       = 0x3b;
#else
    FREQ2       = 0x25;
    FREQ1       = 0x95;
    FREQ0       = 0x55;
#endif
#endif

}
/*************************************************************************************************
 * main startup code                                                                             *
 *************************************************************************************************/
void initBoard(void)
{
    clock_init();
    io_init();
}


void main (void)
{
start:
    initBoard();
    initDMA();  // do this early so peripherals that use DMA can allocate channels correctly
    initAES();
#ifdef IMME
    initIMME();
#else
    initUSB();
#endif
    blink(300,300);

    init_RF();
    appMainInit();

    usb_up();

    /* Enable interrupts */
    EA = 1;

    while (1)
    {  
#ifdef IMME
        poll_keyboard();
#else
        usbProcessEvents();
#endif
        //  LED_RED = !LED_RED;
        appMainLoop();
    }

}

