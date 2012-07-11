/*
 * IM-Me display functions
 *
 * Copyright 2010 Dave
 * http://daveshacks.blogspot.com/2010/01/im-me-lcd-interface-hacked.html
 *
 * Copyright 2010 Michael Ossmann
 *
 * Copyright 2011 atlas
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#include <cc1110.h>
#include "cc1110-ext.h"
#include "bits.h"
#include "immedisplay.h"
#include "immekeys.h"
#include "imme5x7.h"


void setIOPorts() {
	//No need to set PERCFG or P2DIR as default values on reset are fine
	P0SEL |= (BIT5 | BIT3 ); // set SCK and MOSI as peripheral outputs
	P0DIR |= BIT4 | BIT2; // set SSN and A0 as outputs
	P1DIR |= BIT1; // set LCDRst as output
	P2DIR = BIT3 | BIT4; // set LEDs  as outputs
	//LED_GREEN = LOW; // Turn the Green LED on (LEDs driven by reverse logic: 0 is ON)
}

void configureSPI() {
	U0CSR = 0;  //Set SPI Master operation
	U0BAUD =  SPI_BAUD_M; // set Mantissa
	U0GCR = U0GCR_ORDER | SPI_BAUD_E; // set clock on 1st edge, -ve clock polarity, MSB first, and exponent
}
void tx(unsigned char ch) {
	U0DBUF = ch;
	while(!(U0CSR & U0CSR_TX_BYTE)); // wait for byte to be transmitted
	U0CSR &= ~U0CSR_TX_BYTE;         // Clear transmit byte status
}

void txData(unsigned char ch) {
	A0 = HIGH;
	tx(ch);
}

void txCtl(unsigned char ch){
	A0 = LOW;
	tx(ch);
}

void LCDReset(void) {
	LCDRst = LOW; // hold down the RESET line to reset the display
	sleepMillis(1);
	LCDRst = HIGH;
	SSN = LOW;
	// send the initialisation commands to the LCD display
	txCtl(0xe2); // RESET cmd
	txCtl(0x24); // set internal resistor ratio
	txCtl(0x81); // set Vol Control
	txCtl(0x60); // set Vol Control - ctd
	txCtl(0xe6); // ?? -- don't know what this command is
	txCtl(0x00); // ?? -- don't know what this command is
	txCtl(0x2f); // set internal PSU operating mode
	txCtl(0xa1); // LCD bias set
	txCtl(0xaf); // Display ON
	txCtl(0xa4); // Normal (not all pixels) mode
	SSN = HIGH;
}

void LCDPowerSave() { // not tested yet; taken from spi trace
	txCtl(0xac); // static indicator off cmd
	txCtl(0xae); // LCD off
	txCtl(0xa5); // Display all Points on cmd = Power Save when following LCD off
}

void setCursor(unsigned char row, unsigned char col) {
	txCtl(0xb0 + row); // set cursor row
	txCtl(0x00 + (col & 0x0f)); // set cursor col low
	txCtl(0x10 + ( (col>>4) & 0x0f)); // set cursor col high
}

void setDisplayStart(unsigned char start) {
	txCtl(0x40 | (start & 0x3f)); // set Display start address
}

void setNormalReverse(unsigned char normal) {  // 0 = Normal, 1 = Reverse
	txCtl(0xa6 | (normal & 0x01) );
}

/* clear all LCD pixels */
void clear() {
	u8 row;
	u8 col;

	SSN = LOW;
	setDisplayStart(0);

	/* normal display mode (not inverted) */
	setNormalReverse(0);

	for (row = 0; row <= 9; row++) {
		setCursor(row, 0);
	for (col = 0; col < WIDTH; col++)
		txData(0x00);
	}

	SSN = HIGH;
}

/* sdcc provides printf if we provide this */
void putchar(char c) {
	u8 i;

	c &= 0x7f;

	if (c >= FONT_OFFSET) {
		for (i = 0; i < FONT_WIDTH; i++)
			txData(font[c - FONT_OFFSET][i]);
		txData(0x00);
	}
}

