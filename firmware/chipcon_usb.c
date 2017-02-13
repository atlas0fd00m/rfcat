#include "global.h"
#include "cc1111usb.h"
#include "chipcon_dma.h"
#include "bootloader.h"


/*************************************************************************************************
 * welcome to the chipcon_usb library.
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

extern u8 transmit(__xdata u8* __xdata  buf, u16 len, u16 repeat, u16 offset);

USB_STATE usb_data;
__xdata u8  usb_ep0_OUTbuf[EP0_MAX_PACKET_SIZE];                  // these get pointed to by the above structure
__xdata u8  usb_ep5_OUTbuf[EP5OUT_BUFFER_SIZE];                   // these get pointed to by the above structure
__xdata USB_EP_IO_BUF     ep0;
__xdata USB_EP_IO_BUF     ep5;
__xdata u8 appstatus;

__xdata u8   ep0req;
__xdata u16  ep0len;
__xdata u16  ep0value;

//__xdata dmacfg_t usbdma;
__xdata DMA_DESC *usbdma;
__data u8 usbdmachan, usbdmaarm;
//__xdata u8 usbdmar[8];

__xdata int (*cb_ep0outdone)(void);
__xdata int (*cb_ep0out)(void);
__xdata int (*cb_ep0vendor)(USB_Setup_Header* __xdata );
__xdata int (*cb_ep5)(void);

#ifdef SDCC
  __code u8 sdccver[] = "SDCCv" QUOTE(SDCC);
#else 
  #ifdef __SDCC
    __code u8 sdccver[] = "SDCCv" QUOTE(__SDCC);
  #else
    __code u8 sdccver[] = "NON-SDCC";
  #endif
#endif

// BUILD_VERSION is passed in -D from Makefile
__code u8 buildname[] = {
#ifdef DONSDONGLES
    'D','O','N','S','D','O','N','G','L','E',' ','r',ASCII_LONG(BUILD_VERSION),'\x00',
#elif defined YARDSTICKONE
    'Y','A','R','D','S','T','I','C','K','O','N','E',' ','r',ASCII_LONG(BUILD_VERSION),'\x00',
#elif defined CHRONOSDONGLE
    'C','H','R','O','N','O','S',' ','r',ASCII_LONG(BUILD_VERSION),'\x00',
#else
    'I','M','M','E',' ','r',ASCII_LONG(BUILD_VERSION),'\x00',
#endif
};

// USB endpoint
#ifdef DONSDONGLES
    #define ID_VENDOR      0x1D50
    #define ID_PRODUCT     0x6048
    #define MANU_LEN       12
    #define MANUFACTURER   'R',0,'f',0,'C',0,'a',0,'t',0
    #define PROD_LEN       24
    #define PRODUCT_NAME   'D',0,'o',0,'n',0,'s',0,' ',0,'D',0,'o',0,'n',0,'g',0,'l',0,'e',0
#elif YARDSTICKONE
    #define ID_VENDOR      0x1D50
    #define ID_PRODUCT     0x605b
    #define MANU_LEN       40
    #define MANUFACTURER   'G',0,'r',0,'e',0,'a',0,'t',0,' ',0,'S',0,'c',0,'o',0,'t',0,'t',0,' ',0,'G',0,'a',0,'d',0,'g',0,'e',0,'t',0,'s',0
    #define PROD_LEN       30
    #define PRODUCT_NAME   'Y',0,'A',0,'R',0,'D',0,' ',0,'S',0,'t',0,'i',0,'c',0,'k',0,' ',0,'O',0,'n',0,'e',0
#elif defined CHRONOSDONGLE
    #define ID_VENDOR      0x1D50
    #define ID_PRODUCT     0x6047
    #define MANU_LEN       12
    #define MANUFACTURER   'R',0,'f',0,'C',0,'a',0,'t',0
    #define PROD_LEN       30
    #define PRODUCT_NAME   'C',0,'h',0,'r',0,'o',0,'n',0,'o',0,'s',0,' ',0,'D',0,'o',0,'n',0,'g',0,'l',0,'e',0
#else
    #define ID_VENDOR      0x0451
    #define ID_PRODUCT     0x4715
    #define MANU_LEN       36
    #define MANUFACTURER   'a',0, 't',0, 'l',0, 'a',0, 's',0, ' ',0, 'i', 0 , 'n', 0 , 's', 0 , 't', 0 , 'r', 0 , 'u', 0 , 'm', 0 , 'e', 0 , 'n', 0 , 't', 0 , 's', 0 
    #define PROD_LEN       28
    #define PRODUCT_NAME   'C', 0, 'C', 0, '1', 0, '1', 0, '1', 0, '1', 0, ' ', 0, 'U', 0, 'S', 0, 'B', 0, ' ', 0, 'n', 0, 'i', 0, 'c', 0
#endif

int _usb_internal_handle_vendor(USB_Setup_Header* __xdata  pReq);
// state tracking:
// * appstatus
// * usb_data.usbstatus  - usb state overall...  (IDLE, SUSPEND, RESUME, RESET)
// * ep#iobuf.ep_status  - endpoint status

/* txdata is used for communicating back to the host over USB.  
 * return:  0 on success
 *          -1 on failure
 */
int txdata(u8 app, u8 cmd, u16 len, __xdata u8* dataptr)      // assumed EP5 for application use
    // gonna try this direct this time, and ignore all the "state tracking" for the endpoint.
    // wish me luck!  this could horribly crash and burn.
{
    u16 loop;
    u8 firsttime=1;
    USBINDEX=5;

    lastCode[0] = LC_TXDATA_START;

    while (len>0)
    {
        // if we do this in the loop, for some reason ep5.flags never clears between frames.  
        // don't know why since this bit is cleared in the USB ISR.
        loop = TXDATA_MAX_WAIT;
        //while (ep5.flags & EP_INBUF_WRITTEN && loop>0)                 // has last msg been recvd?
        //LED = 1;    //FIXME: DEBUG
        while (USBCSIL & USBCSIL_INPKT_RDY) // && loop>0)                 // has last msg been recvd?
        {
            //REALLYFASTBLINK();
            lastCode[1] = LCE_USB_EP5_TX_WHILE_INBUF_WRITTEN;
            loop--;
        }
        //LED = 0;    //FIXME: DEBUG
        
        // if USB is still not ready... fail.  this should only happen when the USB is disconnected anyway <crosses fingers>
        //  ODD POINT OF INTEREST: INFINITE MODE FAILS IF WE REMOVE THIS... ??
        if (!loop)
        {
            blink(1000, 1000);
            return -1;
        }
        
        // first time through, we send the header.    
        if (firsttime==1)
        {                                                                   // first time through only please
            firsttime=0;
            USBF5 = 0x40;
            USBF5 = app;
            USBF5 = cmd;
            USBF5 = len & 0xff;
            USBF5 = len >> 8;
            if (len>EP5IN_MAX_PACKET_SIZE-5)
                loop=EP5IN_MAX_PACKET_SIZE-5;
            else
                loop=len;

        } else {
            if (len>EP5IN_MAX_PACKET_SIZE)
                loop=EP5IN_MAX_PACKET_SIZE;
            else
                loop=len;
        }



        DMAARM |= 0x80 + usbdmaarm;
        usbdma->srcAddrH = ((u16)dataptr)>>8;
        usbdma->srcAddrL = ((u16)dataptr)&0xff;
        usbdma->destAddrH = 0xde;     //USBF5 == 0xde2a
        usbdma->destAddrL = 0x2a;
        usbdma->lenL = loop;
        usbdma->lenH = 0;
        usbdma->srcInc = 1;
        usbdma->destInc = 0;
        DMAARM |= usbdmaarm;
        DMAREQ |= usbdmaarm;

        while (!(DMAIRQ & usbdmaarm));
        DMAIRQ &= ~usbdmaarm;
        
        USBINDEX=5;
        USBCSIL |= USBCSIL_INPKT_RDY;

        len -= loop;
        dataptr += loop;
        lastCode[0] = LC_TXDATA_COMPLETED_FRAME;

    }
    lastCode[0] = LC_TXDATA_COMPLETED_MESSAGE;
    return(0);
}


