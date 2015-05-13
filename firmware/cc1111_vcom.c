/*
 * CC Bootloader - USB CDC class (serial) driver
 *
 * Adapted from AltOS code by Fergus Noble (c) 2011
 * AltOS code Copyright © 2009 Keith Packard <keithp@keithp.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; version 2 of the License.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA.
 */

#include "cc1111_vcom.h"

static __xdata u16 usb_in_bytes;
static __xdata u16 usb_in_bytes_last;
static __xdata u16 usb_out_bytes;
volatile static __xdata u8  usb_iif;
static __xdata u8  usb_running;

__xdata __at (0xde20) volatile u8 USBFIFO[12];


static void vcom_set_interrupts()
{
  // IN interrupts on the control an IN endpoints
  USBIIE = (1 << USB_CONTROL_EP) | (1 << USB_IN_EP);
  // OUT interrupts on the OUT endpoint
  USBOIE = (1 << USB_OUT_EP);
  // Only care about reset
  USBCIE = USBCIE_RSTIE;
}

struct usb_setup {
  u8   dir_type_recip;
  u8   request;
  u16  value;
  u16  index;
  u16  length;
} __xdata usb_setup;

__xdata u8 usb_ep0_state;
u8 * __xdata usb_ep0_in_data;
__xdata u8 usb_ep0_in_len;
__xdata u8 usb_ep0_in_buf[2];
__xdata u8 usb_ep0_out_len;
__xdata u8 *__xdata usb_ep0_out_data;
__xdata u8 usb_configuration;

// Send an IN data packet
static void vcom_ep0_flush()
{
  __xdata u8 this_len;
  __xdata u8 cs0;

  // If the IN packet hasn't been picked up, just return
  USBINDEX = 0;
  cs0 = USBCS0;
  if (cs0 & USBCS0_INPKT_RDY)
    return;

  this_len = usb_ep0_in_len;
  if (this_len > USB_CONTROL_SIZE)
    this_len = USB_CONTROL_SIZE;
  cs0 = USBCS0_INPKT_RDY;
  if (this_len != USB_CONTROL_SIZE) {
    cs0 = USBCS0_INPKT_RDY | USBCS0_DATA_END;
    usb_ep0_state = USB_EP0_IDLE;
  }
  usb_ep0_in_len -= this_len;
  while (this_len--)
    USBFIFO[0] = *usb_ep0_in_data++;
  USBINDEX = 0;
  USBCS0 = cs0;
}

__xdata static struct usb_line_coding usb_line_codings = {115200, 0, 0, 8};

// Walk through the list of descriptors and find a match
static void vcom_get_descriptor(u16 value)
{
  const u8   *__xdata descriptor;
  __xdata u8   type = value >> 8;
  __xdata u8   index = value;

  descriptor = usb_descriptors;
  while (descriptor[0] != 0) {
    if (descriptor[1] == type && index-- == 0) {
      if (type == USB_DESC_CONFIGURATION)
        usb_ep0_in_len = descriptor[2];
      else
        usb_ep0_in_len = descriptor[0];
      usb_ep0_in_data = descriptor;
      break;
    }
    descriptor += descriptor[0];
  }
}

// Read data from the ep0 OUT fifo
static void vcom_ep0_fill()
{
  __xdata u8 len;

  USBINDEX = 0;
  len = USBCNT0;
  if (len > usb_ep0_out_len)
    len = usb_ep0_out_len;
  usb_ep0_out_len -= len;
  while (len--)
    *usb_ep0_out_data++ = USBFIFO[0];
}

void vcom_ep0_queue_byte (u8 a)
{
  usb_ep0_in_buf[usb_ep0_in_len++] = a;
}

void vcom_set_address (u8 address)
{
  usb_running = 1;
  USBADDR = address | 0x80;
  while (USBADDR & 0x80) {}
}

static void vcom_set_configuration()
{
  // Set the IN max packet size, double buffered
  USBINDEX = USB_IN_EP;
  USBMAXI = USB_IN_SIZE >> 3;
  USBCSIH |= USBCSIH_IN_DBL_BUF;

  // Set the OUT max packet size, double buffered
  USBINDEX = USB_OUT_EP;
  USBMAXO = USB_OUT_SIZE >> 3;
  USBCSOH = USBCSOH_OUT_DBL_BUF;
}

