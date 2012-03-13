#define FHSS_SET_CHANNELS       0x10
#define FHSS_NEXT_CHANNEL       0x11
#define FHSS_CHANGE_CHANNEL     0x12
#define FHSS_SET_MAC_THRESHOLD  0x13
#define FHSS_GET_MAC_THRESHOLD  0x14
#define FHSS_SET_MAC_DATA       0x15
#define FHSS_GET_MAC_DATA       0x16
#define FHSS_XMIT               0x17

#define FHSS_SET_STATE          0x20
#define FHSS_GET_STATE          0x21
#define FHSS_START_SYNC         0x22
#define FHSS_START_HOPPING      0x23
#define FHSS_STOP_HOPPING       0x24


#define FHSS_STATE_NONHOPPING       0
#define FHSS_STATE_DISCOVERY        1
#define FHSS_STATE_SYNCHING         2
#define FHSS_LAST_NONHOPPING_STATE  FHSS_STATE_SYNCHING

#define FHSS_STATE_SYNCHED          3
#define FHSS_STATE_SYNC_MASTER      4
#define FHSS_STATE_SYNCINGMASTER    5


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
void MAC_tx(u8* message, u8 len);
void MAC_rx_handle(u8 len, u8* message);
u8 MAC_getNextChannel();


typedef struct MAC_DATA_s 
{
    u8 mac_state;
    // MAC parameters (FIXME: make this all cc1111fhssmac.c/h?)
    u32 MAC_threshold;              // when the T2 clock as overflowed this many times, change channel
    u16 NumChannels;                // in case of multiple paths through the available channels 
    u16 NumChannelHops;             // total number of channels in pattern (>= g_MaxChannels)
    u16 curChanIdx;                 // indicates current channel index of the hopping pattern
    u16 tLastStateChange;
    u16 tLastHop;
    u16 desperatelySeeking;
    u8  txMsgIdx;
    u8  txMsgIdxDone;
    u16 synched_chans;
} MAC_DATA_t;
