#ifndef CC1111USB
#define CC1111USB

#include "cc1111.h"
#include "global.h"

#define     EP0_MAX_PACKET_SIZE     32
#define     EP5OUT_MAX_PACKET_SIZE  256
#define     EP5IN_MAX_PACKET_SIZE   256
        // note: descriptor needs to be adjusted to match EP5_MAX_PACKET_SIZE

#define  EP_STATE_IDLE      0
#define  EP_STATE_TX        1
#define  EP_STATE_RX        2
#define  EP_STATE_STALL     3

#define USB_STATE_UNCONFIGURED 0
#define USB_STATE_IDLE      1
#define USB_STATE_SUSPEND   2
#define USB_STATE_RESUME    3
#define USB_STATE_RESET     4
#define USB_STATE_WAIT_ADDR 5
#define USB_STATE_BLINK     0xff

typedef struct {
    u8   usbstatus;
    u16  event;
    u8   config;
} USB_STATE;

typedef struct {
    u8*  INbuf;
    u16  INbytesleft;
    u8*  OUTbuf;
    u16  OUTlen;
    u16  BUFmaxlen;
    volatile u8   flags;
    u8   epstatus;
    //xdata u8*  reg;
    //void*   OUTDONE_handle;                                     // this is a function pointer which is called when the OUT transfer is done.  i may destroy this.
} USB_EP_IO_BUF;

typedef struct USB_Device_Desc_Type {
    uint8  bLength;             
    uint8  bDescriptorType;     
    uint16 bcdUSB;                             // cc1111 supports USB v2.0
    uint8  bDeviceClass;                       // 0 (each interface defines), 0xff (vendor-specified class code), or a valid class code
    uint8  bDeviceSubClass;                    // assigned by USB org
    uint8  bDeviceProtocol;                    // assigned by USB org;
    uint8  MaxPacketSize;                      // for EP0, 8,16,32,64;
    uint16 idVendor;                           // assigned by USB org
    uint16 idProduct;                          // assigned by vendor
    uint16 bcdDevice;                          // device release number
    uint8  iManufacturer;                      // index of the mfg string descriptor
    uint8  iProduct;                           // index of the product string descriptor
    uint8  iSerialNumber;                      // index of the serial number string descriptor
    uint8  bNumConfigurations;                 // number of possible configs...  i wonder if the host obeys this?
} USB_Device_Desc;


typedef struct USB_Config_Desc_Type {
    uint8  bLength;             
    uint8  bDescriptorType;     
    uint16 wTotalLength;
    uint8  bNumInterfaces;      
    uint8  bConfigurationValue; 
    uint8  iConfiguration;                     // index of String Descriptor describing this configuration
    uint8  bmAttributes;        
    uint8  bMaxPower;                          // 2mA increments, 0xfa; 
} USB_Config_Desc;


typedef struct USB_Interface_Desc_Type {
    uint8  bLength;             
    uint8  bDescriptorType;     
    uint8  bInterfaceNumber;
    uint8  bAlternateSetting;
    uint8  bNumEndpoints;       
    uint8  bInterfaceClass;     
    uint8  bInterfaceSubClass;  
    uint8  bInterfaceProtocol;  
    uint8  iInterface;          
} USB_Interface_Desc;


typedef struct USB_Endpoint_Desc_Type {
    uint8  bLength;             
    uint8  bDescriptorType;     
    uint8  bEndpointAddress;
    uint8  bmAttributes;                       // 0-1 Xfer Type (0;        Isoc, 2;
    uint16 wMaxPacketSize;
    uint8  bInterval;                          // Update interval in Frames (for isochronous, ignored for Bulk and Control)
} USB_Endpoint_Desc;


typedef struct USB_LANGID_Desc_Type {
    uint8  bLength;
    uint8  bDescriptorType;     
    uint16 wLANGID0;                           // wLANGID[0]  0x0409; 
    uint16 wLANGID1;                           // wLANGID[1]  0x0c09; 
    uint16 wLANGID2;                           // wLANGID[1]  0x0407; 
} USB_LANGID_Desc;


typedef struct USB_String_Desc_Type {
    uint8   bLength;
    uint8   bDescriptorType;     
    uint16* bString;
} USB_String_Desc;


