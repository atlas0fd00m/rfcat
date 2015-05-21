#include "cc1111rf.h"
#include "cc1111_aes.h"
#include "chipcon_dma.h"
#include "global.h"
#include "nic.h"

#ifdef VIRTUAL_COM
    #include "cc1111.h"
    #include "cc1111_vcom.h"
#else
    #include "cc1111usb.h"
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




/*************************************************************************************************
 * Application Code - these first few functions are what should get overwritten for your app     *
 ************************************************************************************************/

__xdata u32 loopCnt;
__xdata u8 xmitCnt;

/* appMainInit() is called *before Interrupts are enabled* for various initialization things. */
void appMainInit(void)
{
    loopCnt = 0;
    xmitCnt = 1;

#ifdef RECEIVE_TEST
    RxMode();
    //startRX();
#endif
}

/* appMain is the application.  it is called every loop through main, as does the USB handler code.
 * do not block if you want USB to work.                                                           */
void appMainLoop(void)
{
    __xdata u8 processbuffer;
#ifdef TRANSMIT_TEST
    __xdata u8 testPacket[14];


    if (loopCnt++ == 90000)
    {
        /* Send a packet */
        testPacket[0] = 0x0D;
        testPacket[1] = xmitCnt++;
        testPacket[2] = 0x48;
        testPacket[3] = 0x41;
        testPacket[4] = 0x4C;
        testPacket[5] = 0x4C;
        testPacket[6] = 0x4F;
        //testPacket[6] = 0x43;
        //testPacket[7] = 0x43;
        testPacket[7] = lastCode[0];
        testPacket[8] = lastCode[1];
        testPacket[9] = 0x31;
        testPacket[10] = 0x31;
        testPacket[11] = 0x31;
        testPacket[12] = 0x31;

        transmit(testPacket, 13, 0, 0);
        //blink(400,400);
        REALLYFASTBLINK();
#ifndef VIRTUAL_COM
        debug("sent packet...");
#endif
        loopCnt = 0;
    }
#endif

    if (rfif)
    {
        lastCode[0] = 0xd;
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

                /* Set receive buffer to processed so it can be used again */
                rfRxProcessed[processbuffer] = RX_PROCESSED;
            }
        }

        rfif = 0;
        IEN2 |= IEN2_RFIE;
    }
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
    // initial radio state.  this is easily changed from the client, but
    // most cases it's far superior to have a sane initial rf config.
    // customize as desired, keeping in mind the impact any changes may
    // have on the function of the firmware (assumptions abound)
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
    TEST2       = 0x88; // low data rates, increased sensitivity provided by 0x81- was 0x88
    TEST1       = 0x31; // always 0x31 in tx-mode, for low data rates 0x35 provides increased sensitivity - was 0x31
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
    initBoard();
    initDMA();  // do this early so peripherals that use DMA can allocate channels correctly
    initAES();
    initUSB();
    blink(300,300);

    init_RF();
    appMainInit();

    usb_up();

    /* Enable interrupts */
    EA = 1;

    while (1)
    {  
        usbProcessEvents();
        appMainLoop();
    }

}

