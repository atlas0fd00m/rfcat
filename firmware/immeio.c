#include "global.h"
#include <string.h>
#include "immedisplay.h"
#include "immefont.h"
#include "immeio.h"
#include "imme5x7.h"
#include "immekeys.h"
#include "cc1111rf.h"

extern __xdata u32 recvCnt;

__xdata u8 imme_state;
__xdata u16 imme_state_counter;

char __xdata rxbuf[30];
u8 modulations[] = {MOD_2FSK, MOD_GFSK, MOD_ASKOOK, MOD_MSK};

u8 current_modulation;
char __code fsk2[] = "2FSK";
char __code gfsk[] = "GFSK";
char __code ask[] = "ASK ";
char __code msk[] = "MSK ";
char* __code modstrings[] = {fsk2, gfsk, ask, msk};



void initIMME(void)
{
    imme_state_counter = 0;
}

void reset (void){
    ((void (__code *) (void)) 0x0000) ();
}

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
  txCtl(0xa4); // Normal (not all pixels) mode.
  setNormalReverse(0); //Non-inverted screen.
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

void eraserow(u8 row){  
  u8 i;//column
  setCursor(row, 0);
  for (i=0; i<132; i++) { // clear every column on the line
    txData(0x00);
  };
}

void erasescreen(){
  u8 row;
  for(row=0;row<9;row++)
    eraserow(row);
}
  
void drawstr(u8 row, u8 col, char *str){
  u8 len=strlen(str);
  
  if (row >8) return;
  setCursor(row, col*6);
  
  while (len--)
    putch(*(str++));
}

void drawint32(u8 row, u8 col, u32 val){
  u8 byte, len = 0;
  u32 temp = 0;
  //FIXME prints backward.
  if (row >8) return;
  setCursor(row, col*6);

  while (val>0)
  {
      temp *= 10;
      temp += (val % 10);
      val /= 10;
      len ++;
  }

  for (;len>0; len--)
  {
    byte = (temp) % 10;
    putch('0'+(byte));
    temp /= 10;
  }
}

void drawint(u8 row, u8 col, u16 val){
  u8 byte, len=0;
  u16 temp = 0;
  //FIXME prints backward.
  if (row >8) return;
  setCursor(row, col*6);

  while (val>0)
  {
      temp *= 10;
      temp += (val % 10);
      val /= 10;
      len++;
  }

  for (;len>0;len--)
  {
    byte = (temp) % 10;
    putch('0'+(byte));
    temp /= 10;
  }
}