typedef struct USB_Request_Type {
    uint8  bmRequestType;
    uint8  bRequest;
    uint16 wValue;
    uint16 wIndex;
    uint16 wLength;
} USB_Setup_Header;


// extern global variables
extern __code u8 USBDESCBEGIN[];
extern USB_STATE usb_data;
extern xdata u8  usb_ep0_OUTbuf[EP0_MAX_PACKET_SIZE];                  // these get pointed to by the above structure
extern xdata u8  usb_ep5_OUTbuf[EP5OUT_MAX_PACKET_SIZE];               // these get pointed to by the above structure
extern xdata USB_EP_IO_BUF     ep0iobuf;
extern xdata USB_EP_IO_BUF     ep5iobuf;
extern xdata u8 appstatus;

extern xdata u8   ep0req;
extern xdata u16  ep0len;
extern xdata u16  ep0value;

// provided by cc1111usb.c
void usbIntHandler(void) interrupt P2INT_VECTOR;
void p0IntHandler(void) interrupt P0INT_VECTOR;
void clock_init(void);
void txdataold(u8 app, u8 cmd, u16 len, u8* dataptr);
void txdata(u8 app, u8 cmd, u16 len, xdata u8* dataptr);
int setup_send_ep0(u8* payload, u16 length);
int setup_sendx_ep0(xdata u8* payload, u16 length);
u16 usb_recv_ep0OUT();

u16 usb_recv_epOUT(u8 epnum, USB_EP_IO_BUF* epiobuf);
void initUSB(void);
void usb_up(void);
void usb_down(void);
void waitForUSBsetup();
// export as this *must* be in main loop.
void usbProcessEvents(void);

void registerCb_ep0OutDone(void (*callback)(void));
void registerCb_ep0Out(void (*callback)(void));
void registerCb_ep0Vendor(void (*callback)(USB_Setup_Header* pReq));
void registerCb_ep5(void (*callback)(void));



#define EP_INBUF_WRITTEN        1
#define EP_OUTBUF_WRITTEN       2


// usb_data bits
#define USBD_CIF_SUSPEND        (u16)0x1
#define USBD_CIF_RESUME         (u16)0x2
#define USBD_CIF_RESET          (u16)0x4
#define USBD_CIF_SOFIF          (u16)0x8
#define USBD_IIF_EP0IF          (u16)0x10
#define USBD_IIF_INEP1IF        (u16)0x20
#define USBD_IIF_INEP2IF        (u16)0x40
#define USBD_IIF_INEP3IF        (u16)0x80
#define USBD_IIF_INEP4IF        (u16)0x100
#define USBD_IIF_INEP5IF        (u16)0x200
#define USBD_OIF_OUTEP1IF       (u16)0x400
#define USBD_OIF_OUTEP2IF       (u16)0x800
#define USBD_OIF_OUTEP3IF       (u16)0x1000
#define USBD_OIF_OUTEP4IF       (u16)0x2000
#define USBD_OIF_OUTEP5IF       (u16)0x4000

#define TXDATA_MAX_WAIT         30



#define     CMD_PEEK        0x80
#define     CMD_POKE        0x81
#define     CMD_PING        0x82
#define     CMD_STATUS      0x83
#define     CMD_POKE_REG    0x84
#define     CMD_GET_CLOCK   0x85
#define     CMD_BUILDTYPE   0x86
#define     CMD_RESET       0x8f

#define     EP0_CMD_GET_DEBUG_CODES         0x00
#define     EP0_CMD_GET_ADDRESS             0x01
#define     EP0_CMD_POKEX                   0x01
#define     EP0_CMD_PEEKX                   0x02
#define     EP0_CMD_PING0                   0x03
#define     EP0_CMD_PING1                   0x04
#define     EP0_CMD_RESET                   0xfe
#define     EP0_CMD_GET_FREQ                0xff

#define     DEBUG_CMD_STRING    0xf0
#define     DEBUG_CMD_HEX       0xf1
#define     DEBUG_CMD_HEX16     0xf2
#define     DEBUG_CMD_HEX32     0xf3
#define     DEBUG_CMD_INT       0xf4

#endif
