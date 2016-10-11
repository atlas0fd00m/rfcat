#ifndef CHIPCON_USB_H
#define CHIPCON_USB_H

#include "global.h"
#include "chipcon_usbdebug.h"

#define     EP0_MAX_PACKET_SIZE     64
#define     EP5_MAX_PACKET_SIZE     64
#define     EP5OUT_MAX_PACKET_SIZE  64
#define     EP5IN_MAX_PACKET_SIZE   64
// EP5OUT_BUFFER_SIZE must match rflib/cc1111client.py definition
#define     EP5OUT_BUFFER_SIZE      516 // data buffer size + 4

#define     EP_STATE_IDLE      0
#define     EP_STATE_TX        1
#define     EP_STATE_RX        2
#define     EP_STATE_STALL     3

#define     EP_INBUF_WRITTEN        1
#define     EP_OUTBUF_WRITTEN       2
#define     EP_OUTBUF_CONTINUED     4

#define USB_STATE_UNCONFIGURED 0
#define USB_STATE_IDLE      1
#define USB_STATE_SUSPEND   2
#define USB_STATE_RESUME    3
#define USB_STATE_RESET     4
#define USB_STATE_WAIT_ADDR 5
#define USB_STATE_BLINK     0xff

#define USBADDR_UPDATE          0x80    //r

#define USB_SERIAL_STRIDX_BYTE  0x03

// Power/Control Register
#define USBPOW_SUSPEND_EN       0x01    //rw
#define USBPOW_SUSPEND          0x02    //r
#define USBPOW_RESUME           0x04    //rw
#define USBPOW_RST              0x08    //r
#define USBPOW_ISO_WAIT_SOF     0x80    //rw

// IN Enpoints and EP0 Interrupt Flags
#define USBIIF_EP0IF            0x01    //r h0
#define USBIIF_INEP1IF          0x02    //r h0
#define USBIIF_INEP2IF          0x04    //r h0
#define USBIIF_INEP3IF          0x08    //r h0
#define USBIIF_INEP4IF          0x10    //r h0
#define USBIIF_INEP5IF          0x20    //r h0

// OUT Endpoints Interrupt Flags
#define USBOIF_OUTEP1IF         0x02    //r h0
#define USBOIF_OUTEP2IF         0x04    //r h0
#define USBOIF_OUTEP3IF         0x08    //r h0
#define USBOIF_OUTEP4IF         0x10    //r h0
#define USBOIF_OUTEP5IF         0x20    //r h0

// USBCIF is all Read/Only
// Common USB Interrupt Flags
#define USBCIF_SUSPENDIF        0x01    //r h0
#define USBCIF_RESUMEIF         0x02    //r h0
#define USBCIF_RSTIF            0x04    //r h0
#define USBCIF_SOFIF            0x08    //r h0

// IN Endpoints and EP0 Interrupt Enable Mask
#define USBIIE_EP0IE            0x01    //rw
#define USBIIE_INEP1IE          0x02    //rw
#define USBIIE_INEP2IE          0x04    //rw
#define USBIIE_INEP3IE          0x08    //rw
#define USBIIE_INEP4IE          0x10    //rw
#define USBIIE_INEP5IE          0x20    //rw

// OUT Endpoint Interrupt Enable Mask
#define USBOIE_EP1IE            0x02    //rw
#define USBOIE_EP2IE            0x04    //rw
#define USBOIE_EP3IE            0x08    //rw
#define USBOIE_EP4IE            0x10    //rw
#define USBOIE_EP5IE            0x20    //rw

// Common USB Interrupt Enable Mask
#define USBCIE_SUSPENDIE        0x01    //rw
#define USBCIE_RESUMEIE         0x02    //rw
#define USBCIE_RSTIE            0x04    //rw
#define USBCIE_SOFIE            0x08    //rw

// EP0 Control and Status
#define USBCS0_OUTPKT_RDY       0x01    //r
#define USBCS0_INPKT_RDY        0x02    //rw h0
#define USBCS0_SENT_STALL       0x04    //rw h1
#define USBCS0_DATA_END         0x08    //rw h0
#define USBCS0_SETUP_END        0x10    //r
#define USBCS0_SEND_STALL       0x20    //rw h0
#define USBCS0_CLR_OUTPKT_RDY   0x40    //rw h0
#define USBCS0_CLR_SETUP_END    0x80    //rw h0

