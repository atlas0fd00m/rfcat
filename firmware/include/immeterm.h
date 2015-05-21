
#include <cc1110.h>
#include "cc1110-ext.h"
//#include "hal_cc8051.h"

#include "bits.h"

#include "immefont.h"
#include "immeio.h"
//#include "string.h"
#include "immekeys.h"
//#include "power.h"


//Apps
#define LOW 0;
#define HIGH 1;

//times.c
void sleepMillis(int ms);
void xtalClock();

//io.c
// IO Port Definitions:
#define A0 P0_2
#define SSN P0_4
#define LCDRst P1_1
#define LED_RED P2_3
#define LED_GREEN P2_4
// plus SPI ports driven from USART0 are:
// MOSI P0_3
// SCK P0_5

//! Sets not !normal
void setNormalReverse(unsigned char normal);
//! Start the display.
void setDisplayStart(unsigned char start);

//! Initialize the IO ports.
void setIOPorts();

// Set a clock rate of approx. 2.5 Mbps for 26 MHz Xtal clock
#define SPI_BAUD_M  170
#define SPI_BAUD_E  16

void configureSPI();
void tx(unsigned char ch);
void txData(unsigned char ch);
void txCtl(unsigned char ch);

//! Reset the LCD display.
void LCDReset(void);

//! Power save, not yet tested.
void LCDPowerSave();

//! Set the cursor position.
void setCursor(unsigned char row, unsigned char col) ;


void fail(char * __xdata msg);