//! waitForUSBsetup() is a helper function to allow the usb stuff to settle before real app processing happens.
void waitForUSBsetup() 
{
    while ((usb_data.usbstatus == USB_STATE_UNCONFIGURED ))
    {
        usbProcessEvents();

    }
}


/*************************************************************************************************
 *  here begins the initialization stuff... this shouldn't change much between firmwares or      *
 *  devices.                                                                                     *
 *************************************************************************************************/

/* initialize the USB subsystems */
void usb_init(void)
{
    USB_RESET();

    // setup Interrupt Flag MASKs... we want all interrupts at the moment.  change to your liking)
    USBCIE = 0xf7;          // skip Start Of Frame (SOFIF).  it's basically a keep-alive packet to keep the device from entering SUSPEND.  
    USBIIE = 0xff;
    USBOIE = 0xff;

    // setup interrupt behaviors
    PICTL   |= PICTL_P0IENH;                // must have this enabled to resume from suspend
    PICTL   &= ~PICTL_P0ICON;               // enable interrupts on rising edge
    P0IE    = 1;                            // enable the p0 interrupt flag  (IEN1 is bit-accessible)
    IEN2    |= IEN2_USBIE;                  // enable the USB interrupt flag (IEN2 is *not* bit-accessible)

    USB_RESUME_INT_CLEAR();                 // P0IFG= 0; P0IF= 0
    USB_INT_CLEAR();                        // P2IFG= 0; P2IF= 0;

    // set usb interrupt priority to 3
    IP0 |= BIT1;
    IP1 |= BIT1;


    // usb dma
    // these are now set in initDMA()
    //DMA1CFGH = ((u16)(&usbdma))>>8;
    //DMA1CFGL = ((u16)(&usbdma))&0xff;
// anything that is static 0 doesn't need to be explicitly set as dma configs start all 0
//    usbdma->vlen = 0;
//    usbdma->wordSize = 0;
    usbdma->lenH = 0;
    usbdma->tMode = 1;
//    usbdma->trig = 0;
    usbdma->irqMask = 1;
//    usbdma->m8 = 0;
    usbdma->priority = 1;
    // when used, the following must be set before triggering:
    // usbdma.srcaddr
    // usbdma.dstaddr
    // usbdma.len    // we're using fixed length transfers
    // usbdma.srcinc
    // usbdma.dstinc
    //  then trigger using DMAREQ


    //USBPOW |= USBPOW_SUSPEND_EN;          // ok, no.
    USBPOW &= ~USBPOW_SUSPEND_EN;           // i don't *wanna* go to sleep if the usb bus is idle for 3ms.  at least not yet.

    usb_data.config = 0;                    // start out unconfigured
    usb_data.event = 0;
    usb_data.usbstatus  = USB_STATE_UNCONFIGURED;   // this tracks the status of our USB Controller


    // configure EP0
    USBINDEX = 0;
    USBMAXI  = (EP0_MAX_PACKET_SIZE+7)>>3;      // these registers live in incrememnts of 8 bytes.  
    USBMAXO  = (EP0_MAX_PACKET_SIZE+7)>>3;      // these registers live in incrememnts of 8 bytes.  
    ep0.epstatus   =  EP_STATE_IDLE;       // this tracks the status of our endpoint 0
    ep0.flags      =  0;                   // reset flags for the OUT (recv) buffer
    ep0.INbytesleft=  0;
    ep0.OUTbuf     =  &usb_ep0_OUTbuf[0];
    ep0.OUTlen     =  0;
    ep0.OUTapp     =  0;
    ep0.OUTcmd     =  0;
    ep0.OUTbytesleft = 0;


    // configure EP5 (data endpoint)
    USBINDEX = 5;
    USBMAXI  = (EP5IN_MAX_PACKET_SIZE+7)>>3;    // these registers live in incrememnts of 8 bytes.  
    USBMAXO  = (EP5OUT_MAX_PACKET_SIZE+7)>>3;   // these registers live in incrememnts of 8 bytes.  
    //USBCSOH |= USBCSOH_AUTOCLEAR;               // when we drain the FIFO, automagically tell host
    //USBCSIH |= USBCSIH_AUTOSET;                 // when the buffer is full, automagically tell host
    USBCSIH |= USBCSIH_IN_DBL_BUF;
    USBCSOH |= USBCSOH_OUT_DBL_BUF;
    ep5.epstatus   =  EP_STATE_IDLE;       // this tracks the status of our endpoint 5
    ep5.flags      =  0;
    ep5.INbytesleft=  0;
    ep5.OUTbuf     =  &usb_ep5_OUTbuf[0];
    ep5.OUTlen     =  0;
    ep5.OUTapp     =  0;
    ep5.OUTcmd     =  0;
    ep5.OUTbytesleft = 0;


   
    USB_INT_ENABLE();     // Enables USB Interrupts to call an ISR

}




/*************************************************************************************************
 * main usb startup code                                                                             *
 *************************************************************************************************/
void initUSB(void)
{
    usbdmachan= getDMA();               // allocate a DMA channel
    usbdmaarm= (DMAARM0 << usbdmachan); // pre-calculate arming bit
    usbdma= &dma_configs[usbdmachan];   // point our DMA descriptor at allocated channel descriptor
    lastCode[0] = LC_USB_INITUSB;
    //USB_ENABLE();                       // enable our usb controller
    usb_init();                         // setup the usb controller settings

}

// usb_up() pulls up the USB_PULLUP_ENABLE signal, which makes the device show up to the Host
void usb_up(void)
{
    USB_PULLUP_ENABLE();                // enable pullup resistor indicating that we are a real usb device
}

// usb_down() pulls down the USB_PULLUP_ENABLE signal, which makes the device go away
void usb_down(void)
{
    USB_PULLUP_DISABLE();                // enable pullup resistor indicating that we are a real usb device
}

/*************************************************************************************************
 * main USB handler/enabler code.                                                                *
 *************************************************************************************************/
int setup_send_ep0(u8* __xdata  payload, u16 length)
{
    if (ep0.epstatus != EP_STATE_IDLE)
    {
        /* catestropic error.  *must* fix! */
        blink(1000,1000);
        blink(1000,1000);
        blink(1000,1000);
        return -1;
    }

    ep0.INbuf = payload;
    ep0.INbytesleft = length;
    ep0.epstatus = EP_STATE_TX;

    return 0;
}