// IN EP 1-5 Control and STatus (low)
#define USBCSIL_INPKT_RDY       0x01    //rw h0
#define USBCSIL_PKT_PRESENT     0x02    //r
#define USBCSIL_UNDERRUN        0x04    //rw
#define USBCSIL_FLUSH_PACKET    0x08    //rw h0
#define USBCSIL_SEND_STALL      0x10    //rw
#define USBCSIL_SENT_STALL      0x20    //rw
#define USBCSIL_CLR_DATA_TOG    0x40    //rw h0

// IN EP 1-5 Control and STatus (high)
#define USBCSIH_IN_DBL_BUF      0x01    //rw
#define USBCSIH_FORCE_DATA_TOG  0x08    //rw
#define USBCSIH_ISO             0x40    //rw
#define USBCSIH_AUTOSET         0x80    //rw

// OUT EP 1-5 Control and Status (low)
#define USBCSOL_OUTPKT_RDY      0x01    //rw
#define USBCSOL_FIFO_FULL       0x02    //r
#define USBCSOL_OVERRUN         0x04    //rw
#define USBCSOL_DATA_ERROR      0x08    //r
#define USBCSOL_FLUSH_PACKET    0x10    //rw
#define USBCSOL_SEND_STALL      0x20    //rw
#define USBCSOL_SENT_STALL      0x40    //rw
#define USBCSOL_CLR_DATA_TOG    0x80    //rw h0

// OUT EP 1-5 Control and Status (high)
#define USBCSOH_OUT_DBL_BUF     0x01    //rw
#define USBCSOH_ISO             0x40    //rw
#define USBCSOH_AUTOCLEAR       0x80    //rw

#define P0IFG_USB_RESUME        0x80    //rw0

   SBIT(USBIF,    0xE8, 0); // USB Interrupt Flag



// Request Types (bmRequestType)
#define USB_BM_REQTYPE_TGTMASK          0x1f
#define USB_BM_REQTYPE_TGT_DEV          0x00
#define USB_BM_REQTYPE_TGT_INTF         0x01
#define USB_BM_REQTYPE_TGT_EP           0x02
#define USB_BM_REQTYPE_TGT_OTHER        0x03
#define USB_BM_REQTYPE_TYPEMASK         0x60
#define USB_BM_REQTYPE_TYPE_STD         0x00
#define USB_BM_REQTYPE_TYPE_CLASS       0x20
#define USB_BM_REQTYPE_TYPE_VENDOR      0x40
#define USB_BM_REQTYPE_TYPE_RESERVED    0x60
#define USB_BM_REQTYPE_DIRMASK          0x80
#define USB_BM_REQTYPE_DIR_OUT          0x00
#define USB_BM_REQTYPE_DIR_IN           0x80
// Standard Requests (bRequest)
#define USB_GET_STATUS                  0x00
#define USB_CLEAR_FEATURE               0x01
#define USB_SET_FEATURE                 0x03
#define USB_SET_ADDRESS                 0x05
#define USB_GET_DESCRIPTOR              0x06
#define USB_SET_DESCRIPTOR              0x07
#define USB_GET_CONFIGURATION           0x08
#define USB_SET_CONFIGURATION           0x09
#define USB_GET_INTERFACE               0x0a
#define USB_SET_INTERFACE               0x11
#define USB_SYNCH_FRAME                 0x12

// Descriptor Types
#define USB_DESC_DEVICE                 0x01
#define USB_DESC_CONFIG                 0x02
#define USB_DESC_STRING                 0x03
#define USB_DESC_INTERFACE              0x04
#define USB_DESC_ENDPOINT               0x05
#define USB_DESC_DEVICE_QUALIFIER       0x06
#define USB_DESC_OTHER_SPEED_CFG        0x07

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

#define TXDATA_MAX_WAIT         10000



// USB activities
//
#define USB_DISABLE()               SLEEP &= ~SLEEP_USB_EN;
#define USB_ENABLE()                SLEEP |= SLEEP_USB_EN;
#define USB_RESET()                 USB_DISABLE(); NOP(); USB_ENABLE();
#define USB_INT_ENABLE()            IEN2|= 0x02;
#define USB_INT_DISABLE()           IEN2&= ~0x02;
#define USB_INT_CLEAR()             P2IFG= 0; P2IF= 0;

#define USB_PULLUP_ENABLE()         USB_ENABLE_PIN = 1;
#define USB_PULLUP_DISABLE()        USB_ENABLE_PIN = 0;

#define USB_RESUME_INT_ENABLE()     P0IE= 1
#define USB_RESUME_INT_DISABLE()    P0IE= 0
#define USB_RESUME_INT_CLEAR()      P0IFG= 0; P0IF= 0
#define PM1()                       SLEEP |= 1


