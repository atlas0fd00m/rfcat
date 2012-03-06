#include "cc1111rf.h"
#include "global.h"
#include "FHSS.h"
#include "nic.h"
#include "string.h"

#ifdef VIRTUAL_COM
    #include "cc1111.h"
    #include "cc1111_vcom.h"
#else
    #include "cc1111usb.h"
#endif

/*************************************************************************************************
 * */


////  turn this on to enable TX of CARRIER at each hop instead of normal RX/TX
//#define DEBUG_HOPPING 1


xdata MAC_DATA_t macdata;
xdata u8 g_Channels[MAX_CHANNELS];

xdata u16 g_NIC_ID;


xdata u8 g_txMsgQueue[MAX_TX_MSGS][MAX_TX_MSGLEN];

////////// internal functions /////////
void t2IntHandler(void) interrupt T2_VECTOR;
void t3IntHandler(void) interrupt T3_VECTOR;
int appHandleEP5();

/**************************** PHY LAYER *****************************/

void PHY_set_channel(u16 chan)
{
    // set mode IDLE
    IdleMode();
    // set the channel
    CHANNR = chan;
    // if we want to transmit in this time slot, it needs to happen after a minimum delay
    RxMode();
}




/**************************** MAC LAYER *****************************/
void MAC_initChannels()
{
    // rudimentary channel setup.  this is for default hopping and testing.
    int loop;
    for (loop=0; loop<macdata.NumChannelHops; loop++)
    {
        g_Channels[loop] = loop % macdata.NumChannels;
    }
    macdata.MAC_threshold = 0;
}

void begin_hopping(u8 T2_offset)
{
    // reset the T2 clock settings based on T1 clock an offset
    T2CT -= T2_offset;
    T2CT -= MAC_TIMER_STATIC_DIFF;
    // start the T2 clock interrupt
    T2CTL |= T2CTL_INT;
    T2IE = 1;
    
}

void stop_hopping(void)
{
    // disable T2 interrupt
    T2CTL &= ~T2CTL_INT;
    
}

void MAC_sync(u16 CellID)
{
    // this should be implemented for a specific MAC/PHY.  too many details are left out here.
    // what are we synching to?  need to determine if we have a network id to sync with?
    // wait on a channel until MAX_SYNC_TIMEOUT
    //
    // do we want to check current state?  this should probably only be allowed from
    // NONHOPPING or DISCOVERY...
    if (macdata.mac_state != FHSS_STATE_NONHOPPING && macdata.mac_state != FHSS_STATE_DISCOVERY)
    {
        debug("FHSS state entering SYNCHING from wrong state");
        debughex(macdata.mac_state);
    }
    //
    // first disable hopping 
    stop_hopping();

    // FIXME: what happens if the first channel is jammed?  make this random or make it try several
    macdata.curChanIdx = 0;
    while (1)
    {
        MAC_set_chanidx(macdata.curChanIdx);
        while (!MARCSTATE == MARC_STATE_RX)
            ;
        if ((RSSI&0x7f) < 0x60)
            break;

        macdata.curChanIdx++;
        blink(10,10);
    }

    // set state =  SYNC
    macdata.mac_state = FHSS_STATE_SYNCHING;

    // store the main timer value for beginning of this phase.
    macdata.tLastStateChange = clock;

    // store the cell we're seeking.  since this search will use other parts of the code...
    macdata.desperatelySeeking = CellID;

    // at MAX_SYNC_TIMEOUT,start activesync, where i become the cell master/time master, and periodically transmit beacons.
}

void MAC_stop_sync()
{
    // this only stops the hunt.  hopping is not re-enabled.  if you want that, use a different mode
    macdata.mac_state = FHSS_STATE_NONHOPPING;
    macdata.tLastStateChange = clock;

}

void MAC_become_master()
{
    // this will force our nic to become the master
    macdata.mac_state = FHSS_STATE_SYNC_MASTER;
    macdata.tLastStateChange = clock;

}

void MAC_do_Master_scanny_thingy()
{
    macdata.mac_state = FHSS_STATE_SYNCINGMASTER;
    macdata.synched_chans = 0;
    macdata.tLastStateChange = clock;
}


void MAC_set_chanidx(u16 chanidx)
{
    PHY_set_channel( g_Channels[ chanidx ] );
}

