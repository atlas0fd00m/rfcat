#ifndef _NIC_H_
#define _NIC_H_

#define APP_NIC                 0x42
#define NIC_RECV                0x1
#define NIC_XMIT                0x2

#define NIC_SET_ID              0x3
#define NIC_SET_RECV_LARGE      0x5

#define NIC_SET_AES_MODE        0x6
#define NIC_GET_AES_MODE        0x7
#define NIC_SET_AES_IV          0x8
#define NIC_SET_AES_KEY         0x9
#define NIC_SET_AMP_MODE        0xa
#define NIC_GET_AMP_MODE        0xb

#define NIC_LONG_XMIT           0xc
#define NIC_LONG_XMIT_MORE      0xd
#endif