/* send from XDATA */
int setup_sendx_ep0(__xdata u8* __xdata  payload, u16 length)
{
    if (ep0.epstatus != EP_STATE_IDLE)
    {
        /* catestropic error.  *must* fix! */
        blink(1000,1000);
        blink(1000,1000);
        blink(1000,1000);
        return -1;
    }

    ep0.INbuf = payload;
    ep0.INbytesleft = length;
    ep0.epstatus = EP_STATE_TX;

    return 0;
}

void usb_arm_ep0IN(){
    /***********************
     * should queue up and send one packet this run.... and recalculate bytesleft so we hit the next packet next run.
     */
    u8  tlen;
    u8  csReg = USBCS0_INPKT_RDY;

    USBINDEX = 0;
    
    if (ep0.INbytesleft > EP0_MAX_PACKET_SIZE)
        tlen = EP0_MAX_PACKET_SIZE;
    else
    {
        tlen = ep0.INbytesleft;
        csReg |= USBCS0_DATA_END;
    }

    // FIXME:   IMPLEMENT DMA FOR THESE TRANSFERS
    ep0.INbytesleft -= tlen;
    for (; tlen>0; tlen--) {               // FIXME: Use DMA
        USBF0 = *ep0.INbuf;
        ep0.INbuf++;
    }
    USBCS0  |= csReg;
    if (ep0.INbytesleft == 0)
        ep0.epstatus = EP_STATE_IDLE;
}


u8 setup_recv_ep0(){
    ep0.epstatus = EP_STATE_RX;
    return 0;
}

u16 usb_recv_ep0OUT(){
    /********************************************************************************************
     * handle receipt of one packet and set flags
     * if another packet has yet to be handled by the application (ie. received through this 
     * function but not acted upon or cleared), return -1
     *******************************************************************************************/
    u16 loop;

    __xdata u8* __xdata  payload = &ep0.OUTbuf[0];
    while (! USBCS0 & USBCS0_OUTPKT_RDY);           // wait for it...

    USBINDEX = 0;
    loop = USBCNT0;
    ep0.OUTlen = loop;

    if (ep0.flags & EP_OUTBUF_WRITTEN)
    {
        ep0.epstatus = EP_STATE_STALL;            // FIXME: don't currently handle stall->idle...
        USBCS0 |= USBCS0_SENT_STALL;
        return -1;
    }
    ep0.flags |= EP_OUTBUF_WRITTEN;            // hey, we've written here, don't write again until this is cleared by a application handler

    if (ep0.OUTlen>EP0_MAX_PACKET_SIZE)
        blink(300,300);
        //ep0.OUTlen = EP0_MAX_PACKET_SIZE;

    ///////////////////////////////  FIXME: USE DMA //////////////////////////////////////////
    //blink_binary_baby_lsb(ep0.OUTlen, 8);
    for (loop=ep0.OUTlen; loop>0; loop--){
        *payload++ = USBF0;
    }
    //////////////////////////////////////////////////////////////////////////////////////////
   
    // handle each packet
    if (cb_ep0out)
        cb_ep0out();

    if (ep0.OUTlen < EP0_MAX_PACKET_SIZE)
    {
        if (cb_ep0outdone)
            cb_ep0outdone();

        USBCS0 |= USBCS0_DATA_END;
        ep0.epstatus = EP_STATE_IDLE;
    }
    USBCS0 |= USBCS0_CLR_OUTPKT_RDY;
    return ep0.OUTlen;
    
}

//void registerCb_ep0OutDone(void (*callback)(void))
//{
//    cb_ep0outdone = callback;
//}

//void registerCb_ep0Out(void (*callback)(void))
//{
//    cb_ep0out = callback;
//}

void registerCb_ep0Vendor(int (*callback)(USB_Setup_Header*))
{
    cb_ep0vendor = callback;
}

void registerCb_ep5(int (*callback2)(void))
{
    cb_ep5 = callback2;
}


/*************************************************************************************************
 * administrative USB handler functions                                                          *
 *************************************************************************************************/
void usbGetConfiguration()
{
    setup_send_ep0(&usb_data.config, 1);
}

void usbSetConfiguration(USB_Setup_Header* __xdata  pReq)
{
    usb_data.config = pReq->wValue & 0xff;
    usb_data.usbstatus = USB_STATE_IDLE;
}

__xdata u8* usbGetDescriptorPrimitive(u8 wantedType, u8 index){

    __xdata u8 counter = 0;
    __xdata u8 descType;
#ifdef BOOTLOADER_SIZE
    __xdata u8* __xdata  tmpdesc;
#endif
    __xdata u8* descPtr = (__xdata u8*)&USBDESCBEGIN;                 // start of data... sorta

    descType = *(descPtr+1);


    while (descType != 0xff ){
        counter ++;

        if (descType == wantedType)
        {
#ifdef BOOTLOADER_SIZE
            tmpdesc = BOOTLOADER_SIZE;
            if (wantedType == USB_DESC_STRING 
                    && index == USB_SERIAL_STRIDX_BYTE
                    && *((__xdata u32*)(tmpdesc-32)) == 0x73616c40) //@las
            {
                descPtr = (__xdata u8*)(tmpdesc-28);
                descType = 0xff;
                index = 0;
                break;
            }
            else
#endif
            if (index == 0){
                descType = 0xff;                            // WARNING: destructive.  go directly to ret, do not pass go, do not collect $200
            } else {
                index--;
                descPtr = descPtr + (u8)*descPtr;
                descType = *(descPtr+1);
            }
        } else 
        {
            descPtr = descPtr + (u8)*descPtr;
            descType = *(descPtr+1);
        }
    }
    //blink(50,30);
    return descPtr;
}

void usbGetDescriptor(USB_Setup_Header* __xdata  pReq)
{
    __xdata u8* __xdata  buffer;                                  // this will point to the start of the descriptor (in code) when we're done
    u16 length;

    switch ((pReq->wValue)>>8){
        case USB_DESC_OTHER_SPEED_CFG:
            pReq->wValue &= 0xaf;   // strip the "other_speed" and just use config
        case USB_DESC_CONFIG:
            buffer = usbGetDescriptorPrimitive((pReq->wValue)>>8, (pReq->wValue)&0xff);
            length = (u16)*(buffer+2);  // use "total config/package size".  this will be reduced if necessary
            break;
        default:
            buffer = usbGetDescriptorPrimitive((pReq->wValue)>>8, (pReq->wValue)&0xff);
            length = (u8)*(buffer);
            break;
    }
    if (length > pReq->wLength)
    {
        length = pReq->wLength;
    }

    if (! length)       // desired descriptor not found.
    {
        USBCS0 |= USBCS0_SEND_STALL;
        //blink_binary_baby_lsb(0x42, 8);
        //blink_binary_baby_lsb(pReq->wValue, 16);
        //blink(700,100);
        //blink(700,100);
    }

    setup_sendx_ep0(buffer, length);
    
}

#ifdef VCOMTEST
__xdata static struct usb_line_coding usb_line_codings = {115200, 0, 0, 8};
#endif

