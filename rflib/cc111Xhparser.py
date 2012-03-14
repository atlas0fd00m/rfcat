#!/usr/bin/env python
"""
#include<compiler.h>
/* ------------------------------------------------------------------------------------------------
*                                        Interrupt Vectors
* ------------------------------------------------------------------------------------------------
*/
#define  RFTXRX_VECTOR  0    /*  RF TX done / RX ready                       */
#define  ADC_VECTOR     1    /*  ADC End of Conversion                       */
#define  URX0_VECTOR    2    /*  USART0 RX Complete                          */
#define  URX1_VECTOR    3    /*  USART1 RX Complete                          */
#define  ENC_VECTOR     4    /*  AES Encryption/Decryption Complete          */
#define  ST_VECTOR      5    /*  Sleep Timer Compare                         */
#define  P2INT_VECTOR   6    /*  Port 2 Inputs                               */
#define  UTX0_VECTOR    7    /*  USART0 TX Complete                          */
#define  DMA_VECTOR     8    /*  DMA Transfer Complete                       */
#define  T1_VECTOR      9    /*  Timer 1 (16-bit) Capture/Compare/Overflow   */
#define  T2_VECTOR      10   /*  Timer 2 (MAC Timer) Overflow                */
#define  T3_VECTOR      11   /*  Timer 3 (8-bit) Capture/Compare/Overflow    */
#define  T4_VECTOR      12   /*  Timer 4 (8-bit) Capture/Compare/Overflow    */
#define  P0INT_VECTOR   13   /*  Port 0 Inputs                               */
#define  UTX1_VECTOR    14   /*  USART1 TX Complete                          */
#define  P1INT_VECTOR   15   /*  Port 1 Inputs                               */
#define  RF_VECTOR      16   /*  RF General Interrupts                       */
#define  WDT_VECTOR     17   /*  Watchdog Overflow in Timer Mode             */

SFR(P0,       0x80); // Port 0
  SBIT(P0_0,     0x80, 0); // Port 0 bit 0
  SBIT(P0_1,     0x80, 1); // Port 0 bit 1
  SBIT(P0_2,     0x80, 2); // Port 0 bit 2
  SBIT(P0_3,     0x80, 3); // Port 0 bit 3
  SBIT(P0_4,     0x80, 4); // Port 0 bit 4
  SBIT(P0_5,     0x80, 5); // Port 0 bit 5
  SBIT(P0_6,     0x80, 6); // Port 0 bit 6
  SBIT(P0_7,     0x80, 7); // Port 0 bit 7

SFR(SP,       0x81); // Stack Pointer
SFR(DPL0,     0x82); // Data Pointer 0 Low Byte
SFR(DPH0,     0x83); // Data Pointer 0 High Byte
SFR(DPL1,     0x84); // Data Pointer 1 Low Byte
SFR(DPH1,     0x85); // Data Pointer 1 High Byte
"""
import sys


def parseLines(lines):
    defs = {}
    incomment = False
    for line in lines:
        # find single-line comments
        slc = line.find("//")
        if (slc > -1):
            line = line[:slc]         + "#" + line[slc+2:]
        # find /* */ comments
        mlcs = line.find("/*")
        mlce = line.find("*/")
        if (mlcs>-1):
            if (mlce>-1):           # both are in this line
                if (mlce>mlcs):     # they are "together"
                    if (mlce >= len(line.strip())-3):
                        line = line[:mlcs] + '#' + line[mlcs+2:mlce]
                    else:
                        line = line[:mlcs] + '"""' + line[mlcs+2:mlce] + '"""' + line[mlce+2:]
                else:               # they are *not* together
                    line = line[mlce+2:mlcs]
            else:                   # only the beginning is in this line, treat like a single-line comment for now
                line = line[:mlcs]
                incomment = True
        elif incomment:              # no mlc-starter found... are we incomment?  then ignore until the end of comment
            if (mlce>-1):
                line = line[mlce+2:]
                incomment = False
            else:
                line = ''
        if incomment:                # if we're still incomment, this whole line is comment
            continue

        # chop initial and trailing whitespace
        line = line.strip()

        # now we can actually parse the line
        if (line.startswith("#define ")):
            line = line[8:].strip()     # peel off any additional spaces after the #define
            pieces = line.split(" ", 1)
            if len(pieces)<2:
                continue
            name, value = pieces
            if "(" in name:
                print >>sys.stderr,("SKIPPING: %s"%(line))
                continue                # skip adding "function" defines
            defs[name.strip()] = value.strip()
            
        elif (line.startswith("SFR(")):
            endparen = line.find(")")
            if (endparen == -1):
                print >>sys.stderr,("ERROR: SFR without end parens: '%s'"%(line))
                continue
            line = line[4:endparen].strip()
            name, value = line.split(",", 1)
            defs[name.strip()] = value.strip()
        elif (line.startswith("SFRX(")):
            endparen = line.find(")")
            if (endparen == -1):
                print >>sys.stderr,("ERROR: SFRX without end parens: '%s'"%(line))
                continue
            line = line[5:endparen].strip()
            name, value = line.split(",", 1)
            defs[name.strip()] = value.strip()
        elif (line.startswith("SBIT")):
            endparen = line.find(")")
            if (endparen == -1):
                print >>sys.stderr,("ERROR: SBIT without end parens: '%s'"%(line))
                continue
            line = line[5:endparen].strip()
            name, val1, val2 = line.split(",", 2)
            defs[name.strip()] = 1 << (int(val2.strip()))

    return defs


if __name__ == '__main__':
    defs = {}
    defs.update(parseLines(file('../includes/cc1110-ext.h')))
    defs.update(parseLines(file('../includes/cc1111.h')))
    defs.update(parseLines(file('/usr/share/sdcc/include/mcs51/cc1110.h')))

    skeys = defs.keys()
    skeys.sort()
    out = ["%-30s = %s"%(key,defs[key]) for key in skeys]

    trueout = []
    for x in out: 
        try:
            compile(x,'stdin','exec')
            trueout.append(x)
            print(x)
        except:
            sys.excepthook(*sys.exc_info())


            