void MAC_tx(u8* message, u8 len)
{
    // FIXME: possibly integrate USB/RF buffers so we don't have to keep copying...
    // queue data for sending at subsequent time slots.
    // FIXME: this is not good for fixed-length

    g_txMsgQueue[macdata.txMsgIdx][0] = len;
    memcpy(&g_txMsgQueue[macdata.txMsgIdx][1], message, len);

    if (++macdata.txMsgIdx >= MAX_TX_MSGS)
    {
        macdata.txMsgIdx = 0;
    }

}


void MAC_set_NIC_ID(u16 NIC_ID)
{
    // this function is a placeholder for more functionality, if it makes sense... perhaps cut it.
    g_NIC_ID = NIC_ID;
}

void MAC_rx_handle(u8 len, u8* message)
{
    len;
    message;
    // does this even exist?  we should just handle received packets same as always.
    // actually, for some systems, this should send back an ACK or NACK on the same channel
}


u8 MAC_getNextChannel()
{
    macdata.curChanIdx++;
    if (macdata.curChanIdx >= MAX_CHANNELS)
    {
        macdata.curChanIdx = 0;
    }
    return g_Channels[macdata.curChanIdx];
}




/************************** Timer Interrupt Vectors **************************/
void t2IntHandler(void) interrupt T2_VECTOR  // interrupt handler should trigger on T2 overflow
{
    xdata u8 packet[28];
    // timer2 controls hopping.
    // if the system is not supposed to be hopping, T2 Interrupt should be disabled
    // otherwise....
    //
    // if we are here, the T2CT must have cycled.  increment rf_MAC_timer
    if (++rf_MAC_timer >= macdata.MAC_threshold)
    {
        // change to the next channel
        macdata.tLastHop = T2CT | (rf_MAC_timer<<8);
        
        if (++macdata.curChanIdx >= macdata.NumChannelHops)
        {
            macdata.curChanIdx = 0;
        }

        MAC_set_chanidx(macdata.curChanIdx);
        rf_MAC_timer = 0;
#ifdef DEBUG_HOPPING
        debug("hop");
        RFST = RFST_SIDLE;
        while(!(MARCSTATE & MARC_STATE_IDLE));
        RFST = RFST_STX;        // for debugging purposes, we'll just transmit carrier at each hop
        LED = !LED;
        while(!(MARCSTATE & MARC_STATE_TX));
#else

        // if we are the SYNC_MASTER and are in the process of "doing the SYNC"
        // we need to transmit something indicating the channel we're on
        switch (macdata.mac_state)
        {
            case FHSS_STATE_SYNCINGMASTER:
                sleepMillis(FHSS_TX_SLEEP_DELAY);
                packet[0] = 28;
                packet[1] = macdata.curChanIdx & 0xff;
                packet[2] = macdata.curChanIdx >> 8;
                packet[3] = 'B';
                packet[4] = 'L';
                packet[5] = 'A';
                packet[6] = 'H';
                packet[7] = 'B';
                packet[8] = 'L';
                packet[9] = 'A';
                packet[10] = 'H';
                packet[11] = 'B';
                packet[12] = 'L';
                packet[13] = 'A';
                packet[14] = 'H';
                packet[15] = 'B';
                packet[16] = 'L';
                packet[17] = 'A';
                packet[18] = 'H';
                packet[19] = 'B';
                packet[20] = 'L';
                packet[21] = 'A';
                packet[22] = 'H';
                packet[23] = 'B';
                packet[24] = 'L';
                packet[25] = 'A';
                packet[26] = 'H';
                packet[27] = ' ';

                transmit((xdata u8*)&packet, packet[0]);
                macdata.synched_chans++;
                break;

            case FHSS_STATE_SYNCHED:
            case FHSS_STATE_SYNC_MASTER:
                // if the queue is not empty, wait but then tx.
                // FIXME: this currently sends only once per hop.  this may or may not be appropriate, but it's simple to implement.
                if (g_txMsgQueue[macdata.txMsgIdxDone][0])      // if length byte >0
                {
                    LED = !LED;
                    sleepMillis(FHSS_TX_SLEEP_DELAY);
                    transmit(&g_txMsgQueue[macdata.txMsgIdxDone][!(PKTCTRL0&1)], g_txMsgQueue[macdata.txMsgIdxDone][0]);
                    // FIXME: rudimentary FHSS_tx in interrupt handler, make more elegant (with confirmation or somesuch?)
                    g_txMsgQueue[macdata.txMsgIdxDone][0] = 0;

                    if (++macdata.txMsgIdxDone > MAX_TX_MSGS)
                    {
                        macdata.txMsgIdxDone = 0;
                    }
                }
        }
#endif
    }
}