//////////////////////////////////////////////////////////////////////////////////////////////////
// handler for activity on endpoint 0.  THIS IS VERY VERY IMPORTANT!                            //
//                                                                                              //
// the handler is broken down into some administrative handlers, then the state engine for the  //
// endpoint 0.  IDLESTATE is the home state
// all configuration, control, and announcement to the OS is done through endpoint 0            //
// basic flow is that 8 bytes (setup packet) are read in from the host which identify what the  //
// transaction is supposed to be.  individual handlers are then called to respond or react to   //
// the purpose of the command.  these 8 bytes are clearly documented in the USB spec            //
// for more information, read USB IN A NUTSHELL, which can be downloaded from the Internet.     //
// google it.                                                                                   //
//////////////////////////////////////////////////////////////////////////////////////////////////
void handleCS0(void)
{
    USB_Setup_Header req;
    u8* pReq = (u8*)(&req);
    u8  csReg;
    u8  loop;
    //u16 val;
    USBINDEX = 0;

    //** DEBUG: GETS HERE.... doesn't have to do anything in particular to show up in Linux logs...**/
    csReg = USBCS0;

    // check if the last xaction ended prematurely by a new setup packet
    if (csReg & USBCS0_SETUP_END) 
    {
        ep0.epstatus = EP_STATE_IDLE;
        USBCS0 |= USBCS0_CLR_SETUP_END;
    }

    // handle a stall packet
    if (csReg & USBCS0_SENT_STALL) 
    {
        USBCS0 = 0x00;
        lastCode[1] = LCE_USB_EP0_SENT_STALL;
        ep0.epstatus = EP_STATE_IDLE;
        blink(20,20);
    }
    
    if (ep0.epstatus == EP_STATE_STALL)
    {
        blink(50,50);
        ep0.epstatus = EP_STATE_IDLE;
    }



    ///////// begin handlers based on EP0 state.
    if (ep0.epstatus == EP_STATE_IDLE)
    {

        if (csReg & USBCS0_OUTPKT_RDY)                          // do we have a SETUP packet ready for us to consume?
        {
            // read in Setup Token Packet
            USBINDEX = 0;
            loop = USBCNT0;
            for (; loop; loop--,pReq++) {               // FIXME: Use DMA
                *pReq = USBF0;
            }

            // handle by target and direction - skeleton shell... only interested in getting 
            // noticed and allowed to send shit down the usb interface!
            // Device Requests
            if (req.bmRequestType & USB_BM_REQTYPE_DIRMASK)                       // should be *sending* data, if any
            {   
                //  if there's any length requirement, enter TX mode
                if (req.wLength)
                    ep0.epstatus == EP_STATE_TX;

                switch(req.bmRequestType & USB_BM_REQTYPE_TYPEMASK)
                {
                    case USB_BM_REQTYPE_TYPE_STD:               //  STANDARD type

                        loop = req.bmRequestType & USB_BM_REQTYPE_TGTMASK;
                        if (loop == USB_BM_REQTYPE_TGT_DEV)
                        {
                            switch (req.bRequest){
                                // return wLength bytes of Device/Config/Interface/EP info (wValue information)
                                case USB_GET_DESCRIPTOR:        usbGetDescriptor(&req); break;
                                case USB_GET_CONFIGURATION:     usbGetConfiguration(); break;
                                // send back 0x0000 for GET_STATUS (not self-powered and not remote-wake-up capable.
                                case USB_GET_STATUS:            setup_send_ep0("\x00\x00", 2);      break;
                                default:                        debugEP0Req((u8*)&req); 
                            }
                        }
                        // Interface Requests
                        else if (loop == USB_BM_REQTYPE_TGT_INTF)
                        {
                            switch (req.bRequest){
                                case USB_GET_STATUS:            setup_send_ep0("\x00\x00", 2);      break;
                                case USB_GET_INTERFACE:         setup_send_ep0("\x00", 1);          break;
                                default:                        USBCS0 |= USBCS0_SEND_STALL;debugEP0Req((u8*)&req); 
                            }
                        }
                        // EndPoint Requests
                        else if (loop == USB_BM_REQTYPE_TGT_EP)
                        {
                            switch (req.bRequest){
                                case USB_GET_STATUS:            setup_send_ep0("\x00\x00", 2);      break;
                                case USB_SYNCH_FRAME:           break;
                                default:                        USBCS0 |= USBCS0_SEND_STALL;debugEP0Req((u8*)&req); 
                            }
                        }
                        // Other Requests
                        else if (loop == USB_BM_REQTYPE_TGT_OTHER)
                        {
                            switch (req.bRequest){
                                case USB_GET_STATUS:            setup_send_ep0("\x00\x00", 2); break;
                                default:                        USBCS0 |= USBCS0_SEND_STALL;debugEP0Req((u8*)&req); 
                            }
                        } else {
                            // We reached Never Never Land.  Stall
                            debugEP0Req((u8*)&req);
                            USBCS0 |= USBCS0_SEND_STALL;
                        }
                        break;
                    case USB_BM_REQTYPE_TYPE_CLASS:             // CLASS type
#ifdef VCOMTEST
                        switch (req.bRequest){
                            case SET_LINE_CODING:
                                setup_send_ep0((__xdata u8 *) &usb_line_codings, 7);
                                break;
                            case GET_LINE_CODING:
                                setup_send_ep0((u8 *) &usb_line_codings, 7);
                                break;
                            case SET_CONTROL_LINE_STATE:
                                break;
                        }
#else
                        USBCS0 |= USBCS0_SEND_STALL;
#endif
                        //debugEP0Req((u8*)&req);
                        break;
                    case USB_BM_REQTYPE_TYPE_VENDOR:            // VENDOR type
                        if (cb_ep0vendor)
                        {
                            //ep0.epstatus = EP_STATE_TX;
                            cb_ep0vendor(&req);
                        }
                        else
                        {
                            _usb_internal_handle_vendor(&req);
                        }
                        break;
                    case USB_BM_REQTYPE_TYPE_RESERVED:          // RESERVED
                        USBCS0 |= USBCS0_SEND_STALL;
                        debugEP0Req((u8*)&req);
                }
            } else {                                            // should be *receiving* data, if any
                //  if there's any length requirement, enter RX mode
                if (req.wLength)
                    ep0.epstatus == EP_STATE_RX;

                switch(req.bmRequestType & USB_BM_REQTYPE_TYPEMASK)
                {
                    case USB_BM_REQTYPE_TYPE_STD:               // STANDARD type
                        loop = req.bmRequestType & USB_BM_REQTYPE_TGTMASK;
                        if (loop == USB_BM_REQTYPE_TGT_DEV)
                        {
                            switch (req.bRequest){
                                case USB_SET_ADDRESS:
                                    USBADDR = req.wValue;       break;
                                case USB_SET_CONFIGURATION:
                                    usbSetConfiguration(&req);  break;
                                // return wLength bytes of Device/Config/Interface/EP info (wValue information)
                                case USB_CLEAR_FEATURE:         break;
                                case USB_SET_FEATURE:           break;
                                case USB_SET_DESCRIPTOR:        break;
                                default:
                                    debugEP0Req((u8*)&req);
                                    USBCS0 |= USBCS0_SEND_STALL;
                            }
                        }
                        // Interface Requests
                        else if (loop == USB_BM_REQTYPE_TGT_INTF)
                        {
                            switch (req.bRequest){
                                case USB_CLEAR_FEATURE:     break;
                                case USB_SET_FEATURE:       break;
                                case USB_SET_INTERFACE:     break;
                                default:
                                    debugEP0Req((u8*)&req);
                                    USBCS0 |= USBCS0_SEND_STALL;
                            }
                        }
                        // EndPoint Requests
                        else if (loop == USB_BM_REQTYPE_TGT_EP)
                        {
                            switch (req.bRequest){
                                case USB_CLEAR_FEATURE:     break;
                                case USB_SET_FEATURE:       break;
                                default:
                                    debugEP0Req((u8*)&req);
                                    USBCS0 |= USBCS0_SEND_STALL;
                            }
                        } else {
                            USBCS0 |= USBCS0_SEND_STALL;
                            debugEP0Req((u8*)&req);
                        }
                        break;
                    case USB_BM_REQTYPE_TYPE_CLASS:             // CLASS type
                        debugEP0Req((u8*)&req);
                        USBCS0 |= USBCS0_SEND_STALL;
                        break;
                    case USB_BM_REQTYPE_TYPE_VENDOR:            // VENDOR type
                        if (cb_ep0vendor)
                        {
                            //ep0.epstatus = EP_STATE_RX;
                            cb_ep0vendor(&req);
                        }
                        else
                        {
                            _usb_internal_handle_vendor(&req);
                        }
                        break;
                    case USB_BM_REQTYPE_TYPE_RESERVED:          // RESERVED type
                        USBCS0 |= USBCS0_SEND_STALL;
                        debugEP0Req((u8*)&req);
                }

            }       // else *receive*
            USBCS0 |= USBCS0_CLR_OUTPKT_RDY;                    // clear the bit, we got it.
            if (req.wLength == 0x0)
                USBCS0 |= USBCS0_DATA_END;                      // if the length is 0, signal that we got it and we're good.  (where did i come up with this?!?)
        }       // USBCS0_OUTPKT_RDY
    }       // EP_STATE_IDLE


    
    if (ep0.epstatus == EP_STATE_TX)
    {
        usb_arm_ep0IN(); 
    }
    if (ep0.epstatus == EP_STATE_RX)
    {
        usb_recv_ep0OUT();
    }
    
}

