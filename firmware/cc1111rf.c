#include "cc1111rf.h"
#include "global.h"

#include <string.h>

// #define RFDMA

/* Rx buffers */
volatile __xdata u8 rfRxCurrentBuffer;
volatile __xdata u8 rfrxbuf[BUFFER_AMOUNT][BUFFER_SIZE];
volatile __xdata u8 rfRxCounter[BUFFER_AMOUNT];
volatile __xdata u8 rfRxProcessed[BUFFER_AMOUNT];

/* Tx buffers */
volatile __xdata u8 rftxbuf[BUFFER_SIZE];
volatile __xdata u8 rfTxCounter = 0;

u8 rfif;
volatile __xdata u8 rf_status;
volatile xdata u16 rf_MAC_timer;
volatile xdata u16 rf_tLastRecv;
volatile __xdata DMA_DESC rfDMA;

volatile __xdata u8 bRepeatMode = 0;

/*************************************************************************************************
 * RF init stuff                                                                                 *
 ************************************************************************************************/
void init_RF()
{
    // MAC variables
    rf_tLastRecv = 0;

    // PHY variables
    rfRxCounter[FIRST_BUFFER] = 0;
    rfRxCounter[SECOND_BUFFER] = 0;


    // setup TIMER 2  (MAC timer)
    // NOTE:
    // !!! any changes to TICKSPD will change the calculation of MAC timer speed !!!
    //
    // free running mode
    // time freq:
    //
    // TICKSPD = Fref (24mhz for cc1111, 26mhz for cc1110)
    //
    // ********************* ALSO IN appFHSSNIC.c: init_FHSS()  **************************
    CLKCON &= 0xc7;

    T2PR = 0;
    T2CTL |= T2CTL_TIP_64;  // 64, 128, 256, 1024
    T2CTL |= T2CTL_TIG;

    // RF state
    rf_status = RF_STATE_IDLE;

    /* Init DMA channel */
    DMA0CFGH = ((u16)(&rfDMA))>>8;
    DMA0CFGL = ((u16)(&rfDMA))&0xff;

    /* clear buffers */
    memset(rfrxbuf,0,(BUFFER_AMOUNT * BUFFER_SIZE));

    appInitRf();

    /* Setup interrupts */
    RFTXRXIE = 1;                   // FIXME: should this be something that is enabled/disabled by usb?
    RFIM = 0xd1;    // TXUNF, RXOVF, DONE, SFD  (SFD to mark time of receipt)
    RFIF = 0;
    rfif = 0;
    IEN2 |= IEN2_RFIE;

    /* Put radio into idle state */
    setRFIdle();

}

void setRFRx(void)
{
    RFST = RFST_SRX;
    while(!(MARCSTATE & MARC_STATE_RX));
    rf_status = RF_STATE_RX;
}

void setRFTx(void)
{
    RFST = RFST_STX;
    while(!(MARCSTATE & MARC_STATE_TX));
    rf_status = RF_STATE_TX;
}

void setRFIdle(void)
{
    RFST = RFST_SIDLE;
    while(!(MARCSTATE & MARC_STATE_IDLE));
    rf_status = RF_STATE_IDLE;
}

//************************** never used.. *****************************
int waitRSSI()
{
    u16 u16WaitTime = 0;
    while(u16WaitTime < RSSI_TIMEOUT_US)
    {
        if(PKTSTATUS & (PKTSTATUS_CCA | PKTSTATUS_CS))
        {
            return 1;
        }
        else
        {
            sleepMicros(50);
            u16WaitTime += 50;
        }
    }
    return 0;
}
//***********************************************************************/

