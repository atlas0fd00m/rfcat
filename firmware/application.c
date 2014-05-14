#include "cc1111rf.h"
#include "cc1111_aes.h"
#include "chipcon_dma.h"
#include "global.h"
#include "nic.h"

#ifdef VIRTUAL_COM
    #include "cc1111_vcom.h"

    // FIXME: this belongs elsewhere...
    #define STATUS_TAG 0
    #define STATUS_LEN 1
    #define STATUS_VAL 2
    
    #define TAG_MODE    0x01 /* Value is mode, IDLE,RX,TX */
    #define TAG_SEND    0x02 /* Value is what to send */
    #define TAG_STATUS  0x03 /* Value is the status value want to know, for example RSSI */
    #define TAG_REG     0x04 /* Register values, value as register=value */

    #define TLV_MAX_DATA 50    

    typedef struct
    {
        u8 uiTag;
        u8 uiLength;
        u8 uiData[TLV_MAX_DATA];
    } tlv_t;

    static __xdata tlv_t tlv_recv,tlv_send;
    static __xdata uiDataPtr = 0;
    static __xdata u8 uiStatus = STATUS_TAG;
#else
    #include "chipcon_usb.h"
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
 * * usb interface code: register a callback using register_Cb_ep5() as demonstrated in appMainInit()
 *
 * if you should need to change anything about the USB descriptors, do your homework!  particularly
 * keep in mind, if you change the IN or OUT max packetsize, you *must* change it in the 
 * EPx_MAX_PACKET_SIZE define, and should correspond to the setting of MAXI and MAXO.
 * 
 * */




/*************************************************************************************************
 * Application Code - these first few functions are what should get overwritten for your app     *
 ************************************************************************************************/

__xdata u32 loopCnt;
__xdata u8 xmitCnt;

int appHandleEP5(void);

/* appMainInit() is called *before Interrupts are enabled* for various initialization things. */
void appMainInit(void)
{
    //registerCb_ep0Vendor( appHandleEP0Vendor );
    registerCb_ep5( appHandleEP5 );

    loopCnt = 0;
    xmitCnt = 1;

    RxMode();
}

/* appMain is the application.  it is called every loop through main, as does the USB handler code.
 * do not block if you want USB to work.                                                           */
void appMainLoop(void)
{
    //  this is part of the NIC code to handle received RF packets and may be replaced/modified //
    __xdata u8 processbuffer;

    if (rfif)
    {
        lastCode[0] = LC_MAIN_RFIF;
        IEN2 &= ~IEN2_RFIE;

        if(rfif & RFIF_IRQ_DONE)
        {
            processbuffer = !rfRxCurrentBuffer;
            if(rfRxProcessed[processbuffer] == RX_UNPROCESSED)
            {
                if (PKTCTRL0&1)     // variable length packets have a leading "length" byte, let's skip it
                    txdata(APP_NIC, NIC_RECV, (u8)rfrxbuf[processbuffer][0], (u8*)&rfrxbuf[processbuffer][1]);
                else
                    txdata(APP_NIC, NIC_RECV, PKTLEN, (u8*)&rfrxbuf[processbuffer]);

                // Set receive buffer to processed so it can be used again //
                rfRxProcessed[processbuffer] = RX_PROCESSED;
            }
        }

        rfif = 0;
        IEN2 |= IEN2_RFIE;
    }
    //////////////////////////////////////////////////////////////////////////////////////////////
}

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

    switch (ep5.OUTcmd)
    {
        /*
        case CMD_RFMODE:
            switch (*ptr++)
            {
                case RF_STATE_RX:

                    RxMode();
                    break;
                case RF_STATE_IDLE:
                    IdleMode();
                    break;
                case RF_STATE_TX:
                    transmit(ptr, len);
                    break;
            }
            txdata(app,cmd,len,ptr);
            break;
            */
        default:
            break;
    }
    ep5.flags &= ~EP_OUTBUF_WRITTEN;                       // this allows the OUTbuf to be rewritten... it's saved until now.