int _usb_internal_handle_vendor(USB_Setup_Header* __xdata  pReq)
{
#ifdef VIRTUAL_COM
    pReq = 0;
#else
    u16 loop;
    __xdata u8* __xdata  dst;

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
    else                        // OUT from host
    {
        switch (ep0req)
        {
            case EP0_CMD_POKEX:     // poke
                
                dst = (__xdata u8*) pReq->wValue;

                USBINDEX = 0;
                loop = USBCNT0;
                blink_binary_baby_lsb(loop, 8);

                for (; loop>0; loop--)
                {
                    *dst++ = USBF0;
                }
                break;
        }

        // must be done with the buffer by now...
        ep0.flags &= ~EP_OUTBUF_WRITTEN;
    }
#endif
    return 0;
}


int handleOUTEP5(void)
{
    // client is sending commands... or looking for information...  status... whatever...
    u16 len;
    __xdata u8* ptr; 
    if (ep5.flags & EP_OUTBUF_WRITTEN)                     // have we processed the last OUTbuf?  don't want to clobber it.
    {
        // // // // FIXME: forget the second memory buffering... rework this to use just the buffering in the usb controller // // // // 
        // FIXME: differentiate between SENT_STALL and SEND_STALL?   CLEAR THE STALLS!
        //USBCSOL |= USBCSOL_SEND_STALL;
        //blink(300,200);
        lastCode[1] = LCE_USB_EP5_OUT_WHILE_OUTBUF_WRITTEN;
        return -1;
    }

    USBINDEX = 5;

    // setup DMA
    len = USBCNTL;
    len += (u16)(USBCNTH<<8);

    // if new transaction, we want to reset OUTlen early so our overall length calculation is clean
    if (ep5.OUTbytesleft == 0)
    {
        ep5.OUTlen = 0;
        ep5.OUTapp = USBF5;
        ep5.OUTcmd = USBF5;
        ep5.OUTbytesleft =  USBF5;
        ep5.OUTbytesleft += (USBF5 << 8);

        len -= 4;

        if (ep5.OUTbytesleft > EP5OUT_BUFFER_SIZE)
            ep5.OUTbytesleft = EP5OUT_BUFFER_SIZE;

    } else
    {
        //debug("Continued...");
        //debughex16(ep5.OUTbytesleft);
        //debughex16((u16)ep5.dptr);
        //ep5.flags |= EP_OUTBUF_CONTINUED;
    }

    while ((DMAIRQ & usbdmaarm))
        blink(20,20);

    // points our destination at the next free point in our buffer
    ptr = &ep5.OUTbuf[0] + ep5.OUTlen;

    // config and arm DMA 
    DMAARM |= 0x80 + usbdmaarm;
    usbdma->srcAddrH = 0xde;     //USBF5 == 0xde2a
    usbdma->srcAddrL = 0x2a;
    usbdma->destAddrH = ((u16)ptr)>>8;
    usbdma->destAddrL = ((u16)ptr)&0xff;
    usbdma->srcInc = 0;
    usbdma->destInc = 1;
    usbdma->lenL = USBCNTL;
    usbdma->lenH = USBCNTH;  // should always be zero, but what if we move to a HS chip someday?

    // doublecheck that overall length is not going to go over our buffer size (no buffer overflows please!)
    if (len + ep5.OUTlen > EP5OUT_BUFFER_SIZE)
        len = EP5OUT_BUFFER_SIZE - ep5.OUTlen;

    // make sure the controller isn't trying to slip in extra bytes (still don't know what to do with this yet, i think it needs to be a client fix)
    if (len > EP5OUT_MAX_PACKET_SIZE)                           // FIXME: if they wanna send too much data, do we accept what we can?  or bomb?
    {                                                           //  currently choosing to bomb.
        lastCode[1] = LCE_USB_EP5_LEN_TOO_BIG;
        //USBCSOL |= USBCSOL_SEND_STALL;
        USBCSOL &= ~USBCSOL_OUTPKT_RDY;
        blink_binary_baby_lsb(5, 4);
        blink_binary_baby_lsb(len, 16);
        return -2;
    }

    //  DMA Trigger
    DMAARM |= usbdmaarm;
    DMAREQ |= usbdmaarm;

    // update OUTlen.  this is vital for determining when we're done
    ep5.OUTlen += len;

    while (!(DMAIRQ & usbdmaarm));
    DMAIRQ &= ~usbdmaarm;


    if (ep5.OUTlen >= ep5.OUTbytesleft)
    {
        ep5.flags |= EP_OUTBUF_WRITTEN;                         // track that we've read into the OUTbuf
        ep5.OUTbytesleft = 0;
        USBINDEX = 5;
        usb_data.event &= ~USBD_OIF_OUTEP5IF;       // this indicates that we have more processing to do.  clear so we can reset in the interrupt handler...
        USBCSOL &= ~USBCSOL_OUTPKT_RDY;             // indicates to the USB controller that we're ready for another packet in the EP5 buffer
        return 1;                                               // this return value is what gets processOUTEP5 to kick
    }

    USBINDEX = 5;
    usb_data.event &= ~USBD_OIF_OUTEP5IF;       // this indicates that we have more processing to do.  clear so we can reset in the interrupt handler...
    USBCSOL &= ~USBCSOL_OUTPKT_RDY;             // indicates to the USB controller that we're ready for another packet in the EP5 buffer
    return 0;
}