#ifdef VCOMTEST
    //  from VCOM
    #define USB_VID 0xFFFE
    #define USB_PID 0x000A
    
    // iManufacturer
    #define USB_iManufacturer_LEN 0x10
    #define USB_iManufacturer_STRING "JobyGPS"
    #define USB_iManufacturer_UCS2 'J', 0, 'o', 0, 'b', 0, 'y', 0, 'G', 0, 'P', 0, 'S', 0
    // iProduct
    #define USB_iProduct_LEN 0x1C
    #define USB_iProduct_STRING "CC Bootloader"
    #define USB_iProduct_UCS2 'C', 0, 'C', 0, ' ', 0, 'B', 0, 'o', 0, 'o', 0, 't', 0, 'l', 0, 'o', 0, 'a', 0, 'd', 0, 'e', 0, 'r', 0
    // iSerial
    #define USB_iSerial_LEN 0x0e
    #define USB_iSerial_STRING "000001"
    #define USB_iSerial_UCS2 '0', 0, '0', 0, '0', 0, '0', 0, '0', 0, '1', 0
    
    #define USB_GET_DESC_TYPE(x)  (((x)>>8)&0xFF)
    #define USB_GET_DESC_INDEX(x) ((x)&0xFF)
    
    #define USB_CONTROL_EP    0
    #define USB_INT_EP        1
    #define USB_OUT_EP        5 //4
    #define USB_IN_EP         5
    #define USB_CONTROL_SIZE  32
    
    // Double buffer IN and OUT EPs, so each
    // gets half of the available space
    //
    // Ah, but USB bulk packets can only come in 8, 16, 32 and 64
    // byte sizes, so we'll use 64 for everything
    #define USB_IN_SIZE   64
    #define USB_OUT_SIZE  64
    
    #define USB_EP0_IDLE      0
    #define USB_EP0_DATA_IN   1
    #define USB_EP0_DATA_OUT  2
    // CDC definitions
    #define CS_INTERFACE  0x24
    #define CS_ENDPOINT   0x25
    
    #define SET_LINE_CODING         0x20
    #define GET_LINE_CODING         0x21
    #define SET_CONTROL_LINE_STATE  0x22
    // Data structure for GET_LINE_CODING / SET_LINE_CODING class requests
    struct usb_line_coding {
      unsigned long  rate;
      unsigned char   char_format;
      unsigned char   parity;
      unsigned char   data_bits;
    };

#endif

// formerly from cc1111usb.h
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
    u8   OUTapp;
    u8   OUTcmd;
    u16  OUTbytesleft;
    volatile u8   flags;
    u8   epstatus;
    __xdata u8* dptr;
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
extern __xdata u8  usb_ep0_OUTbuf[EP0_MAX_PACKET_SIZE];                  // these get pointed to by the above structure
extern __xdata u8  usb_ep5_OUTbuf[EP5OUT_BUFFER_SIZE];               // these get pointed to by the above structure
extern __xdata USB_EP_IO_BUF     ep0;
extern __xdata USB_EP_IO_BUF     ep5;
extern __xdata u8 appstatus;

extern __xdata u8   ep0req;
extern __xdata u16  ep0len;
extern __xdata u16  ep0value;

// provided by cc1111usb.c
void clock_init(void);
int txdata(u8 app, u8 cmd, u16 len, __xdata u8* dataptr);
int setup_send_ep0(u8* __xdata  payload, u16 length);
int setup_sendx_ep0(__xdata u8* __xdata  payload, u16 length);
u16 usb_recv_ep0OUT();

u16 usb_recv_epOUT(u8 epnum, USB_EP_IO_BUF* __xdata  epiobuf);
void initUSB(void);
void usb_up(void);
void usb_down(void);
void waitForUSBsetup();
// export as this *must* be in main loop.
void usbProcessEvents(void);

void registerCb_ep0OutDone(int (*callback)(void));
void registerCb_ep0Out(int (*callback)(void));
//void registerCb_ep0Vendor(int (*callback)(USB_Setup_Header* __xdata  pReq));
void registerCb_ep0Vendor(int (*callback)(USB_Setup_Header*  pReq));
void registerCb_ep5(int (*callback)(void));


void appReturn(__xdata u8 len, __xdata u8* __xdata  response);



#define     CMD_PEEK        0x80
#define     CMD_POKE        0x81
#define     CMD_PING        0x82
#define     CMD_STATUS      0x83
#define     CMD_POKE_REG    0x84
#define     CMD_GET_CLOCK   0x85
#define     CMD_BUILDTYPE   0x86
#define     CMD_BOOTLOADER  0x87
#define     CMD_RFMODE      0x88
#define     CMD_COMPILER    0x89
#define     CMD_PARTNUM     0x8e
#define     CMD_RESET       0x8f
#define     CMD_CLEAR_CODES 0x90

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