#endif
    return 0;
}

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
    PKTCTRL1    = 0x40; // PQT threshold  - was 0x00
    PKTCTRL0    = 0x01;
    ADDR        = 0x00;
    CHANNR      = 0x00;
    FSCTRL1     = 0x06;
    FSCTRL0     = 0x00;
    FREQ2       = 0x24;
    FREQ1       = 0x3a;
    FREQ0       = 0xf1;
    MDMCFG4     = 0xca;
    MDMCFG3     = 0xa3;
    MDMCFG2     = 0x03;
    MDMCFG1     = 0x23;
    MDMCFG0     = 0x11;
    DEVIATN     = 0x36;
    MCSM2       = 0x07;             // RX_TIMEOUT
    MCSM1       = 0x3f;             // CCA_MODE RSSI below threshold unless currently recvg pkt - always end up in RX mode
    MCSM0       = 0x18;             // fsautosync when going from idle to rx/tx/fstxon
    FOCCFG      = 0x17;
    BSCFG       = 0x6c;
    AGCCTRL2    = 0x03;
    AGCCTRL1    = 0x40;
    AGCCTRL0    = 0x91;
    FREND1      = 0x56;
    FREND0      = 0x10;
    FSCAL3      = 0xe9;
    FSCAL2      = 0x2a;
    FSCAL1      = 0x00;
    FSCAL0      = 0x1f;
    TEST2       = 0x88; // low data rates, increased sensitivity - was 0x88
    TEST1       = 0x31; // always 0x31 in tx-mode, for low data rates, increased sensitivity - was 0x31
    TEST0       = 0x09;
    PA_TABLE0   = 0x50;


#ifndef RADIO_EU
    //PKTCTRL1    = 0x04;             // APPEND_STATUS
    //PKTCTRL1    = 0x40;             // PQT threshold
    //PKTCTRL0    = 0x01;             // VARIABLE LENGTH, no crc, no whitening
    //PKTCTRL0    = 0x00;             // FIXED LENGTH, no crc, no whitening
    FSCTRL1     = 0x0c;             // Intermediate Frequency
    //FSCTRL0     = 0x00;
    FREQ2       = 0x25;
    FREQ1       = 0x95;
    FREQ0       = 0x55;
    //MDMCFG4     = 0x1d;             // chan_bw and drate_e
    //MDMCFG3     = 0x55;             // drate_m
    //MDMCFG2     = 0x13;             // gfsk, 30/32+carrier sense sync 
    //MDMCFG1     = 0x23;             // 4-preamble-bytes, chanspc_e
    //MDMCFG0     = 0x11;             // chanspc_m
    //DEVIATN     = 0x63;
    //FOCCFG      = 0x1d;             
    //BSCFG       = 0x1c;             // bit sync config
    //AGCCTRL2    = 0xc7;
    //AGCCTRL1    = 0x00;
    //AGCCTRL0    = 0xb0;
    FREND1      = 0xb6;
    FREND0      = 0x10;
    FSCAL3      = 0xea;
    FSCAL2      = 0x2a;
    FSCAL1      = 0x00;
    FSCAL0      = 0x1f;
    //TEST2       = 0x88;
    //TEST1       = 0x31;
    //TEST0       = 0x09;
    //PA_TABLE0   = 0x83;
#endif

#ifdef CC2511
    IOCFG2      = 0x2e;
    IOCFG1      = 0x00;
    IOCFG0      = 0x06;
    //PKTCTRL1    = 0x04; // PQT threshold  - was 0x00
    PKTCTRL0    = 0x08; // FLEN.  for VLEN use |1 (ie.  FLEN=00, VLEN=01)
    FSCTRL1     = 0x0b;
    FSCTRL0     = 0x00;
    FREQ2       = 0x65;
    FREQ1       = 0x60;
    FREQ0       = 0x00;
    MDMCFG4     = 0x68;
    MDMCFG3     = 0xb5;
    MDMCFG2     = 0x83;
    MDMCFG1     = 0x23;
    MDMCFG0     = 0x11;
    DEVIATN     = 0x45;
    MCSM0       = 0x14;             // fsautosync when going from idle to rx/tx/fstxon
    FOCCFG      = 0x16;
    BSCFG       = 0x6c;
    AGCCTRL2    = 0x43;
    AGCCTRL1    = 0x40;
    AGCCTRL0    = 0x91;
    FREND1      = 0x56;
    FREND0      = 0x10;
    FSCAL3      = 0xa9;
    FSCAL2      = 0x0a;
    FSCAL1      = 0x00;
    FSCAL0      = 0x11;
#endif

}

/*************************************************************************************************
 * main startup code                                                                             *
 *************************************************************************************************/
void initBoard(void)
{
    // in global.c
    clock_init();
    io_init();
}


void main (void)
{
    initBoard();
    initDMA();  // do this early so peripherals that use DMA can allocate channels correctly
    initAES();
    initUSB();
    init_RF();
    appMainInit();

    /* Enable interrupts */
    EA = 1;
    usb_up();


    // wait until the host identifies the usb device (the host timeouts are awfully fast)
    waitForUSBsetup();

    while (1)
    {  
        usbProcessEvents();
        appMainLoop();
    }

}