void drawhex(u8 row, u8 col, u16 val){
  u8 len=4;
  u16 nibble;
  if (row >8) return;
  setCursor(row, col*6);
  
  while (len--){
    nibble=(val&0xF000)>>12;
    if(nibble<10)
      putch('0'+nibble);
    else
      putch('A'+nibble-0xA);
    val<<=4;
  }
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

void usb_up(void)
{
#ifdef IMMEDONGLE
    // do somethin here.
#endif
}

void setModulation(u8 mod_format){
    MDMCFG2 = (MDMCFG2 & 0x8f) | (mod_format<<4);
}

char* getModulationStr(){
    return modstrings[current_modulation];
    //return modstrings[(((MDMCFG2>>4)&7)+1)>>1];
}

void setSyncMode(u8 sync_mode)
{
    MDMCFG2 = (MDMCFG2 & 0xf8) | (sync_mode&7);
}

void setChanBW(u32 chanbw)
{
    u8 chanbw_e = 0;
    u8 chanbw_m = 0;

    for (;chanbw_e<4; chanbw_e++)
    {
        chanbw_m = (((26000000 / (chanbw * (1<<chanbw_e) * 8.0 )) - 4) + .5);        // rounded evenly
        if (chanbw_m < 4)
            break;
    }

    MDMCFG4 = (MDMCFG4&0xf) | (chanbw_e<<6) | (chanbw_m<<4);
}

u32 getChanBW(void)
{
    u16 chanbw_e, chanbw_m, divisor;
    u32 bw;

    chanbw_e = MDMCFG4;
    chanbw_e >>= 6;
    chanbw_e &= 0x3;
    chanbw_m = MDMCFG4;
    chanbw_m >>= 4;
    chanbw_m &= 0x3;
    divisor = (8.0*(4+chanbw_m) * (1<<chanbw_e));
    bw = 26000000 / divisor;
    return bw;
}

void setBaud(u32 baud)
{
    u8 drate_e = 0;
    u32 drate_m = 0;

    for (;drate_e<16; drate_e++)
    {
        drate_m = ((baud / (1<<drate_e))* 10.324440615384615)-256 + .5;        // rounded evenly
        if (drate_m < 256)
            break;
    }

    //drate = 1000000.0 * mhz * (256+drate_m) * pow(2,drate_e) / pow(2,28)
    //print "drate_e: %x   drate_m: %x   drate: %f Hz" % (drate_e, drate_m, drate)
    
    MDMCFG4 = (MDMCFG4&0xf0) | drate_e;
    MDMCFG3 = (u8)drate_m;
}

u32 getBaud(void)
{
    u32 drate;
    u8 drate_m, drate_e;
    
    drate_e = MDMCFG4;
    drate_e &= 0xf;
    drate_m = MDMCFG3;

    drate = (1<<drate_e);
    drate *= (256+drate_m);
    drate *= 0.09685754776000977;
    return drate;
}

void incModulation(){
    current_modulation ++;
    if (current_modulation > 3)
        current_modulation = 0;
    setModulation(modulations[current_modulation]);
}

void decModulation(){
    if (current_modulation == 0)
        current_modulation = 3;
    else
        current_modulation --;
    setModulation(modulations[current_modulation]);
}

/* set the radio frequency in Hz */
void setRadioFrequency(u32 freq) {
    /* the frequency setting is in units of 396.728515625 Hz */
    u32 setting = (u32) (freq * .0025206154);
    FREQ2 = (setting >> 16) & 0xff;
    FREQ1 = (setting >> 8) & 0xff;
    FREQ0 = setting & 0xff;
}

u32 getRadioFrequency(void)
{
    u32 freq;
    freq = FREQ2;
    freq <<= 8;
    freq += FREQ1;
    freq <<= 8;
    freq += FREQ0;
    freq *= 396.7285132035613;
    return freq;
}



void immeLCDUpdateState(void)
{
    SSN=LOW;
    drawhex(7, 0, MARCSTATE);
    drawhex(7,10, rfif);
    SSN=HIGH;
}

void immeLCDShowRFConfig(void)
{
    u32 dummy32;
    u16 syncw;
    //u8 len, nibble;
    //u8* pval;

    SSN = LOW;
    erasescreen();
    drawstr(1,0,"FRQ"); 
    drawstr(2,0,"CH");
    drawstr(3,0,"MOD"); 
    drawstr(4,0,"BAUD");
    drawstr(5,0,"CHANBW");
    drawstr(6,0,"SYNCW");
    drawstr(1,6,"          ");
    dummy32 = getRadioFrequency();
    drawint32(1,6,dummy32);
    drawhex(2,6,CHANNR);
    drawstr(3,6,getModulationStr());
    dummy32 = getBaud();
    /*setCursor(4, 6);
    len = 4;
    pval = (u8*)&dummy32;
    while (len--)
    {
            // high nibble
            nibble=(*(pval) & 0xF0)>>4;
            if(nibble<10)
                putch('0'+nibble);
            else
                putch('A'+nibble-0xA);

            // low nibble
            nibble=((*pval)&0x0F);
            if(nibble<10)
                putch('0'+nibble);
            else
                putch('A'+nibble-0xA);
        pval ++;
    }
    */

    drawstr(4,6,"        ");
    drawint32(4,6,dummy32);
    drawstr(5,8,"        ");
    dummy32 = getChanBW();
    drawstr(5,8,"          ");
    drawint32(5,8,dummy32);
    drawhex(4,15, MDMCFG4);
    drawhex(5,15, MDMCFG3);
    drawhex(6,15, MDMCFG2);
    if (MDMCFG2 & 3)
    {
        syncw = SYNC1;
        syncw <<= 8;
        syncw |= SYNC0;
        drawhex(6,6,syncw);
    }
    else
        drawstr(6,6,"----");

    SSN = HIGH;
}

void immeLCDInitScreen(void)
{
    SSN = LOW;
    erasescreen();
    immeLCDInitialState();
    SSN = HIGH;
}

void immeLCDShowPacket(void)
{
    __xdata u8 *pval = &rfrxbuf[!rfRxCurrentBuffer][0];
    __xdata u8 len   = rfRxCounter[!rfRxCurrentBuffer];
    __xdata u8 count = 0;
    __xdata u8 line = 3;
    __xdata u16 nibble;

    SSN=LOW;
    drawstr(3,0, "                                ");
    drawstr(4,0, "                                ");
    drawstr(5,0, "                                ");
    //blink_binary_baby_lsb(len, 8);
    drawstr(1,0, "Length: ");
    drawhex(1,9, len);
    drawstr(2,0, "Curr: ");
    drawhex(2,6, rfRxCurrentBuffer);
    drawstr(2,12, "Cnt: ");
    drawhex(2,17, recvCnt);
    if (len>30)
        len = 30;

    // not print the packet data, one byte if "printable" or two bytes if hex-representation makes more sense
    setCursor(line, 0);
    while (len--)
    {
        if (*pval > 0x1f && *pval < 0x7f)
        {
            putch(' ');
            putch(*pval);
        } else
        {

            // high nibble
            nibble=(*(pval) & 0xF0)>>4;
            if(nibble<10)
                putch('0'+nibble);
            else
                putch('A'+nibble-0xA);

            // low nibble
            nibble=((*pval)&0x0F);
            if(nibble<10)
                putch('0'+nibble);
            else
                putch('A'+nibble-0xA);
        }

        if (++count % 10 == 0)
        {
            setCursor(++line, 0);
        }
        pval ++;
    }

    //drawstr(2,0, rfrxbuf[processbuffer]+1);
    SSN=HIGH;
}

/* just a little keyboard poller */
                /* couple things for poll_keyboard:
                 * Sleep (off)
                 * pause (wow, the packets fly by!
                 * slow... perhaps a settable delay that we can increment by kb
                 * freq +-
                 * channel +-
                 * chanspc +-
                 * baud +-
                 * modulation +-
                 * PQT mode +-
                 * set sync word
                 *
                 */
void poll_keyboard() {
    u16 tmp;

    switch (imme_state)
    {
        case IMME_STATE_CONFIG_SCREEN:
            if (imme_state_counter >= 300)
            {
                imme_state_counter = 0;
                imme_state = IMME_STATE_SNIFF;
                immeLCDInitScreen();
                immeLCDShowPacket();
            }
            else
                imme_state_counter ++;
        default:
            imme_state_counter = 0;
    }

	switch (getkey()) {
        // frequency/channel
        // modulation - KMNU/KBYE
        // baud - KRIGHT/KLFT
        // syncword - qawsedrfg
	case 'Q':   // highest nibble incr
        LED_GREEN != LED_GREEN;
        RFOFF;
        MDMCFG2 &= 0xf8;
        MDMCFG2 |= 0x05;
        SYNC1 += 0x10;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);


        RFCAL;
        RFRX;

        break;
	case 'A':   // highest nibble decr
        RFOFF;
        MDMCFG2 &= 0xf8;
        MDMCFG2 |= 0x05;
        SYNC1 -= 0x10;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;
	case 'W':   // highbyte, lower nibble incr
        RFOFF;
        MDMCFG2 &= 0xf8;
        MDMCFG2 |= 0x05;
        if ((SYNC1 & 0xf) != 0xf)
            SYNC1 ++;
        else
            SYNC1 = (SYNC1 & 0xf0);

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;
	case 'S':   // highbyte, lower nibble decr
        RFOFF;
        MDMCFG2 &= 0xf8;
        MDMCFG2 |= 0x05;
        if (SYNC1&0xf)
            SYNC1 --;
        else
            SYNC1 = (SYNC1&0xf0) + 9;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;
	case 'E':   // lowbyte, upper nibble incr
        RFOFF;
        MDMCFG2 &= 0xf8;
        MDMCFG2 |= 0x05;
        SYNC0 += 0x10;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);
        
        RFCAL;
        RFRX;

        break;
	case 'D':   // lowbyte, upper nibble decr
        RFOFF;
        MDMCFG2 &= 0xf8;
        MDMCFG2 |= 0x05;
        SYNC0 -= 0x10;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);
        
        RFCAL;
        RFRX;

        break;
	case 'R':   // lowest nibble incr
        RFOFF;
        MDMCFG2 &= 0xf8;
        MDMCFG2 |= 0x05;
        if (SYNC0&0xf == 9)
            SYNC0 = (SYNC0&0xf0);
        else
            SYNC0 ++;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;
	case 'F':   // lowest nibble decr
        RFOFF;
        MDMCFG2 &= 0xf8;
        MDMCFG2 |= 0x05;
        if (SYNC0&0xf == 0)
            SYNC0 = (SYNC0&0xf0) + 9;
        else
            SYNC0 --;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;
	case 'Z':   // no sync word
        RFOFF;
        MDMCFG2 &= 0xf8;
        MDMCFG2 |= 0x04;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;
	case KMNU:  // modulation
        RFOFF;
        incModulation();

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;
	case KBYE:  // modulation
        RFOFF;
        decModulation();

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;
	case KUP:   // bandwidth
        RFOFF;
        tmp = MDMCFG4;
        tmp = (tmp + 0x10);
        if (tmp > 0xff)
            tmp -= 0xf0;
        MDMCFG4 = (u8)tmp;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;

	case KDWN:  // bandwidth
        RFOFF;
        tmp = MDMCFG4;
        if (tmp < 0x10)
            tmp += 0x100;
        tmp -= 0x10;

        MDMCFG4 = (u8)tmp;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;

	case KRIGHT:// baud incr
        RFOFF;
        //
        //if (getBaud()>=2200)
        //    setBaud(getBaud()>>1);
        if ((MDMCFG3 >> 4) == 0xf)
        {
            if ((MDMCFG4 & 0xf) < 0xf)
            {
                MDMCFG4 += 1;
                MDMCFG3 += 0x10;
            }
        }
        else
        {
            MDMCFG3 += 0x10;
        }

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;
	case KLEFT: // baud decr
        RFOFF;
        //
        //if (getBaud() <=250000)
        //    setBaud(getBaud()<<1);
        if ((MDMCFG3 >> 4) == 0x0)
        {
            if ((MDMCFG4 & 0xf) > 0x0)
            {
                MDMCFG4 -= 1;
                MDMCFG3 -= 0x10;
            }
        }
        else
        {
            MDMCFG3 -= 0x10;
        }


        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;
        sleepMillis(50);

        RFCAL;
        RFRX;

        break;

	case 'P': // freq incr
        RFOFF;
        FREQ0 ++;
        if (FREQ0 == 0)
        {
            FREQ1++;
            if (FREQ1 == 0)
                FREQ2++;
        }

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case KENTER: // freq decr
        RFOFF;
        FREQ0 --;
        if (FREQ0 == 0xff)
        {
            FREQ1--;
            if (FREQ1 == 0xff)
                FREQ2--;
        }

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'O': // freq incr
        RFOFF;
        if (FREQ0 >= 0xf0)
        {
            FREQ1++;
            if (FREQ1 == 0)
                FREQ2++;
        }
        FREQ0 += 0x10;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case ',': // freq decr
        RFOFF;
        if (FREQ0 <= 0x10)
        {
            if (FREQ1 == 0)
                FREQ2--;
            FREQ1--;
        }
        FREQ0 -= 0x10;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'I': // freq incr
        RFOFF;

        FREQ1++;
        if (FREQ1 == 0)
            FREQ2++;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'M': // freq decr
        RFOFF;

        if (FREQ1 == 0)
            FREQ2--;
        FREQ1--;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'U': // freq incr
        RFOFF;

        FREQ2++;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'N': // freq decr
        RFOFF;

        FREQ2--;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'L': // freq set 915
        RFOFF;

        FREQ2       = 0x23;
        FREQ1       = 0x31;//0x71;
        FREQ0       = 0x3b;//0x7c;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'K': // freq set 868
        RFOFF;

        FREQ2       = 0x21;
        FREQ1       = 0x62;//0x71;
        FREQ0       = 0x76;//0x7c;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'J': // freq set 433
        RFOFF;

        FREQ2       = 0x10;
        FREQ1       = 0xa7;//0x71;
        FREQ0       = 0x62;//0x7c;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'H': // freq set 315
        RFOFF;

        FREQ2       = 0x0c;
        FREQ1       = 0x1d;//0x71;
        FREQ0       = 0x89;//0x7c;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;


	case 'G': // channr incr
        RFOFF;

        CHANNR = 0;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'T': // channr incr
        RFOFF;

        CHANNR ++;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;

	case 'V': // channr incr
        RFOFF;

        CHANNR --;

        immeLCDShowRFConfig();
        imme_state = IMME_STATE_CONFIG_SCREEN;
        imme_state_counter = 0;

        RFCAL;
        RFRX;

        break;


	case KPWR:
        LCDPowerSave();
        //TODO power down CC1110 here.
        while(keyscan()!=KPWR);
        reset();
  
        break;

    case KSPK:
        if (MARCSTATE == MARC_STATE_RX)
        {
            RFOFF;
            TxMode();
        }
        else
        {
            RFOFF;
            RxMode();
        }

        break;
    case ' ':
        if (imme_state == IMME_STATE_SNIFF)
        {
            imme_state = IMME_STATE_CONFIG_SCREEN;
            immeLCDShowRFConfig();
        }
        else if (imme_state == IMME_STATE_CONFIG_SCREEN)
        {
            imme_state = IMME_STATE_SNIFF;
            immeLCDInitScreen();
            immeLCDShowPacket();
        }
        break;
	default:
		break;
	}
}

