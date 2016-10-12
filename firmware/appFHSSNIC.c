#include "cc1111rf.h"
#include "cc1111_aes.h"
#include "chipcon_dma.h"
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


/* todo:  NIC_LONG_XMIT:
 * usb cycles (appHandleEP5()):
 *    case NIC_LONG_XMIT:
 *      set macdata.txMsgIdx = 0
 *      set macdata.txMsgIdxDone = 0
 *      clear all buffer lengths
 *      set macdata.macstate = MAC_STATE_LONG_XMIT  (rly? should just stay at NONHOPPING?)
 *      write into g_txMsgQueue[macdata.txMsgIdx]
 *      need to indicate that the buffer if filled  (buffer[0] = len)
 *      need to indicate that there's data to RF TRANSMIT
 *
 *    case NIC_LONG_XMIT_MORE:
 *      if g_txMsgQueue[macdata.txMsgIdx+1][0] != 0 (we've looped and caught up with RFtx)
 *          return 1 (meaning, don't release the USB IN buffer for writing)
 *      macdata.txMsgIdx ++
 *      write into g_txMsgQueuepmacdata.txMsgIdx], [0]=len, [1:]=data
 *
 * rf cycles:
 *      some indicator of Infinite Transmit mode  (rfTxInfMode)
 *      start writing g_txMsgQueue[macdata.txMsgIdxDone]
 *      when done with g_txMsgQueue[macdata.txMsgIdxDone]:
 *          macdata.txMsgIdxDone++ (wrap if == MAX...)
 *          if g_txMsgQueue[macdata.txMsgIdxDone][0] == 0:
 *              signal "done with transmitting"
 *      
 *
*/
////  turn this on to enable TX of CARRIER at each hop instead of normal RX/TX
//#define DEBUG_HOPPING 1


#define RFCAT

__xdata u8 g_Channels[MAX_CHANNELS];

__xdata u16 g_NIC_ID;


// queue of messages to transmit.  may be used for FHSS, or to send LONG messages
// first byte of each message indicates its length
__xdata u8 g_txMsgQueue[MAX_TX_MSGS][MAX_TX_MSGLEN+1];

////////// internal functions /////////
void t2IntHandler(void) __interrupt T2_VECTOR;
void t3IntHandler(void) __interrupt T3_VECTOR;
int appHandleEP5();

/**************************** PHY LAYER *****************************/

void PHY_set_channel(__xdata u16 chan)
{
    // set mode IDLE
    RFOFF;
    // set the channel
    CHANNR = chan;
    // if we want to transmit in this time slot, it needs to happen after a minimum delay
    RFRX;
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
    //macdata.MAC_threshold = 0;
}

void begin_hopping(__xdata u8 T2_offset)
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


__xdata u8 transmit_long(__xdata u8* __xdata buf, __xdata u16 len, __xdata u8 blocks)
    /* Infinite transmit.  keep transmitting until the next buffer in the g_txMsgQueue is clear
     * ([0] == 0)
     * */
{
    __xdata u16 countdown;
    __xdata u8 err;

    if (macdata.mac_state != MAC_STATE_NONHOPPING)
    {
        debug("Cannot call transmit_long while FHSS Hopping or already processing transmit_long!");
        debughex(macdata.mac_state);
        return RC_RF_MODE_INCOMPAT;
    }

    macdata.mac_state = MAC_STATE_LONG_XMIT;
    while (MARCSTATE == MARC_STATE_TX)
    {
            //LED = !LED;
    }
    // Leave LED in a known state (off)
    LED = 0;

    // setup infinite mode, length, and the variables that will last for and manage the whole transmission
    rfTxTotalTXLen = len;
                //debughex16(rfTxTotalTXLen);
    rfTxBufferEnd = MAX_TX_MSGLEN + 1; // add 1 for length byte
                //debughex16(rfTxBufferEnd);
    rftxbuf = (volatile __xdata u8*)&g_txMsgQueue[0][0];
    rfTxRepeatCounter = 0;
    rfTxCurBufIdx = macdata.txMsgIdxDone = 0;
    macdata.txMsgIdx = 0;
    rfTxCounter = 1; // don't transmit length byte
    rfTxBufCount = MAX_TX_MSGS;

    // clear buffer
    MAC_tx(NULL, 0);

    // pre-load 1st blocks into message queue
    for(countdown = 0 ; countdown < blocks ; ++countdown)
    {
        err = MAC_tx(buf + (u8) (countdown * MAX_TX_MSGLEN), (u8) MAX_TX_MSGLEN);
        if(err)
            {
            debug("MAC_tx() returned error");
            macdata.mac_state = MAC_STATE_NONHOPPING;
            debughex(err);
            return err;
            }
    }

    // set up crypto - MAC_tx will perform enc/dec if required
    if(rfAESMode & AES_CRYPTO_OUT_ENABLE && rfTxTotalTXLen % 16)
    {
        // set new length to multiple of 16 as last block will be padded
        rfTxTotalTXLen += 16 - (rfTxTotalTXLen % 16);
    }

    // configure for infinitemode if required
    if(rfTxTotalTXLen > RF_MAX_TX_BLOCK)
    {
        PKTLEN = (u8) (rfTxTotalTXLen % 256);
        PKTCTRL0 &= ~PKTCTRL0_LENGTH_CONFIG;
        PKTCTRL0 |= PKTCTRL0_LENGTH_CONFIG_INF;
        rfTxInfMode = 1;
    }
    else
    {
        PKTLEN = (u8) rfTxTotalTXLen;
        rfTxInfMode = 0;
    }

    /* Put radio into tx state */
#ifdef YARDSTICKONE
    SET_TX_AMP;
#endif
    RFST = RFST_STX;

    // wait until we're safely in TX mode
    countdown = 60000;
    while (MARCSTATE != MARC_STATE_TX && --countdown)
    {
        //LED = !LED;
    }
    // LED on - we're transmitting
    LED = 1;
    if (!countdown)
    {
        lastCode[1] = LCE_RFTX_NEVER_TX;
        debug("never entered TX");
    }
    //debug("done with transmit_long");
    return RC_NO_ERROR;
}