void t3IntHandler(void) interrupt T3_VECTOR
{
    // transmit one message from queue... possibly more, if time allows
    // must check the time left when tx completes
}

void init_FHSS(void)
{
    macdata.mac_state = 0;
    macdata.txMsgIdx = 0;
    macdata.txMsgIdxDone = 0;
    macdata.curChanIdx = 0;
    macdata.NumChannels = DEFAULT_NUM_CHANS;
    macdata.NumChannelHops = DEFAULT_NUM_CHANHOPS;
    macdata.tLastHop = 0;
    macdata.tLastStateChange = 0;
    macdata.MAC_threshold = 0;
    macdata.desperatelySeeking = 0;
    macdata.synched_chans = 0;

    MAC_initChannels();

    macdata.mac_state = FHSS_STATE_NONHOPPING;   // this is basic NIC functionality


    // Timer Setup:
// FIXME: this should be defined so it works with 24/26mhz
    // setup TIMER 1
    // free running mode
    // time freq:
    //   ******************** NOW IN GLOBAL.C ************************
    //CLKCON &= 0xc7;          //( ~ 0b111000);
    //T1CTL |= T1CTL_DIV_128;
    //T1CTL |= T1CTL_MODE_FREERUN;
    //   *************************************************************
// FIXME: turn on timer interrupts for t1 and t2
    // (TIMER2 is initially setup in cc1111rf.c in init_RF())
    // setup TIMER 2
    // NOTE:
    // !!! any changes to TICKSPD will change the calculation of MAC timer speed !!!
    //
    // free running mode
    // time freq:
#ifndef IMME
    // 100ms at 24mhz
    //T2PR = 0x92;        
    //T2CTL |= T2CTL_TIP_64;  // 64, 128, 256, 1024

    // 150ms at 24mhz
    T2PR = 0xdc;        
    T2CTL |= T2CTL_TIP_64;  // 64, 128, 256, 1024

    // 200ms at 24mhz
    //T2PR = 0x92;        
    //T2CTL |= T2CTL_TIP_128;  // 64, 128, 256, 1024
    
    // 250ms at 24mhz
    //T2PR = 0xb7;        
    //T2CTL |= T2CTL_TIP_128;  // 64, 128, 256, 1024
    
    // 300ms at 24mhz
    //T2PR = 0xdc;        
    //T2CTL |= T2CTL_TIP_128;  // 64, 128, 256, 1024
#else
    // 100ms at 26mhz
    //T2PR = 0x9f;        
    //T2CTL |= T2CTL_TIP_64;  // 64, 128, 256, 1024

    // 150ms at 26mhz
    T2PR = 0xee;        
    T2CTL |= T2CTL_TIP_64;  // 64, 128, 256, 1024

    // 200ms at 26mhz
    //T2PR = 0x9f;        
    //T2CTL |= T2CTL_TIP_128;  // 64, 128, 256, 1024

    // 250ms at 26mhz
    //T2PR = 0xc6;        
    //T2CTL |= T2CTL_TIP_128;  // 64, 128, 256, 1024
    
    // 300ms at 26mhz
    //T2PR = 0xee;        
    //T2CTL |= T2CTL_TIP_128;  // 64, 128, 256, 1024
#endif
    T2CTL |= T2CTL_TIG;


    // setup TIMER 3
    // free running mode
    // tick freq: 
    T3CTL |= T3CTL_START;
}

/*************************************************************************************************
 * Application Code - these first few functions are what should get overwritten for your app     *
 ************************************************************************************************/

/* appMainInit() is called *before Interrupts are enabled* for various initialization things. */
void appMainInit(void)
{
    registerCb_ep5( appHandleEP5 );
    clock = 0;

    init_FHSS();

    RxMode();
}

/* appMain is the application.  it is called every loop through main, as does the USB handler code.
 * do not block if you want USB to work.                                                           */
