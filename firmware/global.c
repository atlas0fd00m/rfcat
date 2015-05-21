#include "global.h"

// used for debugging and tracing execution.  see client's ".getDebugCodes()"
__xdata u8 lastCode[2];
__xdata u32 clock;



void sleepMillis(int ms) 
{
    int j;
    while (--ms > 0) 
    { 
        for (j=0; j<SLEEPTIMER;j++); // about 1 millisecond
    }
}


void sleepMicros(int us) 
{
    // this while loop for an int takes 11 instructions, which takes 4.5833uS and 4.2308uS
    // at 24MHz and 26MHz
    us *= PLATFORM_CLOCK_FREQ/11;
    while (--us > 0) ;
}

void blink_binary_baby_lsb(u16 num, char bits)
{
    LED = 1;
    sleepMillis(1000);
    LED = 0;
    sleepMillis(500);
    bits -= 1;          // 16 bit numbers needs to start on bit 15, etc....

    for (; bits>=0; bits--)
    {
        if (num & 1)
        {
            sleepMillis(25);
            LED = 1;
            sleepMillis(550);
            LED = 0;
            sleepMillis(25);
        }
        else
        {
            sleepMillis(275);
            LED = 1;
            sleepMillis(50);
            LED = 0;
            sleepMillis(275);
        }
        num = num >> 1;
    }
    LED = 0;
    sleepMillis(1000);
}

/*
void blink_binary_baby_msb(u16 num, char bits)
{
    LED = 1;
    sleepMillis(1500);
    LED = 0;
    sleepMillis(100);
    bits -= 1;          // 16 bit numbers needs to start on bit 15, etc....

    for (; bits>=0; bits--)
    {
        if (num & (1<<bits))
        {
            LED = 0;
            sleepMillis(10);
            LED = 1;
        }
        else
        {
            LED = 1;
            sleepMillis(10);
            LED = 0;
        }
        sleepMillis(350);
    }
    LED = 0;
    sleepMillis(1500);
}*/

int strncmp(const char * __xdata s1, const char * __xdata s2, u16 n)
{
    char tst;

    for (;n>0;n--)
    {
        tst = *s1 - *s2;
        if (tst)
            return tst;
        s1++;
        s2++;
    }
    return 0;
}

void clock_init(void)
{
    //  SET UP CPU SPEED!  USE 26MHz for CC1110 and 24MHz for CC1111
    // Set the system clock source to HS XOSC and max CPU speed,
    // ref. [clk]=>[clk_xosc.c]
    SLEEP &= ~SLEEP_OSC_PD;
    while( !(SLEEP & SLEEP_XOSC_S) );
    CLKCON = (CLKCON & ~(CLKCON_CLKSPD | CLKCON_OSC)) | CLKSPD_DIV_1;
    while (CLKCON & CLKCON_OSC);
    SLEEP |= SLEEP_OSC_PD;
    while (!IS_XOSC_STABLE());
    
    // FIXME: this should be defined so it works with 24/26mhz
    // setup TIMER 1
    // free running mode
    // time freq:       187.50 for cc1111 / 203.125kHz for cc1110
    CLKCON &= 0xc7;          //( ~ 0b00111000);  - clearing out TICKSPD  freq = 24mhz on cc1111, 26mhz on cc1110
    
    T1CTL |= T1CTL_DIV_128;     // T1 running at 187.500 kHz
    T1CTL |= T1CTL_MODE_FREERUN;
    T1IE = 1;

}



/* initialize the IO subsystems for the appropriate dongles */
void io_init(void)
{
#ifdef IMME
    
 #ifdef IMMEDONGLE   // CC1110 on IMME pink dongle
    // IM-ME Dongle.  It's a CC1110, so no USB stuffs.  Still, a bit of stuff to init for talking 
    // to it's own Cypress USB chip
    P0SEL |= (BIT5 | BIT3);     // Select SCK and MOSI as SPI
    P0DIR |= BIT4 | BIT6;       // SSEL and LED as output
    P0 &= ~(BIT4 | BIT2);       // Drive SSEL and MISO low

    P1IF = 0;                   // clear P1 interrupt flag
    IEN2 |= IEN2_P1IE;          // enable P1 interrupt
    P1IEN |= BIT1;              // enable interrupt for P1.1

    P1DIR |= BIT0;              // P1.0 as output, attention line to cypress
    P1 &= ~BIT0;                // not ready to receive
 #else              // full blown IMME with screen and keyboard
    
    //Disable WDT
    IEN2&=~IEN2_WDTIE;
    IEN0&=~EA;
    setIOPorts();
    configureSPI();
    LCDReset();
  
    //Startup display.
    setDisplayStart(0);
    SSN = LOW;
    setNormalReverse(0);
    erasescreen();
    drawstr(0,0, "IMME SNIFF v0.1");
    SSN = HIGH;

    //immeLCDInitScreen();
    //sleepMillis(100);
  
 #endif 
#else       // CC1111
 #ifdef DONSDONGLES
    // CC1111 USB Dongle
    // turn on LED and BUTTON
    P1DIR |= 3;
    // Activate BUTTON - Do we need this?
    //CC1111EM_BUTTON = 1;

 #elif defined YARDSTICKONE
    // USB, LED1, LED2, and LED3
    P1DIR |= 0xf;
    // amplifer configuration pins
    P2DIR |= 0x19;
    // initial states
    LED2 = 0;
    LED3 = 0;
    TX_AMP_EN = 0;
    RX_AMP_EN = 0;
    AMP_BYPASS_EN = 1;

 #else
    // CC1111 USB (ala Chronos watch dongle), we just need LED
    P1DIR |= 3;

 #endif      // CC1111

 #ifndef VIRTUAL_COM
    // Turn off LED
    LED = 0;
 #endif

#endif // conditional
}


void t1IntHandler(void) __interrupt T1_VECTOR  // interrupt handler should trigger on T1 overflow
{   
    clock ++;
}