__xdata u8 MAC_tx(__xdata u8* __xdata msg, __xdata u8 len)
{
    // queue data for sending at subsequent time slots.
    // - overloaded - also used for arbitrary length transmission
    //
    // FIXME: possibly integrate USB/RF buffers so we don't have to keep copying... - this would break stuff
    // FIXME: this is not good for fixed-length
    // FIXME: possibly use DMA for transfers?
    // FIXME: watch for errors and changes in state from ISR, and return value.

    if (len > MAX_TX_MSGLEN)
    {
        debug("FHSSxmit message too long");
        return RC_ERR_BUFFER_SIZE_EXCEEDED;
    }

    // len of 0 means clear buffer
    if(len == 0)
    {
        //debug("clearing queue");
        for(macdata.txMsgIdx = 0 ; macdata.txMsgIdx < rfTxBufCount ; ++macdata.txMsgIdx)
        {
            g_txMsgQueue[macdata.txMsgIdx][0] = BUFFER_AVAILABLE;
        }
        macdata.txMsgIdx = 0;
        return RC_NO_ERROR;
    }

    switch (macdata.mac_state)
    {
        case MAC_STATE_LONG_XMIT:
            if (macdata.txMsgIdx && MARCSTATE != MARC_STATE_TX)
            {
                macdata.mac_state = MAC_STATE_LONG_XMIT_FAIL;
                return RC_TX_ERROR;
            }
            break;
        case MAC_STATE_NONHOPPING:
            return RC_TX_ERROR;
    }
    if (g_txMsgQueue[macdata.txMsgIdx][0] != BUFFER_AVAILABLE)
    {
        // can't add to the next queue
        lastCode[1] = LCE_RF_MULTI_BUFFER_NOT_FREE;
        return RC_ERR_BUFFER_NOT_AVAILABLE;
    }

    // mark the queue msg as filling:
    g_txMsgQueue[macdata.txMsgIdx][0] = BUFFER_FILLING;
    // copy data
    memcpy(&g_txMsgQueue[macdata.txMsgIdx][1], msg, len);
    // crypt if required
    // todo: currently only works at very low baud rates (e.g. 10k)
    // todo: may be a fundamental limitation as it slows throughput
    // todo: implement some kind of failure detection
    if(rfAESMode & AES_CRYPTO_OUT_ENABLE)
    {
        len = padAES(&g_txMsgQueue[macdata.txMsgIdx][1], len);
        if((rfAESMode & AES_CRYPTO_OUT_TYPE) == AES_CRYPTO_OUT_ENCRYPT)
            encAES(&g_txMsgQueue[macdata.txMsgIdx][1], &g_txMsgQueue[macdata.txMsgIdx][1], len, (rfAESMode & AES_CRYPTO_MODE));
        else
            decAES(&g_txMsgQueue[macdata.txMsgIdx][1], &g_txMsgQueue[macdata.txMsgIdx][1], len, (rfAESMode & AES_CRYPTO_MODE));
    }
    // place data len in first byte
    g_txMsgQueue[macdata.txMsgIdx][0] = len;
    //debug("writing block");
    //debughex(macdata.txMsgIdx);
    //debug("writing length");
    //debughex(g_txMsgQueue[macdata.txMsgIdx][0]);
    // [0] means:  0xff=writing, 0=avail, !0=ready_to_send/datalen

    if (++macdata.txMsgIdx == rfTxBufCount)
    {
        macdata.txMsgIdx = 0;
    }

    return RC_NO_ERROR;
}