u8 transmit(__xdata u8* buf, u16 len)
{
    //u8 uiRSSITries = 5;
	// /* Put radio into idle state */
	// setRFIdle();

	// If len is empty, assume first byte is the length
    // if we're in FIXED mode, skip the first byte
    // if we're in VARIABLE mode, make sure we copy the length byte + packet
	if(len == 0)
	{
		len = buf[0];

        switch (PKTCTRL0 & PKTCTRL0_LENGTH_CONFIG)
        {
            case PKTCTRL0_LENGTH_CONFIG_VAR:
                len++;  // we need to send the length byte too...
                break;
            case PKTCTRL0_LENGTH_CONFIG_FIX:
                buf++;  // skip sending the length byte
                break;
            default:
                break;
	    }
    }

    /* If DMA transfer, disable rxtx interrupt */
#ifndef RFDMA
	RFTXRXIE = 1;
#else
    RFTXRXIE = 0;
#endif

    // Copy userdata to tx buffer //
    memcpy(rftxbuf, buf, len);

    // Reset byte pointer //
    rfTxCounter = 0;

    /* Configure DMA struct */
#ifdef RFDMA
    {
        rfDMA.srcAddrH = ((u16)buf)>>8;
        rfDMA.srcAddrL = ((u16)buf)&0xff;
        rfDMA.destAddrH = ((u16)&X_RFD)>>8;
        rfDMA.destAddrL = ((u16)&X_RFD)&0xff;
        rfDMA.lenH = len >> 8;
        rfDMA.vlen = 0;
        rfDMA.lenL = len;
        rfDMA.trig = 19;
        rfDMA.tMode = 0;
        rfDMA.wordSize = 0;
        rfDMA.priority = 1;
        rfDMA.m8 = 0;
        rfDMA.irqMask = 0;
        rfDMA.srcInc = 1;
        rfDMA.destInc = 0;

        DMA0CFGH = ((u16)(&rfDMA))>>8;
        DMA0CFGL = ((u16)(&rfDMA))&0xff;
    }
#endif

    // FIXME: why are we using waitRSSI()? and why all the NOP();s?
    // FIXME: nops should be "while (!(DMAIRQ & DMAARM1));"
    // FIXME: waitRSSI()?  not sure about that one.
	// FIXME: doublecheck CCA enabled and that we're in RX mode
	/* Strobe to rx */
	//RFST = RFST_SRX;
    //while(!(MARCSTATE & MARC_STATE_RX));
    //* wait for good RSSI, TODO change while loop this could hang forever */
    //do
    //{
    //    uiRSSITries--;
    //} while(!waitRSSI() && uiRSSITries);

    //if(uiRSSITries)
    {
#ifdef RFDMA
        {
	        /* Arm DMA channel */
            DMAIRQ &= ~DMAARM0;
            DMAARM |= (0x80 | DMAARM0);
            NOP(); NOP(); NOP(); NOP();
            NOP(); NOP(); NOP(); NOP();
            DMAARM = DMAARM0;
            NOP(); NOP(); NOP(); NOP();
            NOP(); NOP(); NOP(); NOP();
        }
#endif
	    /* Put radio into tx state */
    	RFST = RFST_STX;
        //memcpy(rftxbuf, buf, len);
    	while(!(MARCSTATE & MARC_STATE_TX));
        return 1;
    }
    return 0;
}

