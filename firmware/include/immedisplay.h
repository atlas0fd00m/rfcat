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

#define LOW 0
#define HIGH 1

#define WIDTH  132
#define HEIGHT 65

void sleepMillis(int ms);

void xtalClock();

// IO Port Definitions:
#define A0 P0_2
#define SSN P0_4
#define LCDRst P1_1
//#define LED_RED  P2_3
//#define LED_GREEN P2_4
// plus SPI ports driven from USART0 are:
// MOSI P0_3
// SCK P0_5

void setIOPorts();

void configureSPI();

void tx(unsigned char ch);

void txData(unsigned char ch);

void txCtl(unsigned char ch);

void LCDReset(void);

void LCDPowerSave();

void setCursor(unsigned char row, unsigned char col);

void setDisplayStart(unsigned char start);

void setNormalReverse(unsigned char normal);

void clear();

void putchar(char c);