void MAC_sync(__xdata u16 CellID)
{
    // this should be implemented for a specific MAC/PHY.  too many details are left out here.
    // what are we synching to?  need to determine if we have a network id to sync with?
    // wait on a channel until MAX_SYNC_TIMEOUT
    //
    // do we want to check current state?  this should probably only be allowed from
    // NONHOPPING or DISCOVERY...
    if (macdata.mac_state != MAC_STATE_NONHOPPING && macdata.mac_state != MAC_STATE_DISCOVERY)
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
        while (MARCSTATE != MARC_STATE_RX)
            ;
        if ((RSSI&0x7f) < 0x60)
            break;

        macdata.curChanIdx++;
        blink(10,10);
    }

    // set state =  SYNC
    macdata.mac_state = MAC_STATE_SYNCHING;

    // store the main timer value for beginning of this phase.
    macdata.tLastStateChange = clock;

    // store the cell we're seeking.  since this search will use other parts of the code...
    macdata.desperatelySeeking = CellID;

    // at MAX_SYNC_TIMEOUT,start activesync, where i become the cell master/time master, and periodically transmit beacons.
}

void MAC_stop_sync()
{
    // this only stops the hunt.  hopping is not re-enabled.  if you want that, use a different mode
    macdata.mac_state = MAC_STATE_NONHOPPING;
    macdata.tLastStateChange = clock;

}

void MAC_become_master()
{
    // this will force our nic to become the master
    macdata.mac_state = MAC_STATE_SYNC_MASTER;
    macdata.tLastStateChange = clock;

}

void MAC_do_Master_scanny_thingy()
{
    macdata.mac_state = MAC_STATE_SYNCINGMASTER;
    macdata.synched_chans = 0;
    macdata.tLastStateChange = clock;
    begin_hopping(0);
}


void MAC_set_chanidx(__xdata u16 chanidx)
{
    PHY_set_channel( g_Channels[ chanidx ] );
}


void MAC_set_NIC_ID(__xdata u16 NIC_ID)
{
    // this function is a placeholder for more functionality, if it makes sense... perhaps cut it.
    g_NIC_ID = NIC_ID;
}

void MAC_rx_handle(__xdata u8 len, __xdata u8* __xdata message)
{
    len;
    message;
    // does this even exist?  we should just handle received packets same as always.
    // actually, for some systems, this should send back an ACK or NACK on the same channel
}


__xdata u8 MAC_getNextChannel()
{
    macdata.curChanIdx++;
    if (macdata.curChanIdx >= MAX_CHANNELS)
    {
        macdata.curChanIdx = 0;
    }
    return g_Channels[macdata.curChanIdx];
}




