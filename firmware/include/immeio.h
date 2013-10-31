#include "types.h"

void immeLCDUpdateState(void);
void immeLCDShowRFConfig(void);
void immeLCDInitScreen(void);
void immeLCDShowPacket(void);

void eraserow(u8 row);
void erasescreen();
void drawstr(u8 row, u8 col, char *str);
void drawint(u8 row, u8 col, u16 val);
void drawhex(u8 row, u8 col, u16 val);
void poll_keyboard();
void usb_up(void);
void initIMME(void);

// provided by firmware //////////
void immeLCDInitialState(void);
//////////////////////////////////

// Set a clock rate of approx. 2.5 Mbps for 26 MHz Xtal clock
#define SPI_BAUD_M  170
#define SPI_BAUD_E  16

#define IMME_STATE_CONFIG_SCREEN 1
#define IMME_STATE_SNIFF 0

#define MOD_2FSK    0
#define MOD_GFSK    1
#define MOD_ASKOOK  3
#define MOD_MSK     7

extern char __xdata rxbuf[30];
extern u8 modulations[];
extern u8 current_modulation;
extern char __code fsk2[];
extern char __code gfsk[];
extern char __code ask[];
extern char __code msk[];
extern char* __code modstrings[];