void appMainLoop(void)
{
    xdata u8 processbuffer;

    switch  (macdata.mac_state)
    {
        case FHSS_STATE_SYNCHING:
            // FIXME: need to compare part of the packet to desperatelySeeking;
            // FIXME: TIMEOUT??  do we just stay in SYNCHING forever1?!?
            if (rfif)
            {
                lastCode[0] = 0xd;
                IEN2 &= ~IEN2_RFIE;

                if(rfif & RFIF_IRQ_DONE)
                {
                    // FIXME: do something with desperatelySeeking here.
                    // FIXME: OR... use protocol knowledge to dynamically generate a hopping pattern from this discovered cell
                    macdata.mac_state = FHSS_STATE_SYNCHED;
                    begin_hopping((u8)(rf_tLastRecv & 0xff));       // synching happens within
                    // we've received a packet with the proper sync word and settings.  
                    debug("network packet(sync)");
                    debughex16((u16)rf_tLastRecv);
                    debug((code u8*)&rfrxbuf[rfRxCurrentBuffer][0]);

                    // now back to usual programming
                    processbuffer = !rfRxCurrentBuffer;
                    if(rfRxProcessed[processbuffer] == RX_UNPROCESSED)
                    {   
                        // we've received a packet.  deliver it.
                        if (PKTCTRL0&1)     // variable length packets have a leading "length" byte, let's skip it
                            txdata(APP_NIC, NIC_RECV, (u8)rfrxbuf[processbuffer][0], (u8*)&rfrxbuf[processbuffer][1]);
                        else
                            txdata(APP_NIC, NIC_RECV, PKTLEN, (u8*)&rfrxbuf[processbuffer]);

                        /* Set receive buffer to processed so it can be used again */
                        rfRxProcessed[processbuffer] = RX_PROCESSED;
                    }
                    rfif &= ~RFIF_IRQ_DONE;
                }
            }

            rfif = 0;
            IEN2 |= IEN2_RFIE;
            break;

        case FHSS_STATE_DISCOVERY:
            // check for timeout value.  if we cross timeout, we'll return to FHSS_STATE_NONHOPPING, 
            // or FHSS_STATE_SYNC_MASTER.
            if (rfif)
            {
                lastCode[0] = 0xd;
                IEN2 &= ~IEN2_RFIE;

                if(rfif & RFIF_IRQ_DONE)
                {
                    // we've received a packet with the proper sync word and settings.  
                    processbuffer = !rfRxCurrentBuffer;
                    debug("network packet(discovery)");
                    debughex16((u16)rfrxbuf[processbuffer]);
                    debug((code u8*)&rfrxbuf[processbuffer][0]);

                    // now back to usual programming
                    processbuffer = !rfRxCurrentBuffer;
                    if(rfRxProcessed[processbuffer] == RX_UNPROCESSED)
                    {   
                        // we've received a packet.  deliver it.
                        if (PKTCTRL0&1)     // variable length packets have a leading "length" byte, let's skip it
                            txdata(APP_NIC, NIC_RECV, (u8)rfrxbuf[processbuffer][0], (u8*)&rfrxbuf[processbuffer][1]);
                        else
                            txdata(APP_NIC, NIC_RECV, PKTLEN, (u8*)&rfrxbuf[processbuffer]);

                        /* Set receive buffer to processed so it can be used again */
                        rfRxProcessed[processbuffer] = RX_PROCESSED;
                    }
                    rfif &= ~RFIF_IRQ_DONE;
                }
            }

            rfif = 0;
            IEN2 |= IEN2_RFIE;
            break;

        case FHSS_STATE_SYNCINGMASTER:
            // if we've done one loop, stop
            if (macdata.synched_chans >= macdata.NumChannelHops)
            {
                macdata.mac_state = FHSS_STATE_SYNC_MASTER;
            }
            break;
        // perhaps we should just make this "default:"
        case FHSS_STATE_SYNC_MASTER:
        case FHSS_STATE_SYNCHED:
        case FHSS_STATE_NONHOPPING:
            // this is where we handle the RF packet
            if (rfif)
            {
                //LED = !LED;
                lastCode[0] = 0xd;

                if(rfif & RFIF_IRQ_DONE)
                {
                    processbuffer = !rfRxCurrentBuffer;
                    if(rfRxProcessed[processbuffer] == RX_UNPROCESSED)
                    {   
                        // we've received a packet.  deliver it.
                        if (PKTCTRL0&1)     // variable length packets have a leading "length" byte, let's skip it
                            txdata(APP_NIC, NIC_RECV, (u8)rfrxbuf[processbuffer][0], (u8*)&rfrxbuf[processbuffer][1]);
                        else
                            txdata(APP_NIC, NIC_RECV, PKTLEN, (u8*)&rfrxbuf[processbuffer]);
   
                        //txdata(APP_NIC, NIC_RECV, rfRxCounter[processbuffer], (u8*)&rfrxbuf[processbuffer]);

                        /* Set receive buffer to processed so it can be used again */
                        rfRxProcessed[processbuffer] = RX_PROCESSED;
                    }
                    rfif &= ~RFIF_IRQ_DONE;           // FIXME: rfif is way too easily tossed aside here...
                }

                //LED = !LED;
            }
            break;
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
    u8 app, cmd;
    u16 len;
    __xdata u8 *buf = &ep5.OUTbuf[0];

    app = *buf++;
    cmd = *buf++;
    len = (u8)*buf++;         // FIXME: should we use this?  or the lower byte of OUTlen?
    len += (u16)((*buf++) << 8);                                               // point at the address in memory

    // ep5.OUTbuf should have the following bytes to start:  <app> <cmd> <lenlow> <lenhigh>
    // check the application
    //  then check the cmd
    //   then process the data
    switch (app)
    {
        case APP_NIC:

        switch (cmd)
        {
            case NIC_RFMODE:
                switch (*buf++)
                {
                    case RF_STATE_RX:

                        RxMode();
                        break;
                    case RF_STATE_IDLE:
                        IdleMode();
                        break;
                    case RF_STATE_TX:
						// ??  this should be just turning on CARRIER
                        setRFTx();
                        break;
                }
                txdata(app,cmd,len,buf);
                ep5.OUTbytesleft = 0;
                break;
            case NIC_XMIT:
                // FIXME:  this needs to place buf data into the FHSS txMsgQueue
                transmit(buf, 0);
                //{ LED=1; sleepMillis(2); LED=0; sleepMillis(1); }
                txdata(app, cmd, 1, (xdata u8*)"\x00");
                ep5.OUTbytesleft = 0;
                break;
                
            case NIC_SET_ID:
                MAC_set_NIC_ID(*buf);
                txdata(app, cmd, 1, buf);
                ep5.OUTbytesleft = 0;
                break;

            case FHSS_XMIT:
                MAC_tx(buf, len);
                txdata(app, cmd, 1, (xdata u8*)"\x00");
                ep5.OUTbytesleft = 0;
                break;
                
            case FHSS_SET_CHANNELS:
                macdata.NumChannels = (xdata u16)*buf;
                if (macdata.NumChannels <= MAX_CHANNELS)
                {
                    buf += 2;
                    memcpy(&g_Channels[0], buf, macdata.NumChannels);
                    txdata(app, cmd, 2, (u8*)&macdata.NumChannels);
                } else {
                    txdata(app, cmd, 8, (xdata u8*)"NO DEAL");
                }
                ep5.OUTbytesleft = 0;
                break;

            case FHSS_NEXT_CHANNEL:
                MAC_set_chanidx(MAC_getNextChannel());
                txdata(app, cmd, 1, &g_Channels[macdata.curChanIdx]);
                ep5.OUTbytesleft = 0;
                break;

            case FHSS_CHANGE_CHANNEL:
                PHY_set_channel(*buf);
                txdata(app, cmd, 1, buf);
                ep5.OUTbytesleft = 0;
                break;

            case FHSS_START_HOPPING:
                begin_hopping(0);
                txdata(app, cmd, 1, buf);
                ep5.OUTbytesleft = 0;
                break;

            case FHSS_STOP_HOPPING:
                stop_hopping();
                txdata(app, cmd, 1, buf);
                ep5.OUTbytesleft = 0;
                break;

            // FIXME: do we even need g_MAC_threshold anymore?
            case FHSS_SET_MAC_THRESHOLD:
                macdata.MAC_threshold = *buf;
                txdata(app, cmd, 1, buf);
                ep5.OUTbytesleft = 0;
                break;

            case FHSS_GET_MAC_THRESHOLD:
                txdata(app, cmd, 4, (xdata u8*)&macdata.MAC_threshold);
                ep5.OUTbytesleft = 0;
                break;

            case FHSS_SET_MAC_DATA:
                memcpy((xdata u8*)&macdata, (xdata u8*)*buf, sizeof(macdata));
                txdata(app, cmd, sizeof(macdata), buf);
                ep5.OUTbytesleft = 0;
                break;

            case FHSS_GET_MAC_DATA:
                txdata(app, cmd, sizeof(macdata), (xdata u8*)&macdata);
                ep5.OUTbytesleft = 0;
                break;

            case FHSS_START_SYNC:
                MAC_sync(*buf);
                txdata(app, cmd, 1, buf);
                ep5.OUTbytesleft = 0;
                break;
                
            case FHSS_SET_STATE:
                // store the main timer value for beginning of this phase.
                macdata.tLastStateChange = clock;
                macdata.mac_state = (u8)*buf;
                
                // if macdata.mac_state is > 2, make sure the T2 interrupt is set
                // if macdata.mac_state <= 2, make sure T2 interrupt is ignored
                switch (macdata.mac_state)
                {
                    case FHSS_STATE_NONHOPPING:
                    case FHSS_STATE_DISCOVERY:
                    case FHSS_STATE_SYNCHING:
                        
                        stop_hopping();
                        break;

                    case FHSS_STATE_SYNCINGMASTER:
                        macdata.synched_chans = 0;
                        begin_hopping(0);
                        break;

                    case FHSS_STATE_SYNCHED:
                    case FHSS_STATE_SYNC_MASTER:
                        begin_hopping(0);
                        break;
                }
                
                txdata(app, cmd, 1, buf);
                ep5.OUTbytesleft = 0;
                break;
                
            case FHSS_GET_STATE:
                txdata(app, cmd, 1, (xdata u8*)&macdata.mac_state);
                ep5.OUTbytesleft = 0;
                break;
                
            default:
                txdata(app, cmd, 1, buf);
                ep5.OUTbytesleft = 0;
                break;
        }
        break;
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
    xdata u8* dst;
    xdata u8* src;

    // we are not called with the Request header as is appHandleEP0.  this function is only called after an OUT packet has been received,
    // which triggers another usb interrupt.  the important variables from the EP0 request are stored in ep0req, ep0len, and ep0value, as
    // well as ep0.OUTlen (the actual length of ep0.OUTbuf, not just some value handed in).

    // for our purposes, we only pay attention to single-packet transfers.  in more complex firmwares, this may not be sufficient.
    switch (ep0req)
    {
        case 1:     // poke
            
            src = (xdata u8*) &ep0.OUTbuf[0];
            dst = (xdata u8*) ep0value;

            for (loop=ep0.OUTlen; loop>0; loop--)
            {
                *dst++ = *src++;
            }
            break;
    }

    // must be done with the buffer by now...
    ep0.flags &= ~EP_OUTBUF_WRITTEN;
#endif
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
            case EP0_CMD_GET_DEBUG_CODES:
                setup_send_ep0(&lastCode[0], 2);
                break;
            case EP0_CMD_GET_ADDRESS:
                setup_sendx_ep0((xdata u8*)USBADDR, 40);
                break;
            case EP0_CMD_PEEKX:
                setup_sendx_ep0((xdata u8*)pReq->wValue, pReq->wLength);
                break;
            case EP0_CMD_PING0:
                setup_send_ep0((u8*)pReq, pReq->wLength);
                break;
            case EP0_CMD_PING1:
                setup_sendx_ep0((xdata u8*)&ep0.OUTbuf[0], 16);//ep0.OUTlen);
                break;
            case EP0_CMD_RESET:
                if (strncmp((char*)&(pReq->wValue), "RSTN", 4))           // therefore, ->wValue == "RS" and ->wIndex == "TN" or no reset
                {
                    blink(300,300);
                    break;   //didn't match the signature.  must have been an accident.
                }

                // implement a RESET by trigging the watchdog timer
                WDCTL = 0x83;   // Watchdog ENABLE, Watchdog mode, 2ms until reset
        }
    }
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
    // in global.c
    clock_init();
    io_init();
}


void main (void)
{
    initBoard();
    initUSB();
    init_RF();
    appMainInit();

    usb_up();

    /* Enable interrupts */
    EA = 1;
    waitForUSBsetup();

    REALLYFASTBLINK();

    while (1)
    {  
        usbProcessEvents();
        appMainLoop();
    }

}