void startRX(void)
{
    /* If DMA transfer, disable rxtx interrupt */
#ifdef RFDMA
    RFTXRXIE = 0;
#else
    RFTXRXIE = 1;
#endif

    /* Clear rx buffer */
    memset(rfrxbuf,0,BUFFER_SIZE);

    /* Set both byte counters to zero */
    rfRxCounter[FIRST_BUFFER] = 0;
    rfRxCounter[SECOND_BUFFER] = 0;

    /*
    * Process flags, set first flag to false in order to let the ISR write bytes into the buffer,
    *  The second buffer should flag processed on initialize because it is empty.
    */
    rfRxProcessed[FIRST_BUFFER] = RX_UNPROCESSED;
    rfRxProcessed[SECOND_BUFFER] = RX_PROCESSED;

    /* Set first buffer as current buffer */
    rfRxCurrentBuffer = 0;

    S1CON &= ~(S1CON_RFIF_0|S1CON_RFIF_1);
    RFIF &= ~RFIF_IRQ_DONE;

#ifdef RFDMA
    {
        rfDMA.srcAddrH = ((u16)&X_RFD)>>8;
        rfDMA.srcAddrL = ((u16)&X_RFD)&0xff;
        rfDMA.destAddrH = ((u16)&rfrxbuf[rfRxCurrentBuffer])>>8;
        rfDMA.destAddrL = ((u16)&rfrxbuf[rfRxCurrentBuffer])&0xff;
        rfDMA.lenH = 0;
        rfDMA.vlen = 0;
        rfDMA.lenL = 12;
        rfDMA.trig = 19;
        rfDMA.tMode = 0;
        rfDMA.wordSize = 0;
        rfDMA.priority = 1;
        rfDMA.m8 = 0;
        rfDMA.irqMask = 0;
        rfDMA.srcInc = 0;
        rfDMA.destInc = 1;

        DMA0CFGH = ((u16)(&rfDMA))>>8;
        DMA0CFGL = ((u16)(&rfDMA))&0xff;
        
        DMAIRQ &= ~DMAARM0;
        DMAARM |= (0x80 | DMAARM0);
        NOP(); NOP(); NOP(); NOP();
        NOP(); NOP(); NOP(); NOP();
        DMAARM = DMAARM0;
        NOP(); NOP(); NOP(); NOP();
        NOP(); NOP(); NOP(); NOP();
    }
#endif

    RFST = RFST_SRX;
    while(!(MARCSTATE & MARC_STATE_RX));

    RFIM |= RFIF_IRQ_DONE;
}

void stopRX(void)
{
    RFIM &= ~RFIF_IRQ_DONE;
    setRFIdle();

    DMAARM |= 0x81;                 // ABORT anything on DMA 0

    DMAIRQ &= ~1;

    S1CON &= ~(S1CON_RFIF_0|S1CON_RFIF_1);
    RFIF &= ~RFIF_IRQ_DONE;
}


void RxMode(void)
{
    if (rf_status != RF_STATE_RX)
    {
        rf_status = RF_STATE_RX;
        startRX();
    }
}

void IdleMode(void)
{
    if (rf_status == RF_STATE_RX)
    {
        stopRX();
        rf_status = RF_STATE_IDLE;
    }
}

/* Repeater mode...
    Say whut? Mode that receives a packet and then sends it into the air again :)
    Idea: Setup two DMA channels, we can use channel 0 we normally use and combine that with channel 3, because if correct 1 and 2 are used by USB
    Channel 0 will hold the RX, with one extra configuration than normally it should generate an interrupt when DMA is done.
    Channel 3 will hold the TX data, the TX data will be set to the buffer the RX puts his data in, the channel is activated by the DMA done interrupt of the receiver.
   */
void RepeaterStart()
{
    bRepeatMode = 1;
}

void RepeaterStop()
{
    bRepeatMode = 0;
}

/* End Repeater mode... */

//void dmaIntHandler(void) __interrupt DMA_VECTOR // Interrupt handler for DMA */

void rfTxRxIntHandler(void) __interrupt RFTXRX_VECTOR  // interrupt handler should transmit or receive the next byte
{   // dormant, in favor of DMA transfers (ifdef RFDMA)
    lastCode[0] = LC_RFTXRX_VECTOR;

    if(MARCSTATE == MARC_STATE_RX)
    {   // Receive Byte
        rfrxbuf[rfRxCurrentBuffer][rfRxCounter[rfRxCurrentBuffer]++] = RFD;
        if(rfRxCounter[rfRxCurrentBuffer] >= BUFFER_SIZE || rfRxCounter[rfRxCurrentBuffer] == 0)
        {
            rfRxCounter[rfRxCurrentBuffer] = BUFFER_SIZE-1;
        }
    }
    else if(MARCSTATE == MARC_STATE_TX)
    {  // Transmit Byte
        if(rftxbuf[rfTxCounter] != 0)
        {
            RFD = rftxbuf[rfTxCounter++];
        }
    }
    RFTXRXIF = 0;
}