/******************************** TROUBLESHOOTING *****************************************
#define	EPERM		 1	* Operation not permitted /
#define	ENOENT		 2	* No such file or directory /
#define	ESRCH		 3	* No such process /
#define	EINTR		 4	* Interrupted system call /
#define	EIO		 5	* I/O error /
#define	ENXIO		 6	* No such device or address /
#define	E2BIG		 7	* Argument list too long /
#define	ENOEXEC		 8	* Exec format error /
#define	EBADF		 9	* Bad file number /
#define	ECHILD		10	* No child processes /
#define	EAGAIN		11	* Try again /
#define	ENOMEM		12	* Out of memory /
#define	EACCES		13	* Permission denied /
#define	EFAULT		14	* Bad address /
#define	ENOTBLK		15	* Block device required /
#define	EBUSY		16	* Device or resource busy /
#define	EEXIST		17	* File exists /
#define	EXDEV		18	* Cross-device link /
#define	ENODEV		19	* No such device /
#define	ENOTDIR		20	* Not a directory /
#define	EISDIR		21	* Is a directory /
#define	EINVAL		22	* Invalid argument /
#define	ENFILE		23	* File table overflow /
#define	EMFILE		24	* Too many open files /
#define	ENOTTY		25	* Not a typewriter /
#define	ETXTBSY		26	* Text file busy /
#define	EFBIG		27	* File too large /
#define	ENOSPC		28	* No space left on device /
#define	ESPIPE		29	* Illegal seek /
#define	EROFS		30	* Read-only file system /
#define	EMLINK		31	* Too many links /
#define	EPIPE		32	* Broken pipe /
#define	EDOM		33	* Math argument out of domain of func /
#define	ERANGE		34	* Math result not representable /
#define	EDEADLK		35	* Resource deadlock would occur /
#define	ENAMETOOLONG	36	* File name too long /
#define	ENOLCK		37	* No record locks available /
#define	ENOSYS		38	* Function not implemented /
#define	ENOTEMPTY	39	* Directory not empty /
#define	ELOOP		40	* Too many symbolic links encountered /
#define	EWOULDBLOCK	EAGAIN	* Operation would block /
#define	ENOMSG		42	* No message of desired type /
#define	EIDRM		43	* Identifier removed /
#define	ECHRNG		44	* Channel number out of range /
#define	EL2NSYNC	45	* Level 2 not synchronized /
#define	EL3HLT		46	* Level 3 halted /
#define	EL3RST		47	* Level 3 reset /
#define	ELNRNG		48	* Link number out of range /
#define	EUNATCH		49	* Protocol driver not attached /
#define	ENOCSI		50	* No CSI structure available /
#define	EL2HLT		51	* Level 2 halted /
#define	EBADE		52	* Invalid exchange /
#define	EBADR		53	* Invalid request descriptor /
#define	EXFULL		54	* Exchange full /
#define	ENOANO		55	* No anode /
#define	EBADRQC		56	* Invalid request code /
#define	EBADSLT		57	* Invalid slot /

#define	EDEADLOCK	EDEADLK

#define	EBFONT		59	* Bad font file format /
#define	ENOSTR		60	* Device not a stream /
#define	ENODATA		61	* No data available /
#define	ETIME		62	* Timer expired /
#define	ENOSR		63	* Out of streams resources /
#define	ENONET		64	* Machine is not on the network /
#define	ENOPKG		65	* Package not installed /
#define	EREMOTE		66	* Object is remote /
#define	ENOLINK		67	* Link has been severed /
#define	EADV		68	* Advertise error /
#define	ESRMNT		69	* Srmount error /
#define	ECOMM		70	* Communication error on send /
#define	EPROTO		71	* Protocol error /
#define	EMULTIHOP	72	* Multihop attempted /
#define	EDOTDOT		73	* RFS specific error /
#define	EBADMSG		74	* Not a data message /
#define	EOVERFLOW	75	* Value too large for defined data type /
#define	ENOTUNIQ	76	* Name not unique on network /
#define	EBADFD		77	* File descriptor in bad state /
#define	EREMCHG		78	* Remote address changed /
#define	ELIBACC		79	* Can not access a needed shared library /
#define	ELIBBAD		80	* Accessing a corrupted shared library /
#define	ELIBSCN		81	* .lib section in a.out corrupted /
#define	ELIBMAX		82	* Attempting to link in too many shared libraries /
#define	ELIBEXEC	83	* Cannot exec a shared library directly /
#define	EILSEQ		84	* Illegal byte sequence /
#define	ERESTART	85	* Interrupted system call should be restarted /
#define	ESTRPIPE	86	* Streams pipe error /
#define	EUSERS		87	* Too many users /
#define	ENOTSOCK	88	* Socket operation on non-socket /
#define	EDESTADDRREQ	89	* Destination address required /
#define	EMSGSIZE	90	* Message too long /
#define	EPROTOTYPE	91	* Protocol wrong type for socket /
#define	ENOPROTOOPT	92	* Protocol not available /
#define	EPROTONOSUPPORT	93	* Protocol not supported /
#define	ESOCKTNOSUPPORT	94	* Socket type not supported /
#define	EOPNOTSUPP	95	* Operation not supported on transport endpoint /
#define	EPFNOSUPPORT	96	* Protocol family not supported /
#define	EAFNOSUPPORT	97	* Address family not supported by protocol /
#define	EADDRINUSE	98	* Address already in use /
#define	EADDRNOTAVAIL	99	* Cannot assign requested address /
#define	ENETDOWN	100	* Network is down /
#define	ENETUNREACH	101	* Network is unreachable /
#define	ENETRESET	102	* Network dropped connection because of reset /
#define	ECONNABORTED	103	* Software caused connection abort /
#define	ECONNRESET	104	* Connection reset by peer /
#define	ENOBUFS		105	* No buffer space available /
#define	EISCONN		106	* Transport endpoint is already connected /
#define	ENOTCONN	107	* Transport endpoint is not connected /
#define	ESHUTDOWN	108	* Cannot send after transport endpoint shutdown /
#define	ETOOMANYREFS	109	* Too many references: cannot splice /
#define	ETIMEDOUT	110	* Connection timed out /
#define	ECONNREFUSED	111	* Connection refused /
#define	EHOSTDOWN	112	* Host is down /
#define	EHOSTUNREACH	113	* No route to host /
#define	EALREADY	114	* Operation already in progress /
#define	EINPROGRESS	115	* Operation now in progress /
#define	ESTALE		116	* Stale NFS file handle /
#define	EUCLEAN		117	* Structure needs cleaning /
#define	ENOTNAM		118	* Not a XENIX named type file /
#define	ENAVAIL		119	* No XENIX semaphores available /
#define	EISNAM		120	* Is a named type file /
#define	EREMOTEIO	121	* Remote I/O error /
#define	EDQUOT		122	* Quota exceeded /

#define	ENOMEDIUM	123	* No medium found /
#define	EMEDIUMTYPE	124	* Wrong medium type /
#define	ECANCELED	125	* Operation Canceled /
#define	ENOKEY		126	* Required key not available /
#define	EKEYEXPIRED	127	* Key has expired /
#define	EKEYREVOKED	128	* Key has been revoked /
#define	EKEYREJECTED	129	* Key was rejected by service /

* for robust mutexes /
#define	EOWNERDEAD	130	* Owner died /
#define	ENOTRECOVERABLE	131	* State not recoverable /

#define ERFKILL		132	* Operation not possible due to RF-kill /

 *
 * usb_get_device_descriptor - (re)reads the device descriptor (usbcore)
 * @dev: the device whose device descriptor is being updated
 * @size: how much of the descriptor to read
 * Context: !in_interrupt ()
 *
 * Updates the copy of the device descriptor stored in the device structure,
 * which dedicates space for this purpose.
 *
 * Not exported, only for use by the core.  If drivers really want to read
 * the device descriptor directly, they can call usb_get_descriptor() with
 * type = USB_DT_DEVICE and index = 0.
 *
 * This call is synchronous, and may not be used in an interrupt context.
 *
 * Returns the number of bytes received on success, or else the status code
 * returned by the underlying usb_control_msg() call.
      
int usb_get_device_descriptor(struct usb_device *dev, unsigned int size)
{
    struct usb_device_descriptor *desc;
    int ret;

    if (size > sizeof(*desc))
        return -EINVAL;
    desc = kmalloc(sizeof(*desc), GFP_NOIO);
    if (!desc)
        return -ENOMEM;

    ret = usb_get_descriptor(dev, USB_DT_DEVICE, 0, desc, size);
    if (ret >= 0)
        memcpy(&dev->descriptor, desc, size);
    kfree(desc);
    return ret;
}
 * usb_get_descriptor - issues a generic GET_DESCRIPTOR request
 * @dev: the device whose descriptor is being retrieved
 * @type: the descriptor type (USB_DT_*)
 * @index: the number of the descriptor
 * @buf: where to put the descriptor
 * @size: how big is "buf"?
 * Context: !in_interrupt ()
 *
 * Gets a USB descriptor.  Convenience functions exist to simplify
 * getting some types of descriptors.  Use
 * usb_get_string() or usb_string() for USB_DT_STRING.
 * Device (USB_DT_DEVICE) and configuration descriptors (USB_DT_CONFIG)
 * are part of the device structure.
 * In addition to a number of USB-standard descriptors, some
 * devices also use class-specific or vendor-specific descriptors.
 *
 * This call is synchronous, and may not be used in an interrupt context.
 *
 * Returns the number of bytes received on success, or else the status code
 * returned by the underlying usb_control_msg() call.
int usb_get_descriptor(struct usb_device *dev, unsigned char type,
                   unsigned char index, void *buf, int size)
{
    int i;
    int result;

    memset(buf, 0, size);   * Make sure we parse really received data *

    for (i = 0; i < 3; ++i) {
        * retry on length 0 or error; some devices are flakey *
        result = usb_control_msg(dev, usb_rcvctrlpipe(dev, 0),
                    USB_REQ_GET_DESCRIPTOR, USB_DIR_IN,
                    (type << 8) + index, 0, buf, size,
                    USB_CTRL_GET_TIMEOUT);
        if (result <= 0 && result != -ETIMEDOUT)
            continue;
        if (result > 1 && ((u8 *)buf)[1] != type) {
            result = -ENODATA;
            continue;
        }
        break;
        }
    return result;
}
EXPORT_SYMBOL_GPL(usb_get_descriptor);

**
 * usb_control_msg - Builds a control urb, sends it off and waits for completion
 * @dev: pointer to the usb device to send the message to
 * @pipe: endpoint "pipe" to send the message to
 * @request: USB message request value
 * @requesttype: USB message request type value
 * @value: USB message value
 * @index: USB message index value
 * @data: pointer to the data to send
 * @size: length in bytes of the data to send
 * @timeout: time in msecs to wait for the message to complete before timing
 *  out (if 0 the wait is forever)
 *
 * Context: !in_interrupt ()
 *
 * This function sends a simple control message to a specified endpoint and
 * waits for the message to complete, or timeout.
 *
 * If successful, it returns the number of bytes transferred, otherwise a
 * negative error number.
 *
 * Don't use this function from within an interrupt context, like a bottom half
 * handler.  If you need an asynchronous message, or need to send a message
 * from within interrupt context, use usb_submit_urb().
 * If a thread in your driver uses this call, make sure your disconnect()
 * method can wait for it to complete.  Since you don't have a handle on the
 * URB used, you can't cancel the request.
int usb_control_msg(struct usb_device *dev, unsigned int pipe, __u8 request,
            __u8 requesttype, __u16 value, __u16 index, void *data,
            __u16 size, int timeout)
{
    struct usb_ctrlrequest *dr;
    int ret;

    dr = kmalloc(sizeof(struct usb_ctrlrequest), GFP_NOIO);
    if (!dr)
            return -ENOMEM;

    dr->bRequestType = requesttype;
    dr->bRequest = request;
    dr->wValue = cpu_to_le16(value);
    dr->wIndex = cpu_to_le16(index);
    dr->wLength = cpu_to_le16(size);

    * dbg("usb_control_msg"); *

    ret = usb_internal_control_msg(dev, pipe, dr, data, size, timeout);

    kfree(dr);

    return ret;
}
EXPORT_SYMBOL_GPL(usb_control_msg);

* returns status (negative) or length (positive) *
static int usb_internal_control_msg(struct usb_device *usb_dev,
            unsigned int pipe,
                            struct usb_ctrlrequest *cmd,
                                                void *data, int len, int timeout)
{
    struct urb *urb;
    int retv;
    int length;

    urb = usb_alloc_urb(0, GFP_NOIO);
    if (!urb)
        return -ENOMEM;

    usb_fill_control_urb(urb, usb_dev, pipe, (unsigned char *)cmd, data,
                         len, usb_api_blocking_completion, NULL);

    retv = usb_start_wait_urb(urb, timeout, &length);
    if (retv < 0)
        return retv;
    else
        return length;
}


 * Starts urb and waits for completion or timeout. Note that this call
 * is NOT interruptible. Many device driver i/o requests should be
 * interruptible and therefore these drivers should implement their
 * own interruptible routines.
static int usb_start_wait_urb(struct urb *urb, int timeout, int *actual_length)
{
    struct api_context ctx;
    unsigned long expire;
    int retval;

    init_completion(&ctx.done);
    urb->context = &ctx;
    urb->actual_length = 0;
    retval = usb_submit_urb(urb, GFP_NOIO);
    if (unlikely(retval))
        goto out;

    expire = timeout ? msecs_to_jiffies(timeout) : MAX_SCHEDULE_TIMEOUT;
    if (!wait_for_completion_timeout(&ctx.done, expire)) {
        usb_kill_urb(urb);
        retval = (ctx.status == -ENOENT ? -ETIMEDOUT : ctx.status);

        dev_dbg(&urb->dev->dev,
            "%s timed out on ep%d%s len=%u/%u\n",
            current->comm,
            usb_endpoint_num(&urb->ep->desc),
            usb_urb_dir_in(urb) ? "in" : "out",
            urb->actual_length,
            urb->transfer_buffer_length);
    } else
        retval = ctx.status;
out:
    if (actual_length)
        *actual_length = urb->actual_length;

    usb_free_urb(urb);
    return retval;
}
int usb_submit_urb(struct urb *urb, gfp_t mem_flags)
{
    int             xfertype, max;
    struct usb_device       *dev;
    struct usb_host_endpoint    *ep;
    int             is_out;

    if (!urb || urb->hcpriv || !urb->complete)
        return -EINVAL;
    dev = urb->dev;
    if ((!dev) || (dev->state < USB_STATE_UNAUTHENTICATED))
        return -ENODEV;

    * For now, get the endpoint from the pipe.  Eventually drivers
     * will be required to set urb->ep directly and we will eliminate
     * urb->pipe.
    ep = (usb_pipein(urb->pipe) ? dev->ep_in : dev->ep_out)
            [usb_pipeendpoint(urb->pipe)];
    if (!ep)
        return -ENOENT;

    urb->ep = ep;
    urb->status = -EINPROGRESS;
    urb->actual_length = 0;

    * Lots of sanity checks, so HCDs can rely on clean data
     * and don't need to duplicate tests
    xfertype = usb_endpoint_type(&ep->desc);
    if (xfertype == USB_ENDPOINT_XFER_CONTROL) {
        struct usb_ctrlrequest *setup =
                (struct usb_ctrlrequest *) urb->setup_packet;

        if (!setup)
            return -ENOEXEC;
        is_out = !(setup->bRequestType & USB_DIR_IN) ||
                !setup->wLength;
    } else {
        is_out = usb_endpoint_dir_out(&ep->desc);
    }

    * Cache the direction for later use /
    urb->transfer_flags = (urb->transfer_flags & ~URB_DIR_MASK) |
            (is_out ? URB_DIR_OUT : URB_DIR_IN);

    if (xfertype != USB_ENDPOINT_XFER_CONTROL &&
            dev->state < USB_STATE_CONFIGURED)
        return -ENODEV;

    max = le16_to_cpu(ep->desc.wMaxPacketSize);
    if (max <= 0) {
        dev_dbg(&dev->dev,
            "bogus endpoint ep%d%s in %s (bad maxpacket %d)\n",
            usb_endpoint_num(&ep->desc), is_out ? "out" : "in",
            __func__, max);
        return -EMSGSIZE;
    }

    * periodic transfers limit size per frame/uframe,
     * but drivers only control those sizes for ISO.
     * while we're checking, initialize return status.
     /
    if (xfertype == USB_ENDPOINT_XFER_ISOC) {
        int n, len;

        * FIXME SuperSpeed isoc endpoints have up to 16 bursts /
        * "high bandwidth" mode, 1-3 packets/uframe? /
        if (dev->speed == USB_SPEED_HIGH) {
            int mult = 1 + ((max >> 11) & 0x03);
        if (dev->speed == USB_SPEED_HIGH) {
            int mult = 1 + ((max >> 11) & 0x03);
            max &= 0x07ff;
            max *= mult;
        }

        if (urb->number_of_packets <= 0)
            return -EINVAL;
        for (n = 0; n < urb->number_of_packets; n++) {
            len = urb->iso_frame_desc[n].length;
            if (len < 0 || len > max)
                return -EMSGSIZE;
            urb->iso_frame_desc[n].status = -EXDEV;
            urb->iso_frame_desc[n].actual_length = 0;
        }
    }

    * the I/O buffer must be mapped/unmapped, except when length=0 /
    if (urb->transfer_buffer_length > INT_MAX)
        return -EMSGSIZE;

#ifdef DEBUG
    * stuff that drivers shouldn't do, but which shouldn't
     * cause problems in HCDs if they get it wrong.
     /
    {
    unsigned int    orig_flags = urb->transfer_flags;
    unsigned int    allowed;

    * enforce simple/standard policy /
    allowed = (URB_NO_TRANSFER_DMA_MAP | URB_NO_SETUP_DMA_MAP |
            URB_NO_INTERRUPT | URB_DIR_MASK | URB_FREE_BUFFER);
    switch (xfertype) {
    case USB_ENDPOINT_XFER_BULK:
        if (is_out)
            allowed |= URB_ZERO_PACKET;
        * FALLTHROUGH /
    case USB_ENDPOINT_XFER_CONTROL:
        allowed |= URB_NO_FSBR; * only affects UHCI /
        * FALLTHROUGH /
    default:            * all non-iso endpoints /
        if (!is_out)
            allowed |= URB_SHORT_NOT_OK;
        break;
    case USB_ENDPOINT_XFER_ISOC:
        allowed |= URB_ISO_ASAP;
        break;
    }
    urb->transfer_flags &= allowed;

    * fail if submitter gave bogus flags /
    if (urb->transfer_flags != orig_flags) {
        dev_err(&dev->dev, "BOGUS urb flags, %x --> %x\n",
            orig_flags, urb->transfer_flags);
        return -EINVAL;
    }
    }
#endif
    *
     * Force periodic transfer intervals to be legal values that are
     * a power of two (so HCDs don't need to).
     *
     * FIXME want bus->{intr,iso}_sched_horizon values here.  Each HC
     * supports different values... this uses EHCI/UHCI defaults (and
     * EHCI can use smaller non-default values).
     /
    switch (xfertype) {
    case USB_ENDPOINT_XFER_ISOC:
    case USB_ENDPOINT_XFER_INT:
        * too small? /
        if (urb->interval <= 0)
            return -EINVAL;
        * too big? /
        switch (dev->speed) {
        case USB_SPEED_SUPER:   * units are 125us /
            * Handle up to 2^(16-1) microframes /
            if (urb->interval > (1 << 15))
                return -EINVAL;
            max = 1 << 15;
        case USB_SPEED_HIGH:    * units are microframes /
            * NOTE usb handles 2^15 /
            if (urb->interval > (1024 * 8))
                urb->interval = 1024 * 8;
            max = 1024 * 8;
            break;
        case USB_SPEED_FULL:    * units are frames/msec /
        case USB_SPEED_LOW:
            if (xfertype == USB_ENDPOINT_XFER_INT) {
                if (urb->interval > 255)
                    return -EINVAL;
                * NOTE ohci only handles up to 32 /
                max = 128;
            } else {
                if (urb->interval > 1024)
                    urb->interval = 1024;
                * NOTE usb and ohci handle up to 2^15 /
                max = 1024;
            }
            break;
        default:
            return -EINVAL;
        }
        * Round down to a power of 2, no more than max /
        urb->interval = min(max, 1 << ilog2(urb->interval));
    }

    return usb_hcd_submit_urb(urb, mem_flags);
}
EXPORT_SYMBOL_GPL(usb_submit_urb);

int usb_hcd_submit_urb (struct urb *urb, gfp_t mem_flags)
{
    int         status;
    struct usb_hcd      *hcd = bus_to_hcd(urb->dev->bus);

    * increment urb's reference count as part of giving it to the HCD
     * (which will control it).  HCD guarantees that it either returns
     * an error or calls giveback(), but not both.
     /
    usb_get_urb(urb);
    atomic_inc(&urb->use_count);
    atomic_inc(&urb->dev->urbnum);
    usbmon_urb_submit(&hcd->self, urb);

    * NOTE requirements on root-hub callers (usbfs and the hub
     * driver, for now):  URBs' urb->transfer_buffer must be
     * valid and usb_buffer_{sync,unmap}() not be needed, since
     * they could clobber root hub response data.  Also, control
     * URBs must be submitted in process context with interrupts
     * enabled.
     /
    status = map_urb_for_dma(hcd, urb, mem_flags);
    if (unlikely(status)) {
        usbmon_urb_submit_error(&hcd->self, urb, status);
        goto error;
    }

    if (is_root_hub(urb->dev))
        status = rh_urb_enqueue(hcd, urb);
    else
        status = hcd->driver->urb_enqueue(hcd, urb, mem_flags);

    if (unlikely(status)) {
        usbmon_urb_submit_error(&hcd->self, urb, status);
        unmap_urb_for_dma(hcd, urb);
 error:
        urb->hcpriv = NULL;
        INIT_LIST_HEAD(&urb->urb_list);
        atomic_dec(&urb->use_count);
        atomic_dec(&urb->dev->urbnum);
        if (atomic_read(&urb->reject))
            wake_up(&usb_kill_urb_queue);
        usb_put_urb(urb);
    }
    return status;
}



*/
#endif