static void vcom_ep0_setup()
{
  // Pull the setup packet out of the fifo
  usb_ep0_out_data = (__xdata u8 *) &usb_setup;
  usb_ep0_out_len = 8;
  vcom_ep0_fill();
  if (usb_ep0_out_len != 0)
    return;

  // Figure out how to ACK the setup packet
  if (usb_setup.dir_type_recip & USB_DIR_IN) {
    if (usb_setup.length)
      usb_ep0_state = USB_EP0_DATA_IN;
    else
      usb_ep0_state = USB_EP0_IDLE;
  } else {
    if (usb_setup.length)
      usb_ep0_state = USB_EP0_DATA_OUT;
    else
      usb_ep0_state = USB_EP0_IDLE;
  }
  USBINDEX = 0;
  if (usb_ep0_state == USB_EP0_IDLE)
    USBCS0 = USBCS0_CLR_OUTPKT_RDY | USBCS0_DATA_END;
  else
    USBCS0 = USBCS0_CLR_OUTPKT_RDY;

  usb_ep0_in_data = usb_ep0_in_buf;
  usb_ep0_in_len = 0;
  switch(usb_setup.dir_type_recip & USB_SETUP_TYPE_MASK) {
    case USB_TYPE_STANDARD:
      switch(usb_setup.dir_type_recip & USB_SETUP_RECIP_MASK) {
        case USB_RECIP_DEVICE:
          switch(usb_setup.request) {
            case USB_REQ_GET_STATUS:
                vcom_ep0_queue_byte(0);
                vcom_ep0_queue_byte(0);
                break;
            case USB_REQ_SET_ADDRESS:
                vcom_set_address(usb_setup.value);
                break;
            case USB_REQ_GET_DESCRIPTOR:
                vcom_get_descriptor(usb_setup.value);
                break;
            case USB_REQ_GET_CONFIGURATION:
                vcom_ep0_queue_byte(usb_configuration);
              break;
            case USB_REQ_SET_CONFIGURATION:
              usb_configuration = usb_setup.value;
              vcom_set_configuration();
              break;
          }
          break;
        case USB_RECIP_INTERFACE:
          #pragma disable_warning 110
          switch(usb_setup.request) {
            case USB_REQ_GET_STATUS:
                vcom_ep0_queue_byte(0);
                vcom_ep0_queue_byte(0);
              break;
            case USB_REQ_GET_INTERFACE:
                vcom_ep0_queue_byte(0);
              break;
            case USB_REQ_SET_INTERFACE:
              break;
          }
          break;
        case USB_RECIP_ENDPOINT:
          switch(usb_setup.request) {
            case USB_REQ_GET_STATUS:
                vcom_ep0_queue_byte(0);
                vcom_ep0_queue_byte(0);
              break;
          }
          break;
      }
      break;
    case USB_TYPE_CLASS:
      switch (usb_setup.request) {
        case SET_LINE_CODING:
          usb_ep0_out_len = 7;
          usb_ep0_out_data = (__xdata u8 *) &usb_line_codings;
          break;
        case GET_LINE_CODING:
          usb_ep0_in_len = 7;
          usb_ep0_in_data = (u8 *) &usb_line_codings;
          break;
        case SET_CONTROL_LINE_STATE:
          break;
      }
      break;
  }
  if (usb_ep0_state != USB_EP0_DATA_OUT) {
    if (usb_setup.length < usb_ep0_in_len)
      usb_ep0_in_len = usb_setup.length;
    vcom_ep0_flush();
  }
}

// End point 0 receives all of the control messages.
// This function must be called periodically to process ep0 messages.
static void vcom_ep0()
{
  __xdata u8 cs0;

  // If the ep0 flag has been set by the USB interrupt then do some processing
  if (usb_iif & 1)
  {
    usb_iif &= ~1; // clear flag

    USBINDEX = 0;
    cs0 = USBCS0;
    if (cs0 & USBCS0_SETUP_END) {
      usb_ep0_state = USB_EP0_IDLE;
      USBCS0 = USBCS0_CLR_SETUP_END;
    }
    if (cs0 & USBCS0_SENT_STALL) {
      usb_ep0_state = USB_EP0_IDLE;
      USBCS0 &= ~USBCS0_SENT_STALL;
    }
    if (usb_ep0_state == USB_EP0_DATA_IN &&
        (cs0 & USBCS0_INPKT_RDY) == 0)
    {
        vcom_ep0_flush();
    }
    if (cs0 & USBCS0_OUTPKT_RDY) {
      switch (usb_ep0_state) {
        case USB_EP0_IDLE:
            vcom_ep0_setup();
          break;
        case USB_EP0_DATA_OUT:
            vcom_ep0_fill();
          if (usb_ep0_out_len == 0)
            usb_ep0_state = USB_EP0_IDLE;
          USBINDEX = 0;
          if (usb_ep0_state == USB_EP0_IDLE)
            USBCS0 = USBCS0_CLR_OUTPKT_RDY | USBCS0_DATA_END;
          else
            USBCS0 = USBCS0_CLR_OUTPKT_RDY;
          break;
      }
    }
  }
}