void processOUTEP5(void)
{
    u16 loop;
    __xdata u8* __xdata  ptr; 

    // if the buffer is still being loaded or just plain empty, ignore this  (superfluous... may remove this check later)
    if ((ep5.flags & EP_OUTBUF_WRITTEN) == 0)
        return;

    ptr = &ep5.OUTbuf[0];
    // system application
    if (ep5.OUTapp == 0xff)                                        
    {

        switch (ep5.OUTcmd)
        {
            case CMD_PEEK:
                ep5.OUTbytesleft =  *ptr++;
                ep5.OUTbytesleft += *ptr++ << 8;

                loop =  (u16)*ptr++;
                loop += (u16)*ptr++ << 8;
                ptr = (__xdata u8*) loop;

                txdata(ep5.OUTapp, ep5.OUTcmd, ep5.OUTbytesleft, ptr);
                ep5.OUTbytesleft = 0;
                break;

            case CMD_POKE:
                loop =  *ptr++;
                loop += *ptr++ << 8;
                ep5.dptr = (__xdata u8*) loop;

                loop = ep5.OUTlen - 2;

                for (;loop>0;loop--)
                {
                    *ep5.dptr++ = *ptr++;
                }

                //if (ep5.OUTbytesleft == 0)
                txdata(ep5.OUTapp, ep5.OUTcmd, 2, (__xdata u8*)&(ep5.OUTbytesleft));
                break;

            case CMD_POKE_REG:
                if (!(ep5.flags & EP_OUTBUF_CONTINUED))
                {
                    loop =  *ptr++;
                    loop += *ptr++ << 8;
                    ep5.dptr = (__xdata u8*) loop;
                }
                // FIXME: do we want to DMA here?
                
                loop = ep5.OUTbytesleft;
                if (loop > EP5OUT_MAX_PACKET_SIZE)
                {
                    loop = EP5OUT_MAX_PACKET_SIZE;
                }

                ep5.OUTbytesleft -= loop;
                //debughex16(loop);

                for (;loop>0;loop--)
                {
                    *ep5.dptr++ = *ptr++;
                }

                txdata(ep5.OUTapp, ep5.OUTcmd, 2, (__xdata u8*)&(ep5.OUTbytesleft));

                break;
            case CMD_PING:
                blink(2,2);
                txdata(ep5.OUTapp,ep5.OUTcmd,ep5.OUTlen,ptr);
                break;

            case CMD_STATUS:
                txdata(ep5.OUTapp, ep5.OUTcmd, 13, (__xdata u8*)"UNIMPLEMENTED");
                // unimplemented
                break;

            case CMD_GET_CLOCK:
                txdata(ep5.OUTapp, ep5.OUTcmd, 4, (__xdata u8*)clock);
                break;

            case CMD_BUILDTYPE:
                txdata(ep5.OUTapp, ep5.OUTcmd, sizeof(buildname), (__xdata u8*)&buildname[0]);
                break;

            case CMD_BOOTLOADER:
                // acknowledge first since we won't be coming back!
                txdata(ep5.OUTapp,ep5.OUTcmd,ep5.OUTlen,ptr);
                sleepMillis(200);
                run_bootloader();
                break;

            case CMD_COMPILER:
                txdata(ep5.OUTapp, ep5.OUTcmd, sizeof(sdccver), (__xdata u8*)&sdccver[0]);
                break;
                
            case CMD_RFMODE:
                switch (*ptr++)
                {
                    case RFST_SRX:
                        RxMode();
                        break;
                    case RFST_SIDLE:
                        LED = 0;
                        IdleMode();
                        break;
                    case RFST_STX:
                        TxMode();
                        break;
                }
                //appReturn(ep5.OUTlen,buf);
                txdata(ep5.OUTapp,ep5.OUTcmd,ep5.OUTlen,ptr);
                break;

            case CMD_PARTNUM:
                ep5.OUTbytesleft = 1;

                ptr = (__xdata u8*) &PARTNUM;

                txdata(ep5.OUTapp, ep5.OUTcmd, ep5.OUTbytesleft, ptr);
                ep5.OUTbytesleft = 0;
                break;

            case CMD_RESET:
                if (strncmp(ptr, "RESET_NOW", 9))
                    break;   //didn't match the signature.  must have been an accident.

                // implement a RESET by trigging the watchdog timer
                WDCTL = 0x80;   // Watchdog ENABLE, Watchdog mode, 1s until reset

                txdata(ep5.OUTapp,ep5.OUTcmd,ep5.OUTlen,ptr);
                break;

            case CMD_CLEAR_CODES:
                lastCode[0] = 0;
                lastCode[1] = 0;
                //txdata(ep5.OUTapp,ep5.OUTcmd,ep5.OUTlen,ptr);   // FIXME: need to reorient all these to return LCE_NO_ERROR unless error.
                appReturn(2, ptr);
                break;

            default:
                txdata(ep5.OUTapp,ep5.OUTcmd,ep5.OUTlen,ptr);
        }

        ep5.flags &= ~EP_OUTBUF_WRITTEN; 
    }
    else
    {
        if (cb_ep5)
        {
            if (! cb_ep5())
            {
                // if the callback returns 0, we're done.  
                // if non-zero, we can't handle it right now, keep it around
                ep5.flags &= ~EP_OUTBUF_WRITTEN; 
            }
        }
        else
        {
            ep5.flags &= ~EP_OUTBUF_WRITTEN; 
        }
    }

}

#define handleINEP5()  ep5.flags &= ~EP_INBUF_WRITTEN 

void appReturn(__xdata u8 len, __xdata u8* __xdata  response)
    // use this to easily 
{
    ep5.flags &= ~EP_OUTBUF_WRITTEN;                       // this should be superfluous... but could be causing problems?
    txdata(ep5.OUTapp,ep5.OUTcmd, len, response);
}