void rfIntHandler(void) __interrupt RF_VECTOR  // interrupt handler should trigger on rf events
{
    // which events trigger this interrupt is determined by RFIM (set in init_RF())
    // note: S1CON should be cleared before handling the RFIF flags.
    lastCode[0] = LC_RF_VECTOR;
    S1CON &= ~(S1CON_RFIF_0 | S1CON_RFIF_1);
    rfif |= RFIF;

    if (RFIF & RFIF_IRQ_SFD)
    {
        // mark the last time we received a packet.  this will be used for MAC layer decisions in 
        // some protocols like FHSS
        rf_tLastRecv = T2CT | (rf_MAC_timer << 8);
        RFIF &= ~RFIF_IRQ_SFD;
    }

    if (RFIF & ( RFIF_IRQ_DONE | RFIF_IRQ_RXOVF | RFIF_IRQ_TIMEOUT ))
    {
        // we want *all zee bytezen!*
        if(rf_status == RF_STATE_TX)
        {
            // rearm the DMA?  not sure this is a good thing.
            DMAARM |= 0x81;
        }
        else
        {

            // FIXME: rfRxCurrentBuffer is used for both recv and sending on.... this should be separate.
            if(rfRxProcessed[!rfRxCurrentBuffer] == RX_PROCESSED)
            {
                // EXPECTED RESULT - RX complete.
                //
                /* Clear processed buffer */
                //memset(rfrxbuf[!rfRxCurrentBuffer],0,BUFFER_SIZE);      // FIXME: do we want to waste cycles on this?
                /* Switch current buffer */
                rfRxCurrentBuffer ^= 1;
                rfRxCounter[rfRxCurrentBuffer] = 0;
                /* Set both buffers to unprocessed */
                rfRxProcessed[FIRST_BUFFER] = RX_UNPROCESSED;
                rfRxProcessed[SECOND_BUFFER] = RX_UNPROCESSED;
#ifdef RFDMA
                {
                    /* Switch DMA buffer */
                    rfDMA.destAddrH = ((u16)&rfrxbuf[rfRxCurrentBuffer])>>8;
                    rfDMA.destAddrL = ((u16)&rfrxbuf[rfRxCurrentBuffer])&0xff;
                    /* Arm DMA for next receive */
                    DMAARM = DMAARM0;
                    NOP(); NOP(); NOP(); NOP();
                    NOP(); NOP(); NOP(); NOP();
                }
#endif
            }
            else
            {
                // contingency - Packet Not Handled!
                /* Main app didn't process previous packet yet, drop this one */
                LED = !LED;
                //REALLYFASTBLINK();
                //memset(rfrxbuf[rfRxCurrentBuffer],0,BUFFER_SIZE);
                rfRxCounter[rfRxCurrentBuffer] = 0;
                LED = !LED;
            }
        }
        RFIF &= ~(RFIF_IRQ_DONE | RFIF_IRQ_TIMEOUT);        // OVF needs to be handled next...
    }

    // contingency - RX Overflow
    if(RFIF & RFIF_IRQ_RXOVF)
    {
        //REALLYFASTBLINK();
        // RX overflow, only way to get out of this is to restart receiver //
        //resetRf();
        lastCode[1] = LCE_RF_RXOVF;
        LED = !LED;

        RFST = RFST_SIDLE;
        while(!(MARCSTATE & MARC_STATE_IDLE));
        RFST = RFST_SRX;
        while(!(MARCSTATE & MARC_STATE_RX));

        LED = !LED;
        RFIF &= ~RFIF_IRQ_RXOVF;
    }
    // contingency - TX Underflow
    if(RFIF & RFIF_IRQ_TXUNF)
    {
        // Put radio into idle state //
        lastCode[1] = LCE_RF_TXUNF;
        LED = !LED;

        RFST = RFST_SIDLE;
        while(!(MARCSTATE & MARC_STATE_IDLE));
        RFST = RFST_SRX;

        while(!(MARCSTATE & MARC_STATE_RX));
        LED = !LED;

        //resetRf();
        RFIF &= ~RFIF_IRQ_TXUNF;
    }
}