/************************** Timer Interrupt Vectors **************************/
void t2IntHandler(void) __interrupt T2_VECTOR  // interrupt handler should trigger on T2 overflow
{
    __xdata u8 packet[28];

    // timer2 controls hopping.
    // if the system is not supposed to be hopping, T2 Interrupt should be disabled
    // otherwise....
    //
    // if we are here, the T2CT must have cycled.  increment rf_MAC_timer
    if (++rf_MAC_timer == macdata.MAC_threshold)
        rf_MAC_timer = 0;   // since we're 0-based, MAC_threshold is actually past the end of our state machine, which makes it 0 *right now*
    
    switch (rf_MAC_timer)
    {
        case 0:     // change channels
            // mark last hop time
            macdata.tLastHop = T2CT | (rf_MAC_timer<<8);        // should this be based on clock and T1?
            
            // change to the next channel
            if (++macdata.curChanIdx >= macdata.NumChannelHops)
            {
                macdata.curChanIdx = 0;
            }

#ifndef DEBUG_HOPPING
            // if we are transmitting, don't change.  this helps with certain faster hopping systems where the packet is intended to take longer than the dwell time
            if (MARCSTATE == MARC_STATE_TX)
                return;
#endif

            // actually change the channel to our new index
            MAC_set_chanidx(macdata.curChanIdx);
            
#ifdef DEBUG_HOPPING
            debug("hop");
            RFOFF;
            RFTX;        // for debugging purposes, we'll just transmit carrier at each hop
            //LED = !LED;
            while(MARCSTATE != MARC_STATE_TX);
            return();
    
#endif
            break;
            
        case 1:
            //only on the first tick do we send our sync master discovery beacon frame
            if (macdata.mac_state == MAC_STATE_SYNCINGMASTER)
            {
                sleepMillis(FHSS_TX_SLEEP_DELAY);
                packet[0] = 28;
                packet[1] = macdata.curChanIdx & 0xff;
                packet[2] = macdata.curChanIdx >> 8;
                packet[3] =  'B';
                packet[4] =  'L';
                packet[5] =  'A';
                packet[6] =  'H';
                packet[7] =  'B';
                packet[8] =  'L';
                packet[9] =  'A';
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

                transmit((__xdata u8*)&packet[1], 28, 0, 0);
                macdata.synched_chans++;
                break;      // don't want to do anything else if we're in this state.
            }
            break;
            
        default:    // all other ticks we can transmit
            // if we are the SYNC_MASTER and are in the process of "doing the SYNC"
            // we need to transmit something indicating the channel we're on
            switch (macdata.mac_state)
            {
                case MAC_STATE_SYNCINGMASTER:
                case MAC_STATE_SYNC_MASTER:
                    if (100 < (clock - macdata.tLastStateChange))   // periodically shift back to beaconing
                    {
                        debug("SYNCH_MASTER -> SYNCINGMASTER");
                        macdata.mac_state = MAC_STATE_SYNCINGMASTER;
                        macdata.tLastStateChange = clock;
                    }
                    // flow into SYNCHED to behave just like any other synched node (transmitting, etc...)
                case MAC_STATE_SYNCHED:
                    // if the queue is not empty, wait but then tx.
                    // FIXME: this currently sends only once per hop.  this may or may not be appropriate, but it's simple to implement.

                    /*if (T2CT < 10 || T2CT > 246)      // always 0xff, i mean, we're *in* the interrupt handler after all.
                    {
                        debughex(T2CT);
                        return;
                    }*/

                    if ( g_txMsgQueue[macdata.txMsgIdxDone][0])      // if length byte >0
                    {
                        //LED = !LED;
                        sleepMillis(FHSS_TX_SLEEP_DELAY);
                        transmit(&g_txMsgQueue[macdata.txMsgIdxDone][!(PKTCTRL0&1)], g_txMsgQueue[macdata.txMsgIdxDone][0], 0, 0);
                        // FIXME: rudimentary FHSS_tx in interrupt handler, make more elegant (with confirmation or somesuch?)
                        g_txMsgQueue[macdata.txMsgIdxDone][0] = 0;

                        if (++macdata.txMsgIdxDone >= MAX_TX_MSGS)
                        {
                            macdata.txMsgIdxDone = 0;
                        }
                        debug("FHSSxmit done");
                    }
            }
    }
}

void t3IntHandler(void) __interrupt T3_VECTOR
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
    macdata.MAC_threshold = 6;
    macdata.MAC_timer = 0;
    macdata.desperatelySeeking = 0;
    macdata.synched_chans = 0;

    MAC_initChannels();

    macdata.mac_state = MAC_STATE_NONHOPPING;   // this is basic NIC functionality


    // Timer Setup:
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

//  initialize the MAC layer.  
void init_MAC(void)
{
    init_FHSS();
}


/*************************************************************************************************
 * Application Code - these first few functions are what should get overwritten for your app     *
 ************************************************************************************************/
__xdata u8 processbuffer;
__xdata u8 *__xdata chan_table;

/* appMainInit() is called *before Interrupts are enabled* for various initialization things. */
void appMainInit(void)
{
    registerCb_ep5( appHandleEP5 );
    clock = 0;

    init_MAC();

    processbuffer = 0;
    chan_table = rfrxbuf[0];

}

/* appMain is the application.  it is called every loop through main, as does the USB handler code.
 * do not block if you want USB to work.                                                           */