void usbProcessEvents(void)
{
    // usb_data.event accumulates the event flags.  *as they are handled, make sure you clear them!*

    // handle Suspend signals
    if (usb_data.event & USBD_CIF_SUSPEND) {
        usb_data.usbstatus = USB_STATE_SUSPEND;
        usb_data.event    &= ~USBD_CIF_SUSPEND;
        PM1();                                               // sir, if you'll not be needing me i'll close down for a while.  sure go ahead.
    }


    // FIXME: this needs to be gone through and sorted out.
    if (usb_data.event & (USBD_CIF_RESET | USBD_CIF_RESUME)) {
        lastCode[0] = LC_USB_DATA_RESET_RESUME;
        usb_data.usbstatus = USB_STATE_RESUME;
        usb_data.event    &= ~(USBD_CIF_RESUME);
        USBPOW |= USBPOW_RESUME;
        sleepMillis(8);
        USBPOW &= ~USBPOW_RESUME;

        usb_data.usbstatus = USB_STATE_IDLE;
    }

    USBINDEX = 0;
    if (USBCS0 & (USBCS0_SENT_STALL))
    {
        USBCS0 &= ~(USBCS0_SEND_STALL | USBCS0_SENT_STALL);
        ep0.INbytesleft = 0;
        ep0.OUTlen = 0;
        ep0.epstatus = EP_STATE_IDLE;
    }
    USBINDEX = 5;
    if (USBCSIL & (USBCSIL_SENT_STALL))
    {
        USBCSIL &= ~(USBCSIL_SEND_STALL | USBCSIL_SENT_STALL);
        lastCode[1] = LCE_USB_EP5_STALL;
        ep5.INbytesleft = 0;
        ep5.OUTlen = 0;
        ep5.epstatus = EP_STATE_IDLE;          // not sure about this.  perhaps check to see if state us RX or TX?
    }
    if (USBCSOL & (USBCSOL_SENT_STALL))
    {
        USBCSOL &= ~(USBCSOL_SEND_STALL | USBCSOL_SENT_STALL);
        lastCode[1] = LCE_USB_EP5_STALL;
        ep5.INbytesleft = 0;
        ep5.OUTlen = 0;
        ep5.epstatus = EP_STATE_IDLE;          // not sure about this.  perhaps check to see if state us RX or TX?
    }


    // usb_data.event accumulates the event flags.  *as they are handled, make sure you clear them!*

    if (usb_data.event & USBD_CIF_RESET || usb_data.usbstatus == USB_STATE_RESET)                // handle RESET
    { 
        //      catching either the CIF_RESET or the USB_STATE_RESET... should normalize.. probably catching the same stuff.
        usb_init();
        lastCode[0] = LC_USB_RESET;
        usb_data.event &= ~USBD_CIF_RESET;
    } 

    if (usb_data.event & (USBD_IIF_EP0IF))
    {
        // read the packet and interpret/handle
        handleCS0();
        usb_data.event &= 0xfe7;
    } 
    
    if (usb_data.event & (USBD_OIF_OUTEP5IF))
    {
        __xdata u16 retval;
        lastCode[0] = LC_USB_EP5OUT;
        switch (handleOUTEP5())                    // handles the immediate read into ep5
        {
            case -1:                                    // we failed to send.  still waiting on our OUT_BUF.  still a message waiting in queue.
                //txdata(ep5.OUTapp,ep5.OUTcmd, 0, ptr);      // WTF do we do here?  what if it never gets processed??  did we miss a race condition for status???  *processOUTEP5* should be processing something, but we're here... so it's not processed it.  what gives?
                    // * Race condition on ep5.flags
                    // * Not resetting ep5.flags correctly
                    // * Interrupt Collisions
                    // * ???
                //break;
                //  no need to break since we still want to run processOUTEP5 on the current buffer.
            case 1:
//                processOUTEP5();                            // process the data read into ep5
                break;

            case -2:
                retval = LCE_USB_EP5_LEN_TOO_BIG;
                txdata(ep5.OUTapp,ep5.OUTcmd, 2, (u8*)&retval);
                txdata(ep5.OUTapp,1, 2, (u8*)&retval);

                break;

            default:
        }
        processOUTEP5();                            // process the data read into ep5
    }

    // we don't currently queue IN data, we just send it.  probably should move to a queuing system but it takes valuable RAM.
    //if (usb_data.event & (USBD_IIF_INEP5IF))
    //{ 
    //    handleINEP5();
    //    usb_data.event &= ~USBD_IIF_INEP5IF;
    //}

    // debugging if any interesting events are still left over at this point...
    if (usb_data.event & ~(USBD_IIF_INEP5IF|USBD_OIF_OUTEP5IF|USBD_IIF_EP0IF|USBD_CIF_RESET|
                USBD_CIF_RESUME|USBD_CIF_SUSPEND|USBD_CIF_SOFIF))
    {
        lastCode[1] = LCE_USB_DATA_LEFTOVER_FLAGS;
        blink_binary_baby_lsb(0x44, 8);
        blink_binary_baby_lsb(usb_data.event, 16);
        usb_data.event &= ~(USBD_IIF_INEP5IF|USBD_OIF_OUTEP5IF|USBD_IIF_EP0IF|USBD_CIF_RESET|
                USBD_CIF_RESUME|USBD_CIF_SUSPEND|USBD_CIF_SOFIF);
    }

    //debug("usbprocessevents");

}


/*************************************************************************************************
 * Interrupt Service Routines                                                                    *
 ************************************************************************************************/
void usbIntHandler(void) __interrupt P2INT_VECTOR
{

    while (!IS_XOSC_STABLE());

    // Set event flags for interpretation by main loop.  Since these registers are cleared upon read, we OR with the existing flags
    usb_data.event |= USBCIF;
    usb_data.event |= (USBIIF << 4);
    usb_data.event |= (USBOIF << 9);
 
    // process events that are fast and not part of the main loop
    /*  this is currently handled in the main loop.  worst thing would be for us to interrupt EP5 handlers  */
    /*if (usb_data.event & (USBD_IIF_EP0IF))
    {
        // read the packet and interpret/handle
        handleCS0();
        usb_data.event &= 0xfe7;
    } */
    
    if (usb_data.event & (USBD_IIF_INEP5IF))
    {
        ep5.flags &= ~EP_INBUF_WRITTEN;        // host received our message, ok to write more
        usb_data.event &= ~USBD_IIF_INEP5IF;
    }
 
    // Clear the P2 interrupt flag
    USB_INT_CLEAR();                                // P2IFG= 0; P2IF= 0;

}

void p0IntHandler(void) __interrupt P0INT_VECTOR  // P0_7's interrupt is used as the USB RESUME interrupt
{
    while (!IS_XOSC_STABLE());
    EA=0;

    if (P0IFG & P0IFG_USB_RESUME)
        usb_data.usbstatus = USB_STATE_RESUME;

    SLEEP &= ~0x3;                                  // clear the PM mode bits
    USB_RESUME_INT_CLEAR();
    
    EA=1;
}

/* blinks the EP0 SETUP packet in binary on the LED */
void debugEP0Req(u8 * __xdata pReq)
{
#ifndef DEBUG
    (void) pReq;
#else
    u8  loop;

    blink_binary_baby_lsb(0x40, 8);
    for (loop = sizeof(USB_Setup_Header);loop>0; loop--)
    {
        blink_binary_baby_lsb(*(pReq), 8);
        pReq++;
    }
#endif

}




/*************************************************************************************************
 * setup Config Descriptor  (see cc1111.h for defaults and fields to change)                     *
 ************************************************************************************************/

// all numbers are lsb.  modify this for your own use.

