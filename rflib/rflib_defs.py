# firmware errors
LCE_NO_ERROR                            = 0x00
LCE_USB_EP5_TX_WHILE_INBUF_WRITTEN      = 0x01
LCE_USB_EP0_SENT_STALL                  = 0x04
LCE_USB_EP5_OUT_WHILE_OUTBUF_WRITTEN    = 0x05
LCE_USB_EP5_LEN_TOO_BIG                 = 0x06
LCE_USB_EP5_GOT_CRAP                    = 0x07
LCE_USB_EP5_STALL                       = 0x08
LCE_USB_DATA_LEFTOVER_FLAGS             = 0x09

LCE_RF_RXOVF                            = 0x10
LCE_RF_TXUNF                            = 0x11
LCE_DROPPED_PACKET                      = 0x12
LCE_RFTX_NEVER_TX                       = 0x13
LCE_RFTX_NEVER_LEAVE_TX                 = 0x14
LCE_RF_MODE_INCOMPAT                    = 0x15
LCE_RF_BLOCKSIZE_INCOMPAT               = 0x16
LCE_RF_MULTI_BUFFER_NOT_INIT            = 0x17
LCE_RF_MULTI_BUFFER_NOT_FREE            = 0x18

RC_NO_ERROR                             = 0x00
RC_TX_DROPPED_PACKET                    = 0xec
RC_TX_ERROR                             = 0xed
RC_RF_BLOCKSIZE_INCOMPAT                = 0xee
RC_RF_MODE_INCOMPAT                     = 0xef
RC_TEMP_ERR_BUFFER_NOT_AVAILABLE        = 0xfe # temporary error - retry!
RC_ERR_BUFFER_SIZE_EXCEEDED             = 0xff
RC_FAIL_TRANSMIT_LONG                   = 0xffff

# python client only errors
PY_NO_ERROR                             = 0x00
PY_TX_BLOCKSIZE_INCOMPAT                = 0xd0 # block > 255 bytes but with with repeat or offset specified
PY_TX_BLOCKSIZE_TOO_LARGE               = 0xda # block > 65535 (we could make this bigger by using a u32 for size)