void appMainLoop(void)
{

    switch  (macdata.mac_state)
    {
        // do this first for speed/efficiency
        case MAC_STATE_LONG_XMIT:
            break;

        case MAC_STATE_PREP_SPECAN:
            RFOFF;
            PKTCTRL1 =  0xE5;       // highest PQT, address check, append_status
            PKTCTRL0 =  0x04;       // crc enabled      ( we really don't want any packets coming our way :)
            FSCTRL1 =   0x12;       // freq if
            FSCTRL0 =   0x00;
            MCSM0 =     0x10;       // autocal/no auto-cal....  hmmm...
            AGCCTRL2 |= AGCCTRL2_MAX_DVGA_GAIN;     // disable 3 highest gain settings
            macdata.mac_state = MAC_STATE_SPECAN;
            
            chan_table = rfrxbuf[0];

        case MAC_STATE_SPECAN:
            for (processbuffer = 0; processbuffer < macdata.synched_chans; processbuffer++)
            {
                /* tune radio and start RX */
                CHANNR = processbuffer;        // may not be the fastest, but otherwise we have to store FSCAL data for each channel
                RFOFF;
                RFRX;
                sleepMillis(2);

                /* read RSSI */
                chan_table[processbuffer] = (RSSI);
            }

            /* end RX */
            RFOFF;
            txdata( APP_SPECAN, SPECAN_QUEUE, (u8)macdata.synched_chans, (__xdata u8*)&chan_table[0] );
            break;

        case MAC_STATE_SYNCHING:
            // FIXME: need to compare part of the packet to desperatelySeeking;
            // FIXME: TIMEOUT??  do we just stay in SYNCHING forever1?!?
            if (rfif)
            {
                lastCode[0] = 0xd;
                IEN2 &= ~IEN2_RFIE;   // FIXME: is this ok?

                if(rfif & RFIF_IRQ_DONE)
                {
                    // FIXME: do something with desperatelySeeking here.
                    // FIXME: OR... use protocol knowledge to dynamically generate a hopping pattern from this discovered cell
                    macdata.mac_state = MAC_STATE_SYNCHED;
                    begin_hopping((u8)(rf_tLastRecv & 0xff));       // synching happens within
                    // we've received a packet with the proper sync word and settings.  
                    debug("network packet(sync)");
                    debughex16((u16)rf_tLastRecv);
                    debug((__code u8*)&rfrxbuf[rfRxCurrentBuffer][0]);

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

            __critical { rfif = 0; }
            IEN2 |= IEN2_RFIE;
            break;

        case MAC_STATE_DISCOVERY:
            // check for timeout value.  if we cross timeout, we'll return to MAC_STATE_NONHOPPING, 
            // or MAC_STATE_SYNC_MASTER.
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
                    debug((__code u8*)&rfrxbuf[processbuffer][0]);

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
                    __critical { rfif &= ~RFIF_IRQ_DONE; }
                }
            }

            __critical{ rfif = 0; }
            IEN2 |= IEN2_RFIE;
            break;

        case MAC_STATE_SYNCINGMASTER:
            // if we've done one loop, stop
            if (macdata.synched_chans >= macdata.NumChannelHops)
            {
                macdata.mac_state = MAC_STATE_SYNC_MASTER;
            }
            break;
        // perhaps we should just make this "default:"
        case MAC_STATE_SYNC_MASTER:
        case MAC_STATE_SYNCHED:
        case MAC_STATE_NONHOPPING:
            // this is where we handle the RF packet
            if (rfif)
            {
                //LED = !LED;
                lastCode[0] = 0xd;

                if(rfif & (RFIF_IRQ_DONE | RFIF_IRQ_TIMEOUT) )
                {
                    processbuffer = !rfRxCurrentBuffer;
                    if(rfRxProcessed[processbuffer] == RX_UNPROCESSED)
                    {   
                        // we've received a packet.  deliver it.
                        if (PKTCTRL0&1)     // variable length packets have a leading "length" byte, let's skip it
                        {
                            txdata(APP_NIC, NIC_RECV, (u8)rfrxbuf[processbuffer][0], (u8*)&rfrxbuf[processbuffer][1]);
                        } else {
                            txdata(APP_NIC, NIC_RECV, rfRxInfMode ? rfRxLargeLen : PKTLEN, (u8*)&rfrxbuf[processbuffer]);
                        }

                        /* Set receive buffer to processed so it can be used again */
                        rfRxProcessed[processbuffer] = RX_PROCESSED;
                    }
                    __critical { rfif &= ~( RFIF_IRQ_DONE | RFIF_IRQ_TIMEOUT );  }          // FIXME: rfif is way too easily tossed aside here...
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
    __xdata u16 len, repeat, offset;
    __xdata u8 * __xdata buf = &ep5.OUTbuf[0];
    __xdata u8 blocks;

    switch (ep5.OUTapp)
    {
        case APP_NIC:

            switch (ep5.OUTcmd)
            {
                case RFCAT_START_SPECAN:
                    // FIXME: need to consider tracking what mode we're in, and dropping back into that mode at the end.
                    // FIXME: or perhaps FHSS/MAC stuff should be take care of in the client side.
                    stop_hopping();
                    macdata.mac_state = MAC_STATE_PREP_SPECAN;
                    macdata.synched_chans = buf[0];
                    appReturn( 1, buf);
                    break;

                case RFCAT_STOP_SPECAN:
                    macdata.mac_state = MAC_STATE_NONHOPPING;
                    appReturn( 1, buf);
                    break;

                case NIC_XMIT:
                    // this needs to place buf data into the FHSS txMsgQueue    - really?
                    // certainly don't want to allow this function if we're HOPPING.  that would be baaaaaaaaad.
                    if (macdata.mac_state != MAC_STATE_NONHOPPING)
                    {
                        debug("crap, please use FHSSxmit() instead!");
                        break;
                    }
                    len = buf[0];
                    len += buf[1] << 8;
                    repeat = buf[2];
                    repeat += buf[3] << 8;
                    offset = buf[4];
                    offset += buf[5] << 8;
                    txTotal= 0;
                    buf[0] = transmit(&buf[6], len, 0, offset);
                    appReturn( 1, buf);
                    break;

                case NIC_SET_RECV_LARGE:
                    // FIXME: simply make this normal, coincide with standard makePktLen(), keep packet length in rfRxLargeLen (rename it so it's not so special)
                    
                    // configure large block receive (infinite mode)
                    // call with block size of 0 to switch off
                    rfRxLargeLen = buf[0];
                    rfRxLargeLen += buf[1] << 8;
                    if(rfRxLargeLen)
                    {
                        rfRxInfMode = 1;
                        // starting a new packet?
                        if(!rfRxTotalRXLen)
                        {
                            IdleMode();
                            rfRxTotalRXLen = rfRxLargeLen;
                            PKTLEN = (u8) (rfRxTotalRXLen % 256);
                            PKTCTRL0 &= ~PKTCTRL0_LENGTH_CONFIG;
                            PKTCTRL0 |= PKTCTRL0_LENGTH_CONFIG_INF;
                            RxMode();
                        }
                    }
                    else
                    {
                        rfRxInfMode = 0;
                        rfRxTotalRXLen = 0;
                        rfRxLargeLen = 0;
                        IdleMode();
                    }
                    txdata(ep5.OUTapp, ep5.OUTcmd, 1, (__xdata u8*)&rfRxLargeLen);
                    break;

                case NIC_SET_AES_MODE:
                    rfAESMode= buf[0];
                    appReturn( 1, buf);
                    break;

                case NIC_GET_AES_MODE:
                    appReturn( 1, (__xdata u8*) &rfAESMode);
                    break;

                case NIC_SET_AES_IV:
                    setAES(buf, ENCCS_CMD_LDIV, (rfAESMode & AES_CRYPTO_MODE));
                    appReturn( 16, buf);
                    break;

                case NIC_SET_AES_KEY:
                    setAES(buf, ENCCS_CMD_LDKEY, (rfAESMode & AES_CRYPTO_MODE));
                    appReturn( 16, buf);
                    break;

                case NIC_SET_AMP_MODE:
                    rfAmpMode= *buf;
                    rfAmpMode &= 1;
                    appReturn( 1, buf);
                    break;

                case NIC_GET_AMP_MODE:
                    appReturn( 1, (__xdata u8*) &rfAmpMode);
                    break;

                case NIC_SET_ID:
                    // fixme: sending 8 bit to 16 bit function???
                    MAC_set_NIC_ID(buf[0]);
                    appReturn( 1, buf);
                    break;

                case NIC_LONG_XMIT:
                    // load up macdata queues, follow-on with 
                    //
                    //
                    // this is duplicating our work in transmit_long().  pick one.
                    if (macdata.mac_state != MAC_STATE_NONHOPPING)
                    {
                        buf[0] = RC_RF_MODE_INCOMPAT;
                        appReturn( 1, buf);
                        break;
                    }
                    len = buf[0];
                    len += buf[1] << 8;
                    blocks = buf[2];
                    txTotal= 0;
                    buf[0] = transmit_long(&buf[3], len, blocks);
                    appReturn( 1, buf);
                    break;

                case NIC_LONG_XMIT_MORE:
                    len = buf[0];
                    if (len == 0)
                    {
                        // this is after the last chunk, wait for tx to finish and return OK
                        while (rfTxTotalTXLen && MARCSTATE == MARC_STATE_TX) 
                        {
                            sleepMillis(40); // delay to avoid race condition that will cause mis-read of rfTxTotalTXLen == 0
                        }
                        if(rfTxTotalTXLen)
                        {
                            debug("dropout final wait!");
                            debughex16(rfTxTotalTXLen);
                            debughex(g_txMsgQueue[0][0]);
                            debughex(g_txMsgQueue[1][0]);
                            lastCode[1] = LCE_DROPPED_PACKET;
                            buf[0] = RC_TX_DROPPED_PACKET;
                            LED = 0;
                            resetRFSTATE();
                            macdata.mac_state = MAC_STATE_NONHOPPING;
                            appReturn( 1, buf);
                            break;
                        }
                        LED = 0;
                        macdata.mac_state = MAC_STATE_NONHOPPING;
                        buf[0] = LCE_NO_ERROR;
                        debug("total bytes tx:");
                        debughex16(txTotal);
                        appReturn( 1, buf);
                        break;
                    }
                    // catch if we've been called out of sequence, or we've had an underrun
                    if (macdata.mac_state != MAC_STATE_LONG_XMIT)
                    {
                        debug("underrun");
                        // TX underrun
                        if(lastCode[1] == LCE_DROPPED_PACKET)
                            {
                            buf[0] = RC_TX_DROPPED_PACKET;
                            appReturn( 1, buf);
                            }
                        else
                        {
                            lastCode[1] = LCE_RF_MULTI_BUFFER_NOT_INIT;
                            buf[0] = RC_RF_MODE_INCOMPAT;
                            appReturn( 1, buf);
                        }
                        LED = 0;
                        resetRFSTATE();
                        macdata.mac_state = MAC_STATE_NONHOPPING;
                        break;
                    }
                    // add data to rolling buffer
                    buf[0] = MAC_tx(&buf[1], (__xdata u8) len);
                    // check for any other error return
                    if(buf[0] && buf[0] != RC_ERR_BUFFER_NOT_AVAILABLE)
                    {
                        debug("buffer error");
                        debughex(buf[0]);
                        LED = 0;
                        resetRFSTATE();
                        macdata.mac_state = MAC_STATE_NONHOPPING;
                    }
                    appReturn( 1, buf);
                    break;

                case FHSS_XMIT:
                    len = buf[0];
                    //len += (*buf++) << 8;
                    //repeat = *buf++;
                    //repeat += (*buf++) << 8;
                    //offset = *buf++;
                    //offset += (*buf++) << 8;
                    //transmit(buf, len, repeat, offset);
                    //MAC_tx(buf, len);
                    /////// for some strange reason, if we call this in MAC_tx it dies, but not from here. ugh.
                    if (len > MAX_TX_MSGLEN)
                    {
                        debug("FHSSxmit message too long");
                                    appReturn( 1, (__xdata u8*)&len);
                        break;
                    }

                    if (g_txMsgQueue[macdata.txMsgIdx][0] != 0)
                    {
                        debug("still waiting on the last packet");
                                    appReturn( 1, (__xdata u8*)&len);
                        break;
                    }

                    g_txMsgQueue[macdata.txMsgIdx][0] = len;
                    memcpy(&g_txMsgQueue[macdata.txMsgIdx][1], &buf[1], len);

                    if (++macdata.txMsgIdx >= MAX_TX_MSGS)
                    {
                        macdata.txMsgIdx = 0;
                    }

                    appReturn( 1, (__xdata u8*)&len);
                    break;
                    
                case FHSS_SET_CHANNELS:
                    macdata.NumChannels = (__xdata u16)buf[0];
                    if (macdata.NumChannels <= MAX_CHANNELS)
                    {
                        //buf += 2;
                        memcpy(&g_Channels[0], &buf[2], macdata.NumChannels);
                        appReturn( 2, (u8*)&macdata.NumChannels);
                    } else {
                        appReturn( 8, (__xdata u8*)"NO DEAL");
                    }
                    break;

                case FHSS_GET_CHANNELS:
                    appReturn( macdata.NumChannels, &g_Channels[0]);
                    break;

                case FHSS_NEXT_CHANNEL:
                    MAC_set_chanidx(MAC_getNextChannel());
                    appReturn( 1, &g_Channels[macdata.curChanIdx]);
                    break;

                case FHSS_CHANGE_CHANNEL:
                    PHY_set_channel(buf[0]);
                    appReturn( 1, buf);
                    break;

                case FHSS_START_HOPPING:
                    begin_hopping(0);
                    appReturn( 1, buf);
                    break;

                case FHSS_STOP_HOPPING:
                    stop_hopping();
                    appReturn( 1, buf);
                    break;

                // FIXME: do we even need g_MAC_threshold anymore?
                case FHSS_SET_MAC_THRESHOLD:
                    macdata.MAC_threshold = buf[0];
                    appReturn( 1, buf);
                    break;

                case FHSS_GET_MAC_THRESHOLD:
                    appReturn( 4, (__xdata u8*)&macdata.MAC_threshold);
                    break;

                case FHSS_SET_MAC_DATA:
                    debugx(buf);
                    debughex(buf[0]);
                    memcpy((__xdata u8*)&macdata, (__xdata u8*)*buf, sizeof(macdata));
                    appReturn( sizeof(macdata), buf);
                    break;

                case FHSS_GET_MAC_DATA:
                    macdata.MAC_timer = rf_MAC_timer;
                    appReturn( sizeof(macdata), (__xdata u8*)&macdata);
                    break;

                case FHSS_START_SYNC:
                    MAC_sync(buf[0]);
                    appReturn( 1, buf);
                    break;
                    
                case FHSS_SET_STATE:
                    // store the main timer value for beginning of this phase.
                    macdata.tLastStateChange = clock;
                    macdata.mac_state = (u8)buf[0];
                    
                    // if macdata.mac_state is > 2, make sure the T2 interrupt is set
                    // if macdata.mac_state <= 2, make sure T2 interrupt is ignored
                    switch (macdata.mac_state)
                    {
                        case MAC_STATE_NONHOPPING:
                        case MAC_STATE_DISCOVERY:
                        case MAC_STATE_SYNCHING:
                            
                            stop_hopping();
                            break;

                        case MAC_STATE_SYNCINGMASTER:
                            MAC_do_Master_scanny_thingy();
                            break;

                        case MAC_STATE_SYNCHED:
                        case MAC_STATE_SYNC_MASTER:
                            begin_hopping(0);
                            break;
                    }
                    
                    appReturn( 1, buf);
                    break;
                    
                case FHSS_GET_STATE:
                    appReturn( 1, (__xdata u8*)&macdata.mac_state);
                    break;
                    
                default:
                    appReturn( 1, buf);
                    break;
            }
            break;
    }
    //ep5.flags &= ~EP_OUTBUF_WRITTEN;                       // this allows the OUTbuf to be rewritten... it's saved until now.
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
    USBCS0 |= USBCS0_DATA_END;
#endif
}

/* this function is the application handler for endpoint 0.  it is called for all VENDOR type    *
 * messages.  currently it implements a simple debug, ping, and peek functionality.              *
 * data is sent back through calls to either setup_send_ep0 or setup_sendx_ep0 for xdata vars    *
 * theoretically you can process stuff without the IN-direction bit, but we've found it is better*
 * to handle OUT packets in appHandleEP0OUTdone, which is called when the last packet is complete*/
int appHandleEP0(__xdata USB_Setup_Header* pReq)
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
                setup_sendx_ep0((__xdata u8*)USBADDR, 40);
                break;
            case EP0_CMD_PEEKX:
                setup_sendx_ep0((__xdata u8*)pReq->wValue, pReq->wLength);
                break;
            case EP0_CMD_PING0:
                setup_send_ep0((u8*)pReq, pReq->wLength);
                break;
            case EP0_CMD_PING1:
                setup_sendx_ep0((__xdata u8*)&ep0.OUTbuf[0], 16);//ep0.OUTlen);
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

void appInitRf(void)
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
    PKTCTRL0    = 0x00; // FLEN.  for VLEN use |1 (ie.  FLEN=00, VLEN=01)
    ADDR        = 0x00;
    CHANNR      = 0x00;
    FSCTRL1     = 0x06;
    FSCTRL0     = 0x00;
    FREQ2       = 0x24;
    FREQ1       = 0x3a;
    FREQ0       = 0xf1;
    MDMCFG4     = 0xca;
    MDMCFG3     = 0xa3;
    MDMCFG2     = 0x01;
    MDMCFG1     = 0x23;
    MDMCFG0     = 0x11;
    DEVIATN     = 0x36;
    MCSM2       = 0x07;             // RX_TIMEOUT
    MCSM1       = 0x0f;             // was 'CCA_MODE RSSI below threshold unless currently recvg pkt'-3, now 'Always'-0 - always end up in RX mode
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
    PA_TABLE0   = 0xc0;


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
    IOCFG0      = 0x00; //0x06; for "write"
    //PKTCTRL1    = 0x04; // PQT threshold  - was 0x00
    //PKTCTRL0    = 0x00; // FLEN.  for VLEN use |1 (ie.  FLEN=00, VLEN=01)
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
    MCSM2       = 0x07;             // RX_TIMEOUT
    MCSM1       = 0x30;             // CCA_MODE RSSI below threshold unless currently recvg pkt - always end up in RX mode
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