__code u8 USBDESCBEGIN [] = 
#ifndef VCOMTEST
{
// Device descriptor
               18,                      // bLength 
               USB_DESC_DEVICE,         // bDescriptorType
               LE_WORD(0x0110),              // bcdUSB
               0x00,                    // bDeviceClass - defined at interface
               0x00,                    // bDeviceSubClass
               0x00,                    // bDeviceProtocol
               EP0_MAX_PACKET_SIZE,     //   EP0_PACKET_SIZE
               LE_WORD(ID_VENDOR),      // idVendor
               LE_WORD(ID_PRODUCT),      // idProduct
               LE_WORD(0x0100),         // bcdDevice             (change to hardware version)
               0x01,                    // iManufacturer
               0x02,                    // iProduct
               USB_SERIAL_STRIDX_BYTE,  // iSerialNumber
               0x01,                    // bNumConfigurations

// Device Qualifier
               10,                      // bLength 
               USB_DESC_DEVICE_QUALIFIER,  // bDescriptorType
               LE_WORD(0x0110),              // bcdUSB
               0x00,                    // bDeviceClass - defined at interface
               0x00,                    // bDeviceSubClass
               0x00,                    // bDeviceProtocol
               EP0_MAX_PACKET_SIZE,     //   EP0_PACKET_SIZE
               0x01,                    // bNumConfigurations
               0x00,                    // reserved

// Configuration descriptor
               9,                       // bLength
               USB_DESC_CONFIG,         // bDescriptorType
               LE_WORD(32),             //   overall configuration length, including Config, Interface, Endpoints
               0x01,                    // NumInterfaces
               0x01,                    // bConfigurationValue  - should be nonzero
               0x00,                    // iConfiguration
               0x80,                    // bmAttributes
               0xfa,                    // MaxPower

// Interface descriptor
               9,                       // bLength
               USB_DESC_INTERFACE,      // bDescriptorType
               0x00,                    // bInterfaceNumber
               0x00,                    // bAlternateSetting
               0x02,                    // bNumEndpoints
               0x00,                    // bInterfaceClass
               0x00,                    // bInterfaceSubClass
               0x01,                    // bInterfaceProcotol
               0x00,                    // iInterface

// Endpoint descriptor (EP5 IN)
               7,                       // bLength
               USB_DESC_ENDPOINT,       // bDescriptorType
               0x85,                    // bEndpointAddress
               0x02,                    // bmAttributes - bits 0-1 Xfer Type (0=Ctrl, 1=Isoc, 2=Bulk, 3=Intrpt);      2-3 Isoc-SyncType (0=None, 1=FeedbackEndpoint, 2=Adaptive, 3=Synchronous);       4-5 Isoc-UsageType (0=Data, 1=Feedback, 2=Explicit)
               LE_WORD(EP5IN_MAX_PACKET_SIZE),// wMaxPacketSize
               0x01,                    // bInterval
// Endpoint descriptor (EP5 OUT)
               7,                       // bLength
               USB_DESC_ENDPOINT,       // bDescriptorType
               0x05,                    // bEndpointAddress
               0x02,                    // bmAttributes
               LE_WORD(EP5OUT_MAX_PACKET_SIZE),// wMaxPacketSize
               0x01,                    // bInterval
// Language ID
               4,                       // bLength
               USB_DESC_STRING,         // bDescriptorType
               0x09,                    // US-EN
               0x04,
// Manufacturer
               MANU_LEN,                // bLength
               USB_DESC_STRING,         // bDescriptorType
               MANUFACTURER,
// Product
               PROD_LEN,                // bLength
               USB_DESC_STRING,         // bDescriptorType
               PRODUCT_NAME,
// Serial number
               10,                      // bLength
               USB_DESC_STRING,         // bDescriptorType
               USB_DEVICE_SERIAL_NUMBER
          
// END OF STRINGS (len 0, type ff)
               0, 0xff
};
#else
{
  // Device descriptor
  0x12,
  USB_DESC_DEVICE,
  LE_WORD(0x0110),  // bcdUSB
  0x02,             // bDeviceClass
  0x00,             // bDeviceSubClass
  0x00,             // bDeviceProtocol
  USB_CONTROL_SIZE, // bMaxPacketSize
  LE_WORD(USB_VID), // idVendor
  LE_WORD(USB_PID), // idProduct
  LE_WORD(0x010),   // bcdDevice
  0x01,             // iManufacturer
  0x02,             // iProduct
  0x03,             // iSerialNumber
  0x01,             // bNumConfigurations

  // Configuration descriptor
  0x09,
  USB_DESC_CONFIG,
  LE_WORD(67),  // wTotalLength
  0x02,         // bNumInterfaces
  0x01,         // bConfigurationValue
  0x00,         // iConfiguration
  0xC0,         // bmAttributes
  0x32,         // bMaxPower

  // Control class interface
  0x09,
  USB_DESC_INTERFACE,
  0x00,  // bInterfaceNumber
  0x00,  // bAlternateSetting
  0x01,  // bNumEndPoints
  0x02,  // bInterfaceClass
  0x02,  // bInterfaceSubClass
  0x01,  // bInterfaceProtocol, linux requires value of 1 for the cdc_acm module
  0x00,  // iInterface

  // Header functional descriptor
  0x05,
  CS_INTERFACE,
  0x00,             // bDescriptor SubType Header
  LE_WORD(0x0110),  // CDC version 1.1

  // Call management functional descriptor
  0x05,
  CS_INTERFACE,
  0x01,  // bDescriptor SubType Call Management
  0x01,  // bmCapabilities = device handles call management
  0x01,  // bDataInterface call management interface number

  // ACM functional descriptor
  0x04,
  CS_INTERFACE,
  0x02,  // bDescriptor SubType Abstract Control Management
  0x02,  // bmCapabilities = D1 (Set_line_Coding, Set_Control_Line_State, Get_Line_Coding and Serial_State)

  // Union functional descriptor
  0x05,
  CS_INTERFACE,
  0x06,  // bDescriptor SubType Union Functional descriptor
  0x00,  // bMasterInterface
  0x01,  // bSlaveInterface0

  // Notification EP
  0x07,
  USB_DESC_ENDPOINT,
  USB_INT_EP|0x80,  // bEndpointAddress
  0x03,             // bmAttributes = intr
  LE_WORD(8),       // wMaxPacketSize
  0x0A,             // bInterval

  // Data class interface descriptor
  0x09,
  USB_DESC_INTERFACE,
  0x01, // bInterfaceNumber
  0x00, // bAlternateSetting
  0x02, // bNumEndPoints
  0x0A, // bInterfaceClass = data
  0x00, // bInterfaceSubClass
  0x00, // bInterfaceProtocol
  0x00, // iInterface

  // Data EP OUT
  0x07,
  USB_DESC_ENDPOINT,
  USB_OUT_EP,             // bEndpointAddress
  0x02,                   // bmAttributes = bulk
  LE_WORD(USB_OUT_SIZE),  // wMaxPacketSize
  0x00,                   // bInterval

  // Data EP in
  0x07,
  USB_DESC_ENDPOINT,
  USB_IN_EP|0x80,       // bEndpointAddress
  0x02,                 // bmAttributes = bulk
  LE_WORD(USB_IN_SIZE), // wMaxPacketSize
  0x00,                 // bInterval

  // String descriptors
  0x04,
  USB_DESC_STRING,
  LE_WORD(0x0409),

  // iManufacturer
  USB_iManufacturer_LEN,
  USB_DESC_STRING,
  USB_iManufacturer_UCS2,

  // iProduct
  USB_iProduct_LEN,
  USB_DESC_STRING,
  USB_iProduct_UCS2,

  // iSerial
  USB_iSerial_LEN,
  USB_DESC_STRING,
  USB_iSerial_UCS2,

  // Terminating zero
  0
};
#endif
