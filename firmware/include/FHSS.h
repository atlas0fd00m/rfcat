#define FHSS_SET_CHANNELS       0x10
#define FHSS_NEXT_CHANNEL       0x11
#define FHSS_CHANGE_CHANNEL     0x12
#define FHSS_SET_MAC_THRESHOLD  0x13
#define FHSS_GET_MAC_THRESHOLD  0x14
#define FHSS_SET_MAC_DATA       0x15
#define FHSS_GET_MAC_DATA       0x16
#define FHSS_XMIT               0x17
#define FHSS_GET_CHANNELS       0x18

#define FHSS_SET_STATE          0x20
#define FHSS_GET_STATE          0x21
#define FHSS_START_SYNC         0x22
#define FHSS_START_HOPPING      0x23
#define FHSS_STOP_HOPPING       0x24
#define FHSS_SET_MAC_PERIOD     0x25

#define MAC_STATE_NONHOPPING        0
#define MAC_STATE_DISCOVERY         1
#define MAC_STATE_SYNCHING          2
#define MAC_LAST_NONHOPPING_STATE   MAC_STATE_SYNCHING

#define MAC_STATE_SYNCHED           3
#define MAC_STATE_SYNC_MASTER       4
#define MAC_STATE_SYNCINGMASTER     5


// spectrum analysis defines
// application and command
#define APP_SPECAN                  0x43
#define SPECAN_QUEUE                0x1

// FHSSNIC commands to start and stop SPECAN mode
#define RFCAT_START_SPECAN          0x40
#define RFCAT_STOP_SPECAN           0x41

// MAC_STATEs for SPECAN
#define MAC_STATE_PREP_SPECAN       0x40
#define MAC_STATE_SPECAN            0x41


// MAC layer defines
#define MAX_CHANNELS 880
#define MAX_TX_MSGS 5
#define MAX_TX_MSGLEN 41
#define MAX_SYNC_WAIT 10    //seconds... need to true up with T1/clock

#define MAC_TIMER_STATIC_DIFF   6
#define FHSS_TX_SLEEP_DELAY     25

#define DEFAULT_NUM_CHANS       83
#define DEFAULT_NUM_CHANHOPS    83

void begin_hopping(u8 T2_offset);
void stop_hopping(void);

void PHY_set_channel(u16 chan);
void MAC_initChannels();
void MAC_sync(u16 netID);
void MAC_set_chanidx(u16 chanidx);
void MAC_tx(__xdata u8* message, u8 len);
void MAC_rx_handle(u8 len, __xdata u8* message);
u8 MAC_getNextChannel();


typedef struct MAC_DATA_s 
{
    u8 mac_state;
    // MAC parameters (FIXME: make this all cc1111fhssmac.c/h?)
    u16 MAC_threshold;              // when the T2 clock as overflowed this many times, change channel
    u16 MAC_timer;                  // this tracks how many times it's overflowed (really?  32-bits for these two?!?)
    u16 NumChannels;                // in case of multiple paths through the available channels 
    u16 NumChannelHops;             // total number of channels in pattern (>= g_MaxChannels)
    u16 curChanIdx;                 // indicates current channel index of the hopping pattern
    u16 tLastStateChange;
    u16 tLastHop;
    u16 desperatelySeeking;         // this should be unnecessary, and should instead use mac_state?
    u8  txMsgIdx;
    u8  txMsgIdxDone;
    u16 synched_chans;
} MAC_DATA_t;