// This interrupt is shared with port 2,
// so when we hook that up, fix this
void usbIntHandler(void) __interrupt P2INT_VECTOR
{
  USBIF = 0;
  usb_iif |= USBIIF;
  vcom_ep0();

  if (USBCIF & USBCIF_RSTIF)
      vcom_set_interrupts();
}

void p0IntHandler(void) interrupt P0INT_VECTOR
{
    while (!IS_XOSC_STABLE());

    SLEEP &= ~0x3;                                  // clear the PM mode bits
    USB_RESUME_INT_CLEAR();
    
}

// Wait for a free IN buffer
static void vcom_in_wait()
{
  while (1) {
    USBINDEX = USB_IN_EP;
    if ((USBCSIL & USBCSIL_INPKT_RDY) == 0)
      break;
    while (!(usb_iif & (1 << USB_IN_EP))) {}
  }
}

// Send the current IN packet
static void vcom_in_send()
{
  USBINDEX = USB_IN_EP;
  USBCSIL |= USBCSIL_INPKT_RDY;
  usb_in_bytes_last = usb_in_bytes;
  usb_in_bytes = 0;
}

void vcom_flush()
{
  if (!usb_running)
    return;

  // If there are pending bytes, or if the last packet was full,
  // send another IN packet
  if (usb_in_bytes || (usb_in_bytes_last == USB_IN_SIZE)) {
      vcom_in_wait();
      vcom_in_send();
  }
}

void vcom_putchar(char c) __reentrant
{
  if (!usb_running)
    return;

  vcom_in_wait();

  // Queue a byte, sending the packet when full
  USBFIFO[USB_IN_EP << 1] = c;
  if (++usb_in_bytes == USB_IN_SIZE)
      vcom_in_send();
}

char vcom_pollchar()
{
  char c;
  if (usb_out_bytes == 0) {
    USBINDEX = USB_OUT_EP;
    if ((USBCSOL & USBCSOL_OUTPKT_RDY) == 0)
      return USB_READ_AGAIN;
    usb_out_bytes = (USBCNTH << 8) | USBCNTL;
    if (usb_out_bytes == 0) {
      USBINDEX = USB_OUT_EP;
      USBCSOL &= ~USBCSOL_OUTPKT_RDY;
      return USB_READ_AGAIN;
    }
  }
  --usb_out_bytes;
  c = USBFIFO[USB_OUT_EP << 1];
  if (usb_out_bytes == 0) {
    USBINDEX = USB_OUT_EP;
    USBCSOL &= ~USBCSOL_OUTPKT_RDY;
  }
  return c;
}

char vcom_getchar()
{
  char c;
  while ((c = vcom_pollchar()) == USB_READ_AGAIN)
  {
    while (!(USBOIF & (1 << USB_OUT_EP))) {}
  }
  return c;
}

void vcom_enable()
{
  // Turn on the USB controller
  SLEEP |= SLEEP_USB_EN;

  vcom_set_configuration();
  vcom_set_interrupts();

  // enable USB interrupts
  IEN2 |= IEN2_USBIE;

  // Clear any pending interrupts
  USBCIF = 0;
  USBOIF = 0;
  USBIIF = 0;
  USBIF = 0;
}

void vcom_disable()
{
  // Disable USB interrupts
  USBIIE = 0;
  USBOIE = 0;
  USBCIE = 0;
  IEN2 &= ~IEN2_USBIE;

  // Clear any pending interrupts
  USBCIF = 0;
  USBOIF = 0;
  USBIIF = 0;

  // Turn off the USB controller
  SLEEP &= ~SLEEP_USB_EN;
}

void initUSB()
{
  // Init ep0
    usb_ep0_state = USB_EP0_IDLE;
    usb_iif = 0;
    vcom_enable();
}

void usbProcessEvents()
{    
    return; /* dummy function */
}

void vcom_readline(char* buff) {
  char c;
  while ((c = vcom_getchar()) != '\n') {
    *buff++ = c;
  }
  *buff = 0;
}

void vcom_putstr(char* buff) {
  while (*buff) {
      vcom_putchar(*buff++);
  }
  vcom_flush();
}

void usb_up() {
  // Bring up the USB link
    P1DIR |= 0x02;
    P1_1 = 1;
}

void vcom_down() {
  // Bring down the USB link
  P1_1 = 0;
  P1DIR &= ~0x02;
}

int txdata(u8 app, u8 cmd, u16 len, xdata u8* dataptr)
{
    u16 test = 0;

    /*removes warning */    
    test = app = cmd = len;

    /* function from usb thing, only need data ptr */    
      while (*dataptr) 
    {
          vcom_putchar(*dataptr++);
      }
    vcom_flush();
}
