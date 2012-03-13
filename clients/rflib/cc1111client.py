#!/usr/bin/env ipython
import sys, threading, time, struct, select
import usb

import bits
from chipcondefs import *


EP_TIMEOUT_IDLE     = 400
EP_TIMEOUT_ACTIVE   = 10


USB_BM_REQTYPE_TGTMASK          =0x1f
USB_BM_REQTYPE_TGT_DEV          =0x00
USB_BM_REQTYPE_TGT_INTF         =0x01
USB_BM_REQTYPE_TGT_EP           =0x02

USB_BM_REQTYPE_TYPEMASK         =0x60
USB_BM_REQTYPE_TYPE_STD         =0x00
USB_BM_REQTYPE_TYPE_CLASS       =0x20
USB_BM_REQTYPE_TYPE_VENDOR      =0x40
USB_BM_REQTYPE_TYPE_RESERVED    =0x60

USB_BM_REQTYPE_DIRMASK          =0x80
USB_BM_REQTYPE_DIR_OUT          =0x00
USB_BM_REQTYPE_DIR_IN           =0x80

USB_GET_STATUS                  =0x00
USB_CLEAR_FEATURE               =0x01
USB_SET_FEATURE                 =0x03
USB_SET_ADDRESS                 =0x05
USB_GET_DESCRIPTOR              =0x06
USB_SET_DESCRIPTOR              =0x07
USB_GET_CONFIGURATION           =0x08
USB_SET_CONFIGURATION           =0x09
USB_GET_INTERFACE               =0x0a
USB_SET_INTERFACE               =0x11
USB_SYNCH_FRAME                 =0x12

APP_GENERIC                     = 0x01
APP_DEBUG                       = 0xfe
APP_SYSTEM                      = 0xff


SYS_CMD_PEEK                    = 0x80
SYS_CMD_POKE                    = 0x81
SYS_CMD_PING                    = 0x82
SYS_CMD_STATUS                  = 0x83
SYS_CMD_POKE_REG                = 0x84
SYS_CMD_GET_CLOCK               = 0x85
SYS_CMD_BUILDTYPE               = 0x86
SYS_CMD_RESET                   = 0x8f

EP0_CMD_GET_DEBUG_CODES         = 0x00
EP0_CMD_GET_ADDRESS             = 0x01
EP0_CMD_POKEX                   = 0x01
EP0_CMD_PEEKX                   = 0x02
EP0_CMD_PING0                   = 0x03
EP0_CMD_PING1                   = 0x04
EP0_CMD_RESET                   = 0xfe


DEBUG_CMD_STRING                = 0xf0
DEBUG_CMD_HEX                   = 0xf1
DEBUG_CMD_HEX16                 = 0xf2
DEBUG_CMD_HEX32                 = 0xf3
DEBUG_CMD_INT                   = 0xf4

EP5OUT_MAX_PACKET_SIZE          = 64
EP5IN_MAX_PACKET_SIZE           = 64

SYNCM_NONE                      = 0
SYNCM_15_of_16                  = 1
SYNCM_16_of_16                  = 2
SYNCM_30_of_32                  = 3
SYNCM_CARRIER                   = 4
SYNCM_CARRIER_15_of_16          = 5
SYNCM_CARRIER_16_of_16          = 6
SYNCM_CARRIER_30_of_32          = 7

RF_STATE_RX                     = 1
RF_STATE_TX                     = 2
RF_STATE_IDLE                   = 3

RF_SUCCESS                      = 0

MODES = {}
lcls = locals()
for lcl in lcls.keys():
    if lcl.startswith("MARC_STATE_"):
        MODES[lcl] = lcls[lcl]
        MODES[lcls[lcl]] = lcl


"""  MODULATIONS
Note that MSK is only supported for data rates above 26 kBaud and GFSK,
ASK , and OOK is only supported for data rate up until 250 kBaud. MSK
cannot be used if Manchester encoding/decoding is enabled.
"""
MOD_2FSK                        = 0x00
MOD_GFSK                        = 0x10
MOD_ASK_OOK                     = 0x30
MOD_MSK                         = 0x70
MANCHESTER                      = 0x08

MODULATIONS = {
        MOD_2FSK    : "2FSK",
        MOD_GFSK    : "GFSK",
        MOD_ASK_OOK : "ASK/OOK",
        MOD_MSK     : "MSK",
        MOD_2FSK | MANCHESTER    : "2FSK/Manchester encoding",
        MOD_GFSK | MANCHESTER    : "GFSK/Manchester encoding",
        MOD_ASK_OOK | MANCHESTER : "ASK/OOK/Manchester encoding",
        MOD_MSK  | MANCHESTER    : "MSK/Manchester encoding",
        }

SYNCMODES = {
        SYNCM_NONE: "None",
        SYNCM_15_of_16: "15 of 16 bits must match",
        SYNCM_16_of_16: "16 of 16 bits must match",
        SYNCM_30_of_32: "30 of 32 sync bits must match",
        SYNCM_CARRIER: "Carrier Detect",
        SYNCM_CARRIER_15_of_16: "Carrier Detect and 15 of 16 sync bits must match",
        SYNCM_CARRIER_16_of_16: "Carrier Detect and 16 of 16 sync bits must match",
        SYNCM_CARRIER_30_of_32: "Carrier Detect and 30 of 32 sync bits must match",
        }

NUM_PREAMBLE = [2, 3, 4, 6, 8, 12, 16, 24 ]

ADR_CHK_TYPES = [
        "No address check",
        "Address Check, No Broadcast",
        "Address Check, 0x00 is broadcast",
        "Address Check, 0x00 and 0xff are broadcast",
        ]



PKT_FORMATS = [
        "Normal mode",
        "reserved...",
        "Random TX mode",
        "reserved",
        ]

LENGTH_CONFIGS = [
        "Fixed Packet Mode",
        "Variable Packet Mode (len=first byte after sync word)",
        "reserved",
        "reserved",
        ]
LC_USB_INITUSB                = 0x2
LC_MAIN_RFIF                  = 0xd
LC_USB_DATA_RESET_RESUME      = 0xa
LC_USB_RESET                  = 0xb
LC_USB_EP5OUT                 = 0xc
LC_RF_VECTOR                  = 0x10
LC_RFTXRX_VECTOR              = 0x11

LCE_USB_EP5_TX_WHILE_INBUF_WRITTEN    = 0x1
LCE_USB_EP0_SENT_STALL                = 0x4
LCE_USB_EP5_OUT_WHILE_OUTBUF_WRITTEN  = 0x5
LCE_USB_EP5_LEN_TOO_BIG               = 0x6
LCE_USB_EP5_GOT_CRAP                  = 0x7
LCE_USB_EP5_STALL                     = 0x8
LCE_USB_DATA_LEFTOVER_FLAGS           = 0x9
LCE_RF_RXOVF                          = 0x10
LCE_RF_TXUNF                          = 0x11

LCS = {}
LCES = {}
lcls = locals()
for lcl in lcls.keys():
    if lcl.startswith("LCE_"):
        LCES[lcl] = lcls[lcl]
        LCES[lcls[lcl]] = lcl
    if lcl.startswith("LC_"):
        LCS[lcl] = lcls[lcl]
        LCS[lcls[lcl]] = lcl

class CC111xTimeoutException(Exception):
    def __str__(self):
        return "Timeout waiting for USB response."

direct=False

class USBDongle:
    ######## INITIALIZATION ########
    def __init__(self, idx=0, debug=False):
        self.rsema = None
        self.xsema = None
        self._do = None
        self.idx = idx
        self.cleanup()
        self._debug = debug
        self._threadGo = False
        self._recv_time = 0
        self.radiocfg = RadioConfig()
        self.recv_thread = threading.Thread(target=self.runEP5)
        self.recv_thread.setDaemon(True)
        self.recv_thread.start()
        self.resetup()

    def cleanup(self):
        self._usberrorcnt = 0;
        self.recv_queue = ''
        self.recv_mbox  = {}
        self.xmit_queue = []
        self.trash = []
    
    def setup(self, console=True):
        global dongles

        dongles = []
        self.ep5timeout = EP_TIMEOUT_ACTIVE

        for bus in usb.busses():
            for dev in bus.devices:
                if dev.idProduct == 0x4715:
                    if console: print >>sys.stderr,(dev)
                    do = dev.open()
                    iSN = do.getDescriptor(1,0,50)[16]
                    devnum = dev.devnum
                    dongles.append((devnum, dev, do))

        dongles.sort()
        if len(dongles) == 0:
            raise(Exception("No Dongle Found.  Please insert a RFCAT dongle."))

        self.rsema = threading.Lock()
        self.xsema = threading.Lock()

        # claim that interface!
        do = dongles[self.idx][2]
        
        try:
            do.claimInterface(0)
        except Exception,e:
            if console or self._debug: print >>sys.stderr,("Error claiming usb interface:" + repr(e))



        self.devnum, self._d, self._do = dongles[self.idx]
        self._usbmaxi, self._usbmaxo = (EP5IN_MAX_PACKET_SIZE, EP5OUT_MAX_PACKET_SIZE)
        self._usbcfg = self._d.configurations[0]
        self._usbintf = self._usbcfg.interfaces[0][0]
        self._usbeps = self._usbintf.endpoints
        for ep in self._usbeps:
            if ep.address & 0x80:
                self._usbmaxi = ep.maxPacketSize
            else:
                self._usbmaxo = ep.maxPacketSize

        self._threadGo = True

    def resetup(self, console=True):
        self._do=None
        #self._threadGo = True
        if console or self._debug: print >>sys.stderr,("waiting (resetup) %x" % self.idx)
        while (self._do==None):
            try:
                self.setup(console)
                self._clear_buffers(False)

            except Exception, e:
                if console: sys.stderr.write('.')
                if console or self._debug: print >>sys.stderr,("Error in resetup():" + repr(e))
                time.sleep(1)



    ########  BASE FOUNDATIONAL "HIDDEN" CALLS ########
    def _sendEP0(self, request=0, buf=None, value=0x200, index=0, timeout=1000):
        if buf == None:
            buf = 'HELLO THERE'
        #return self._do.controlMsg(USB_BM_REQTYPE_TGT_EP|USB_BM_REQTYPE_TYPE_VENDOR|USB_BM_REQTYPE_DIR_OUT, request, "\x00\x00\x00\x00\x00\x00\x00\x00"+buf, value, index, timeout), buf
        return self._do.controlMsg(USB_BM_REQTYPE_TGT_EP|USB_BM_REQTYPE_TYPE_VENDOR|USB_BM_REQTYPE_DIR_OUT, request, buf, value, index, timeout), buf

    def _recvEP0(self, request=0, length=64, value=0, index=0, timeout=100):
        retary = ["%c"%x for x in self._do.controlMsg(USB_BM_REQTYPE_TGT_EP|USB_BM_REQTYPE_TYPE_VENDOR|USB_BM_REQTYPE_DIR_IN, request, length, value, index, timeout)]
        if len(retary):
            return ''.join(retary)
        return ""

    def _sendEP5(self, buf=None, timeout=1000):
        global direct
        if (buf==None):
            buf = "\xff\x82\x07\x00ABCDEFG"
        if direct:
            self._do.bulkWrite(5, buf, timeout)
            return

        while (len(buf)>0):
            drain = buf[:self._usbmaxo]
            buf = buf[self._usbmaxo:]

            if self._debug: print >>sys.stderr,"XMIT:"+repr(drain)
            try:
                self._do.bulkWrite(5, drain, timeout)
            except Exception, e:
                if self._debug: print >>sys.stderr,"requeuing on error '%s' (%s)" % (repr(drain), e)
                self.xsema.acquire()
                msg = self.xmit_queue.insert(0, drain)
                self.xsema.release()
                if self._debug: print >>sys.stderr, repr(self.xmit_queue)
        '''
        drain = buf[:self._usbmaxo]
        buf = buf[self._usbmaxo:]
        if len(buf):
            if self._debug: print >>sys.stderr,"requeuing '%s'" % repr(buf)
            self.xsema.acquire()
            msg = self.xmit_queue.insert(0, buf)
            self.xsema.release()
            if self._debug: print >>sys.stderr, repr(self.xmit_queue)
        if self._debug: print >>sys.stderr,"XMIT:"+repr(drain)
        try:
            self._do.bulkWrite(5, drain, timeout)
        except Exception, e:
            if self._debug: print >>sys.stderr,"requeuing on error '%s' (%s)" % (repr(drain), e)
            self.xsema.acquire()
            msg = self.xmit_queue.insert(0, drain)
            self.xsema.release()
            if self._debug: print >>sys.stderr, repr(self.xmit_queue)

        ---
        while (len(buf)>0):
            drain = buf[:self._usbmaxo]
            buf = buf[self._usbmaxo:]

            if self._debug: print >>sys.stderr,"XMIT:"+repr(drain)
            self._do.bulkWrite(5, drain, timeout)
            time.sleep(1)
        ---
        if (len(buf) > self._usbmaxo):
            drain = buf[:self._usbmaxo]
            buf = buf[self._usbmaxo:]
            self.xsema.acquire()
            msg = self.xmit_queue.insert(0, buf)
            self.xsema.release()
        else:
            drain = buf[:]
        if self._debug: print >>sys.stderr,"XMIT:"+repr(drain)
        self._do.bulkWrite(5, drain, timeout)
        ---
        while (len(buf)>0):
            if (len(buf) > self._usbmaxo):
                drain = buf[:self._usbmaxo]
                buf = buf[self._usbmaxo:]
            else:
                drain = buf[:]
            if self._debug: print >>sys.stderr,"XMIT:"+repr(drain)
            self._do.bulkWrite(5, drain, timeout)
            time.sleep(1)
        '''
        
    def _recvEP5(self, timeout=100):
        retary = ["%c"%x for x in self._do.bulkRead(0x85, 500, timeout)]
        if self._debug: print >>sys.stderr,"RECV:"+repr(retary)
        if len(retary):
            return ''.join(retary)
            #return retary
        return ''

    def _clear_buffers(self, clear_recv_mbox=False):
        threadGo = self._threadGo
        self._threadGo = False
        if self._debug:
            print >>sys.stderr,("_clear_buffers()")
        if clear_recv_mbox:
            for key in self.recv_mbox.keys():
                self.trash.extend(self.recvAll(key))
        self.trash.append((time.time(),self.recv_queue))
        self.recv_queue = ''
        # self.xmit_queue = []          # do we want to keep this?
        self._threadGo = threadGo


    ######## TRANSMIT/RECEIVE THREADING ########
    def runEP5(self):
        msg = ''
        self.threadcounter = 0

        while True:
            if (self._do is None or not self._threadGo): 
                time.sleep(.04)
                continue

            self.threadcounter = (self.threadcounter + 1) & 0xffffffff

            #### transmit stuff.  if any exists in the xmit_queue
            msgsent = False
            msgrecv = False
            try:
                if len(self.xmit_queue):
                    self.xsema.acquire()
                    msg = self.xmit_queue.pop(0)
                    self.xsema.release()
                    self._sendEP5(msg)
                    msgsent = True
                else:
                    if self._debug>3: sys.stderr.write("NoMsgToSend ")
            #except IndexError:
                #if self._debug==3: sys.stderr.write("NoMsgToSend ")
                #pass
            except:
                sys.excepthook(*sys.exc_info())


            #### handle debug application
            try:
                q = None
                b = self.recv_mbox.get(APP_DEBUG, None)
                if (b != None):
                    for cmd in b.keys():
                        q = b[cmd]
                        if len(q):
                            buf,timestamp = q.pop(0)
                            #cmd = ord(buf[1])
                            if self._debug > 1: print >>sys.stderr,("buf length: %x\t\t cmd: %x\t\t(%s)"%(len(buf), cmd, repr(buf)))
                            if (cmd == DEBUG_CMD_STRING):
                                if (len(buf) < 4):
                                    if (len(q)):
                                        buf2 = q.pop(0)
                                        buf += buf2
                                    q.insert(0,buf)
                                    if self._debug: sys.stderr.write('*')
                                else:
                                    length, = struct.unpack("<H", buf[2:4])
                                    if self._debug >1: print >>sys.stderr,("len=%d"%length)
                                    if (len(buf) < 4+length):
                                        if (len(q)):
                                            buf2 = q.pop(0)
                                            buf += buf2
                                        q.insert(0,buf)
                                        if self._debug: sys.stderr.write('&')
                                    else:
                                        printbuf = buf[4:4+length]
                                        requeuebuf = buf[4+length:]
                                        if len(requeuebuf):
                                            if self._debug>1:  print >>sys.stderr,(" - DEBUG..requeuing %s"%repr(requeuebuf))
                                            q.insert(0,requeuebuf)
                                        print >>sys.stderr,("DEBUG: (%.3f) %s" % (timestamp, repr(printbuf)))
                            elif (cmd == DEBUG_CMD_HEX):
                                #print >>sys.stderr, repr(buf)
                                print >>sys.stderr, "DEBUG: (%.3f) %x"%(timestamp, struct.unpack("B", buf[4:5])[0])
                            elif (cmd == DEBUG_CMD_HEX16):
                                #print >>sys.stderr, repr(buf)
                                print >>sys.stderr, "DEBUG: (%.3f) %x"%(timestamp, struct.unpack("<H", buf[4:6])[0])
                            elif (cmd == DEBUG_CMD_HEX32):
                                #print >>sys.stderr, repr(buf)
                                print >>sys.stderr, "DEBUG: (%.3f) %x"%(timestamp, struct.unpack("<L", buf[4:8])[0])
                            elif (cmd == DEBUG_CMD_INT):
                                print >>sys.stderr, "DEBUG: (%.3f) %d"%(timestamp, struct.unpack("<L", buf[4:8])[0])
                            else:
                                print >>sys.stderr,('DEBUG COMMAND UNKNOWN: %x (buf=%s)'%(cmd,repr(buf)))

            except:
                sys.excepthook(*sys.exc_info())

            #### receive stuff.
            try:
                #### first we populate the queue
                msg = self._recvEP5(timeout=self.ep5timeout)
                if len(msg) > 0:
                    self.recv_queue += msg
                    msgrecv = True
            except usb.USBError, e:
                #sys.stderr.write(repr(self.recv_queue))
                #sys.stderr.write(repr(e))
                errstr = repr(e)
                if self._debug>4: print >>sys.stderr,repr(sys.exc_info())
                if ('No error' in errstr):
                    pass
                elif ('Operation timed out' in errstr):
                    pass
                else:
                    if ('could not release intf' in errstr):
                        pass
                    elif ('No such device' in errstr):
                        self._threadGo = False
                        self.resetup(False)
                    else:
                        if self._debug: print "Error in runEP5() (receiving): %s" % errstr
                        if self._debug>2: sys.excepthook(*sys.exc_info())
                    self._usberrorcnt += 1
                pass


            #### parse, sort, and deliver the mail.
            try:
                # FIXME: is this robust?  or just overcomplex?
                if len(self.recv_queue):
                    idx = self.recv_queue.find('@')
                    if (idx==-1):
                        if self._debug > 3:
                            sys.stderr.write('@')
                    else:
                        if (idx>0):
                            if self._debug: print >>sys.stderr,("runEP5(): idx>0?")
                            self.trash.append(self.recv_queue[:idx])
                            self.recv_queue = self.recv_queue[idx:]
                   
                        # recv_queue is vulnerable here, but it's ok because we only modify it earlier in this same thread
                        # DON'T CHANGE recv_queue from other threads!
                        msg = self.recv_queue
                        msglen = len(msg)
                        while (msglen>=5):                                      # if not enough to parse length... we'll wait.
                            if not self._recv_time:                             # should be 0 to start and when done with a packet
                                self._recv_time = time.time()
                            app = ord(msg[1])
                            cmd = ord(msg[2])
                            length, = struct.unpack("<H", msg[3:5])

                            if self._debug>1: print>>sys.stderr,("app=%x  cmd=%x  len=%x"%(app,cmd,length))

                            if (msglen >= length+5):
                                #### if the queue has enough characters to handle the next message... chop it and put it in the appropriate recv_mbox
                                msg = self.recv_queue[1:length+5]                   # drop the initial '@' and chop out the right number of chars
                                self.recv_queue = self.recv_queue[length+5:]        # chop it out of the queue

                                b = self.recv_mbox.get(app,None)
                                if self.rsema.acquire():                            # THREAD SAFETY DANCE
                                    #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],0
                                    try:
                                        if (b == None):
                                            b = {}
                                            self.recv_mbox[app] = b
                                    except:
                                        sys.excepthook(*sys.exc_info())
                                    finally:
                                        self.rsema.release()                            # THREAD SAFETY DANCE COMPLETE
                                        #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],0
                               
                                q = b.get(cmd)
                                if self.rsema.acquire():                            # THREAD SAFETY DANCE
                                    #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],1
                                    try:
                                        if (q is None):
                                            q = []
                                            b[cmd] = q

                                        q.append((msg, self._recv_time))
                                        self._recv_time = 0                         # we've delivered the current message
                                    except:
                                        sys.excepthook(*sys.exc_info())
                                    finally:
                                        self.rsema.release()                            # THREAD SAFETY DANCE COMPLETE
                                        #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],1
                               
                            else:            
                                if self._debug>1:     sys.stderr.write('=')

                            msg = self.recv_queue
                            msglen = len(msg)
                            # end of while loop
                        #else:
                        #    if self._debug:     sys.stderr.write('.')
            except:
                sys.excepthook(*sys.exc_info())


            if not (msgsent or msgrecv or len(msg)) :
                #time.sleep(.1)
                self.ep5timeout = EP_TIMEOUT_IDLE
            else:
                self.ep5timeout = EP_TIMEOUT_ACTIVE
                if self._debug > 5:  sys.stderr.write(" %s:%s:%d .-P."%(msgsent,msgrecv,len(msg)))


                




    ######## APPLICATION API ########
    def recv(self, app, cmd=None, wait=100):
        for x in xrange(wait+1):
            try:
                b = self.recv_mbox.get(app)
                if cmd is None:
                    keys = b.keys()
                    if len(keys):
                        cmd = b.keys()[-1]
                if b is not None:
                    q = b.get(cmd)
                    #print >>sys.stderr,"debug(recv) q='%s'"%repr(q)
                    if q is not None and self.rsema.acquire(False):
                        #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],2
                        try:
                            resp, rt = q.pop(0)
                            self.rsema.release()
                            #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],2
                            return resp[4:], rt
                        except IndexError:
                            pass
                            #sys.excepthook(*sys.exc_info())
                        except AttributeError:
                            sys.excepthook(*sys.exc_info())
                            pass
                        self.rsema.release()
                        #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],2
            except:
                sys.excepthook(*sys.exc_info())

            time.sleep(.001)                                      # only hits here if we don't have something in queue
            
        raise(CC111xTimeoutException())

    def recvAll(self, app, cmd=None):
        retval = self.recv_mbox.get(app,None)
        if retval is not None:
            if cmd is not None:
                b = retval
                if self.rsema.acquire():
                    #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],3
                    try:
                        retval = b.get(cmd)
                        b[cmd]=[]
                        if len(retval):
                            retval = [ (d[4:],t) for d,t in retval ] 
                    except:
                        sys.excepthook(*sys.exc_info())
                    finally:
                        self.rsema.release()
                        #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],3
            else:
                if self.rsema.acquire():
                    #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],4
                    try:
                        self.recv_mbox[app]={}
                    finally:
                        self.rsema.release()
                        #if self._debug: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],4
            return retval

    def send(self, app, cmd, buf, wait=10000):
        msg = "%c%c%s%s"%(app,cmd, struct.pack("<H",len(buf)),buf)
        self.xsema.acquire()
        self.xmit_queue.append(msg)
        self.xsema.release()
        return self.recv(app, cmd, wait)

    def getDebugCodes(self, timeout=100):
        x = self._recvEP0(timeout=timeout)
        if (x != None and len(x)==2):
            return struct.unpack("BB", x)
        else:
            return x

    def ep0GetAddr(self):
        addr = self._recvEP0(request=EP0_CMD_GET_ADDRESS)
        return addr
    def ep0Reset(self):
        x = self._recvEP0(request=0xfe, value=0x5352, index=0x4e54)
        return x

    def ep0Peek(self, addr, length, timeout=100):
        x = self._recvEP0(request=EP0_CMD_PEEKX, value=addr, length=length, timeout=timeout)
        return x#x[3:]

    def ep0Poke(self, addr, buf='\x00', timeout=100):
        x = self._sendEP0(request=EP0_CMD_POKEX, buf=buf, value=addr, timeout=timeout)
        return x

    def ep0Ping(self, count=10):
        good=0
        bad=0
        for x in range(count):
            #r = self._recvEP0(3, 10)
            r = self._recvEP0(request=2, value=count, length=count, timeout=1000)
            print "PING: %d bytes received: %s"%(len(r), repr(r))
            if r==None:
                bad+=1
            else:
                good+=1
        return (good,bad)

    def debug(self):
        while True:
            """
            try:
                print >>sys.stderr, ("DONGLE RESPONDING:  mode :%x, last error# %d"%(self.getDebugCodes()))
            except:
                pass
            print >>sys.stderr,('recv_queue:\t\t (%d bytes) "%s"'%(len(self.recv_queue),repr(self.recv_queue)[:len(self.recv_queue)%39+20]))
            print >>sys.stderr,('trash:     \t\t (%d bytes) "%s"'%(len(self.trash),repr(self.trash)[:len(self.trash)%39+20]))
            print >>sys.stderr,('recv_mbox  \t\t (%d keys)  "%s"'%(len(self.recv_mbox),repr(self.recv_mbox)[:len(repr(self.recv_mbox))%79]))
            for x in self.recv_mbox.keys():
                print >>sys.stderr,('    recv_mbox   %d\t (%d records)  "%s"'%(x,len(self.recv_mbox[x]),repr(self.recv_mbox[x])[:len(repr(self.recv_mbox[x]))%79]))
                """
            print self.reprRadioState()
            print self.reprClientState()

            x,y,z = select.select([sys.stdin],[],[],1)
            if sys.stdin in x:
                sys.stdin.read(1)
                break

    def ping(self, count=10, buf="ABCDEFGHIJKLMNOPQRSTUVWXYZ", wait=1000):
        good=0
        bad=0
        start = time.time()
        for x in range(count):
            istart = time.time()
            
            try:
                r = self.send(APP_SYSTEM, SYS_CMD_PING, buf, wait)
            except CC111xTimeoutException, e:
                r = None
                pass #print e
            r,rt = r
            istop = time.time()
            print "PING: %d bytes transmitted, received: %s (%f seconds)"%(len(buf), repr(r), istop-istart)
            if r==None:
                bad+=1
            else:
                good+=1
        stop = time.time()
        return (good,bad,stop-start)

    def RESET(self):
        try:
            r = self.send(APP_SYSTEM, SYS_CMD_RESET, "RESET_NOW\x00")
        except CC111xTimeoutException:
            pass
        
    def peek(self, addr, bytecount=1):
        r, t = self.send(APP_SYSTEM, SYS_CMD_PEEK, struct.pack("<HH", bytecount, addr))
        return r

    def poke(self, addr, data):
        r, t = self.send(APP_SYSTEM, SYS_CMD_POKE, struct.pack("<H", addr) + data)
        return r
    
    def pokeReg(self, addr, data):
        r, t = self.send(APP_SYSTEM, SYS_CMD_POKE_REG, struct.pack("<H", addr) + data)
        return r

    def getBuildInfo(self):
        r, t = self.send(APP_SYSTEM, SYS_CMD_BUILDTYPE, '')
        return r
            
    def getInterruptRegisters(self):
        regs = {}
        # IEN0,1,2
        regs['IEN0'] = self.peek(IEN0,1)
        regs['IEN1'] = self.peek(IEN1,1)
        regs['IEN2'] = self.peek(IEN2,1)
        # TCON
        regs['TCON'] = self.peek(TCON,1)
        # S0CON
        regs['S0CON'] = self.peek(S0CON,1)
        # IRCON
        regs['IRCON'] = self.peek(IRCON,1)
        # IRCON2
        regs['IRCON2'] = self.peek(IRCON2,1)
        # S1CON
        regs['S1CON'] = self.peek(S1CON,1)
        # RFIF
        regs['RFIF'] = self.peek(RFIF,1)
        # DMAIE
        regs['DMAIE'] = self.peek(DMAIE,1)
        # DMAIF
        regs['DMAIF'] = self.peek(DMAIF,1)
        # DMAIRQ
        regs['DMAIRQ'] = self.peek(DMAIRQ,1)
        return regs

    ######## RADIO METHODS #########
    ### radio recv
    def getMARCSTATE(self, radiocfg=None):
        if radiocfg is None:
            self.getRadioConfig()
            radiocfg=self.radiocfg

        mode = self.radiocfg.marcstate
        return (MODES[mode], mode)

    def setModeTX(self):
        self.poke(X_RFST, "%c"%RFST_STX)

    def setModeRX(self):
        self.poke(X_RFST, "%c"%RFST_SRX)

    def setModeIDLE(self):
        self.poke(X_RFST, "%c"%RFST_SIDLE)

    def setModeFSTXON(self):
        self.poke(X_RFST, "%c"%RFST_SFSTXON)

    def setModeCAL(self):
        self.poke(X_RFST, "%c"%RFST_SCAL)


    def setRFRegister(self, regaddr, value):
        marcstate = self.radiocfg.marcstate

        self.setModeIDLE()
        self.poke(regaddr, chr(value))
        if (marcstate == MARC_STATE_RX):
            self.setModeRX()
        elif (marcstate == MARC_STATE_TX):
            self.setModeTX()
        # if other than these, we can stay in IDLE

    ### radio config
    def getRadioConfig(self):
        bytedef = self.peek(0xdf00, 0x3e)
        self.radiocfg.vsParse(bytedef)
        return bytedef

    def setRadioConfig(self, bytedef = None):
        if bytedef is None:
            bytedef = self.radiocfg.vsEmit()

        statestr, marcstate = self.getMARCSTATE()
        self.setModeIDLE()

        self.poke(0xdf00, bytedef)

        if (marcstate == MARC_STATE_RX):
            self.setModeRX()
        elif (marcstate == MARC_STATE_TX):
            self.setModeTX()

        return bytedef

    def setFreq(self, freq=902000000, mhz=24, radiocfg=None):
        freqmult = (0x10000 / 1000000.0) / mhz
        num = int(freq * freqmult)
        self.radiocfg.freq2 = num >> 16
        self.radiocfg.freq1 = (num>>8) & 0xff
        self.radiocfg.freq0 = num & 0xff
        self.setModeIDLE()
        self.poke(FREQ2, struct.pack("3B", self.radiocfg.freq2, self.radiocfg.freq1, self.radiocfg.freq0))
        self.setModeRX()

    def getFreq(self, mhz=24, radiocfg=None):
        freqmult = (0x10000 / 1000000.0) / mhz
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
            
        num = (self.radiocfg.freq2<<16) + (self.radiocfg.freq1<<8) + self.radiocfg.freq0
        freq = num / freqmult
        return freq, hex(num)

    def setMdmModulation(self, mod, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        if (mod) & 0x8f:
            raise(Exception("Please use constants MOD_FORMAT_* to specify modulation and "))

        radiocfg.mdmcfg2 &= 0x8f
        radiocfg.mdmcfg2 |= (mod)
        self.setRFRegister(MDMCFG2, radiocfg.mdmcfg2)

    def getMdmModulation(self, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
        
        mdmcfg2 = radiocfg.mdmcfg2
        mod = (mdmcfg2) & 0x70
        return mod

    def reprRadioConfig(self, mhz=24, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        output = []

        output.append( "Frequency Configuration")
        output.append( self.reprFreqConfig(mhz, radiocfg))
        output.append( "\nModem Configuration")
        output.append( self.reprModemConfig(mhz, radiocfg))
        output.append( "\nPacket Configuration")
        output.append( self.reprPacketConfig(radiocfg))
        output.append( "\nRadio Test Signal Configuration")
        output.append( self.reprRadioTestSignalConfig(radiocfg))
        output.append( "\nRadio State")
        output.append( self.reprRadioState(radiocfg))
        output.append("\nClient State")
        output.append( self.reprClientState())
        return "\n".join(output)


    def reprMdmModulation(self, radiocfg=None):
        mod = self.getMdmModulation(radiocfg)
        return ("Modulation:           %s" % MODULATIONS[mod])

    def getMdmChanSpc(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        chanspc_m = radiocfg.mdmcfg0
        chanspc_e = radiocfg.mdmcfg1 & 3
        chanspc = 1000000.0 * mhz/pow(2,18) * (256 + chanspc_m) * pow(2, chanspc_e)
        print "chanspc_e: %x   chanspc_m: %x   chanspc: %f hz" % (chanspc_e, chanspc_m, chanspc)
        return (chanspc)

    def setMdmChanSpc(self, chanspc=None, chanspc_m=None, chanspc_e=None, mhz=24, radiocfg=None):
        '''
        calculates the appropriate exponent and mantissa and updates the correct registers
        chanspc is in kHz.  if you prefer, you may set the chanspc_m and chanspc_e settings 
        directly.

        only use one or the other:
        * chanspc
        * chanspc_m and chanspc_e
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        if (chanspc != None):
            for e in range(4):
                m = int(((chanspc * pow(2,18) / (1000000.0 * mhz * pow(2,e)))-256) +.5)    # rounded evenly
                if m < 256:
                    chanspc_e = e
                    chanspc_m = m
                    break
        if chanspc_e is None or chanspc_m is None:
            raise(Exception("ChanSpc does not translate into acceptable parameters.  Should you be changing this?"))

        #chanspc = 1000000.0 * mhz/pow(2,18) * (256 + chanspc_m) * pow(2, chanspc_e)
        #print "chanspc_e: %x   chanspc_m: %x   chanspc: %f hz" % (chanspc_e, chanspc_m, chanspc)
        
        radiocfg.mdmcfg1 &= 0xfc            # clear out old exponent value
        radiocfg.mdmcfg1 |= chanspc_e
        radiocfg.mdmcfg0 = chanspc_m
        self.setRFRegister(MDMCFG1, (radiocfg.mdmcfg1))
        self.setRFRegister(MDMCFG0, (radiocfg.mdmcfg0))

    def makePktVLEN(self, maxlen=0xff, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        self.radiocfg.pktctrl0 &= 0xfc
        self.radiocfg.pktctrl0 |= 1
        self.radiocfg.pktlen = maxlen
        self.setRFRegister(PKTCTRL0, (self.radiocfg.pktctrl0))
        self.setRFRegister(PKTLEN, (self.radiocfg.pktlen))

    def makePktFLEN(self, flen=0xff, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        self.radiocfg.pktctrl0 &= 0xfc
        self.radiocfg.pktlen = flen
        self.setRFRegister(PKTCTRL0, (self.radiocfg.pktctrl0))
        self.setRFRegister(PKTLEN, (self.radiocfg.pktlen))

    def setEnablePktCRC(self, enable=True, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        crcE = (0,1)[enable]<<2
        crcM = ~(1<<2)
        self.radiocfg.pktctrl0 &= crcM
        self.radiocfg.pktctrl0 |= crcE
        self.setRFRegister(PKTCTRL0, (self.radiocfg.pktctrl0))

    def getEnablePktCRC(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        return (radiocfg.pktctrl0 >>2) & 0x1

    def setEnablePktDataWhitening(self, enable=True, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        dwEnable = (0,1)[enable]<<6
        dwMask = ~(1<<6)
        self.radiocfg.pktctrl0 &= dwMask
        self.radiocfg.pktctrl0 |= dwEnable
        self.setRFRegister(PKTCTRL0, (self.radiocfg.pktctrl0))

    def getEnablePktDataWhitening(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        return (radiocfg.pktctrl0 >>6) & 0x1

    def setPktPQT(self, num=3, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        num &=  7
        num <<= 5
        numM = ~(7<<5)
        radiocfg.pktctrl1 &= numM
        radiocfg.pktctrl1 |= num
        self.setRFRegister(PKTCTRL1, (radiocfg.pktctrl1))

    def getPktPQT(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        return (radiocfg.pktctrl1 >> 5) & 7

    def setEnableMdmManchester(self, enable=True, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        radiocfg.mdmcfg2 &= 0xf7
        radiocfg.mdmcfg2 |= (enable<<3)
        self.setRFRegister(MDMCFG2, radiocfg.mdmcfg2)

    def getEnableMdmManchester(self, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        mdmcfg2 = radiocfg.mdmcfg2
        mchstr = (mdmcfg2>>3) & 0x01
        return mchstr

    def setEnableMdmFEC(self, enable=True, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        fecEnable = (0,1)[enable]<<7
        fecMask = ~(1<<7)
        self.radiocfg.mdmcfg1 &= fecMask
        self.radiocfg.mdmcfg1 |= fecEnable
        self.setRFRegister(MDMCFG1, (self.radiocfg.mdmcfg1))

    def getEnableMdmFEC(self, radiocfg=None):
        if radiocfg == None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        mdmcfg1 = radiocfg.mdmcfg1
        fecEnable = (mdmcfg1>>7) & 0x01
        return fecEnable

    def setEnableMdmDCFilter(self, enable=True, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        dcfEnable = (0,1)[enable]<<7
        dcfMask = ~(1<<7)
        radiocfg.mdmcfg2 &= dcfMask
        radiocfg.mdmcfg2 |= dcfEnable
        self.setRFRegister(MDMCFG2, radiocfg.mdmcfg2)

    def getEnableMdmDCFilter(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        dcfEnable = (radiocfg.mdmcfg2>>7) & 0x1
        return dcfEnable


    def setFsIF(self, freq_if, mhz=24, radiocfg=None):
        '''
        Note that the SmartRF Studio software
        automatically calculates the optimum register
        setting based on channel spacing and channel
        filter bandwidth. (from cc1110f32.pdf)
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        ifBits = freq_if * pow(2,10) / (1000000.0 * mhz)
        ifBits = int(ifBits + .5)       # rounded evenly

        if ifBits >0x1f:
            raise(Exception("FAIL:  freq_if is too high?  freqbits: %x (must be <0x1f)" % ifBits))
        self.radiocfg.fsctrl1 &= ~(0x1f)
        self.radiocfg.fsctrl1 |= int(ifBits)
        self.setRFRegister(FSCTRL1, (self.radiocfg.fsctrl1))

    def getFsIF(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        freq_if = (radiocfg.fsctrl1&0x1f) * (1000000.0 * mhz / pow(2,10))
        return freq_if


    def setFsOffset(self, if_off, mhz=24, radiocfg=None):
        '''
        Note that the SmartRF Studio software
        automatically calculates the optimum register
        setting based on channel spacing and channel
        filter bandwidth. (from cc1110f32.pdf)
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        self.radiocfg.fsctrl0 = if_off
        self.setRFRegister(FSCTRL0, (self.radiocfg.fsctrl0))

    def getFsOffset(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        freqoff = radiocfg.fsctrl0
        return freqoff

    def getChannel(self):
        self.getRadioConfig()
        return self.radiocfg.channr

    def setChannel(self, channr):
        self.radiocfg.channr = channr
        self.setRFRegister(CHANNR, (self.radiocfg.channr))

    def setMdmChanBW(self, bw, mhz=24, radiocfg=None):
        '''
        For best performance, the channel filter
        bandwidth should be selected so that the
        signal bandwidth occupies at most 80% of the
        channel filter bandwidth. The channel centre
        tolerance due to crystal accuracy should also
        be subtracted from the signal bandwidth. The
        following example illustrates this:

            With the channel filter bandwidth set to 500
            kHz, the signal should stay within 80% of 500
            kHz, which is 400 kHz. Assuming 915 MHz
            frequency and +/-20 ppm frequency uncertainty
            for both the transmitting device and the
            receiving device, the total frequency
            uncertainty is +/-40 ppm of 915 MHz, which is
            +/-37 kHz. If the whole transmitted signal
            bandwidth is to be received within 400 kHz, the
            transmitted signal bandwidth should be
            maximum 400 kHz - 2*37 kHz, which is 326
            kHz.

        DR:1.2kb Dev:5.1khz Mod:GFSK RXBW:63kHz sensitive     fsctrl1:06 mdmcfg:e5 a3 13 23 11 dev:16 foc/bscfg:17/6c agctrl:03 40 91 frend:56 10
        DR:1.2kb Dev:5.1khz Mod:GFSK RXBW:63kHz lowpower      fsctrl1:06 mdmcfg:e5 a3 93 23 11 dev:16 foc/bscfg:17/6c agctrl:03 40 91 frend:56 10    (DEM_DCFILT_OFF)
        DR:2.4kb Dev:5.1khz Mod:GFSK RXBW:63kHz sensitive     fsctrl1:06 mdmcfg:e6 a3 13 23 11 dev:16 foc/bscfg:17/6c agctrl:03 40 91 frend:56 10
        DR:2.4kb Dev:5.1khz Mod:GFSK RXBW:63kHz lowpower      fsctrl1:06 mdmcfg:e6 a3 93 23 11 dev:16 foc/bscfg:17/6c agctrl:03 40 91 frend:56 10    (DEM_DCFILT_OFF)
        DR:38.4kb Dev:20khz Mod:GFSK RXBW:94kHz sensitive     fsctrl1:08 mdmcfg:ca a3 13 23 11 dev:36 foc/bscfg:16/6c agctrl:43 40 91 frend:56 10    (IF changes, Deviation)
        DR:38.4kb Dev:20khz Mod:GFSK RXBW:94kHz lowpower      fsctrl1:08 mdmcfg:ca a3 93 23 11 dev:36 foc/bscfg:16/6c agctrl:43 40 91 frend:56 10    (.. DEM_DCFILT_OFF)

        DR:250kb Dev:129khz Mod:GFSK RXBW:600kHz sensitive    fsctrl1:0c mdmcfg:1d 55 13 23 11 dev:63 foc/bscfg:1d/1c agctrl:c7 00 b0 frend:b6 10    (IF_changes, Deviation)

        DR:500kb            Mod:MSK  RXBW:750kHz sensitive    fsctrl1:0e mdmcfg:0e 55 73 43 11 dev:00 foc/bscfg:1d/1c agctrl:c7 00 b0 frend:b6 10    (IF_changes, Modulation of course, Deviation has different meaning with MSK)
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        chanbw_e = None
        chanbw_m = None
        for e in range(4):
            m = int(((mhz*1000000.0 / (bw *pow(2,e) * 8.0 )) - 4) + .5)        # rounded evenly
            if m < 4:
                chanbw_e = e
                chanbw_m = m
                break
        if chanbw_e is None:
            raise(Exception("ChanBW does not translate into acceptable parameters.  Should you be changing this?"))

        bw = 1000.0*mhz / (8.0*(4+chanbw_m) * pow(2,chanbw_e))
        print "chanbw_e: %x   chanbw_m: %x   chanbw: %f kHz" % (e, m, bw)

        self.radiocfg.mdmcfg4 &= 0x0f
        self.radiocfg.mdmcfg4 |= ((chanbw_e<<6) | (chanbw_m<<4))
        self.setRFRegister(MDMCFG4, (self.radiocfg.mdmcfg4))

    def getMdmChanBW(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        chanbw_e = (self.radiocfg.mdmcfg4 >> 6) & 0x3
        chanbw_m = (self.radiocfg.mdmcfg4 >> 4) & 0x3
        bw = 1000000.0*mhz / (8.0*(4+chanbw_m) * pow(2,chanbw_e))
        #print "chanbw_e: %x   chanbw_m: %x   chanbw: %f hz" % (chanbw_e, chanbw_m, bw)
        return bw

    def setMdmDRate(self, drate, mhz=24, radiocfg=None):
        ''' 
        set the baud of data being modulated through the radio
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        drate_e = None
        drate_m = None
        for e in range(16):
            m = int((drate * pow(2,28) / (pow(2,e)* (mhz*1000000.0))-256) + .5)        # rounded evenly
            if m < 256:
                drate_e = e
                drate_m = m
                break
        if drate_e is None:
            raise(Exception("DRate does not translate into acceptable parameters.  Should you be changing this?"))

        drate = 1000000.0 * mhz * (256+drate_m) * pow(2,drate_e) / pow(2,28)
        print "drate_e: %x   drate_m: %x   drate: %f Hz" % (drate_e, drate_m, drate)
        
        radiocfg.mdmcfg3 = drate_m
        radiocfg.mdmcfg4 &= 0xf0
        radiocfg.mdmcfg4 |= drate_e
        self.setRFRegister(MDMCFG3, (radiocfg.mdmcfg3))
        self.setRFRegister(MDMCFG4, (radiocfg.mdmcfg4))

    def getMdmDRate(self, mhz=24, radiocfg=None):
        ''' 
        get the baud of data being modulated through the radio
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        drate_e = radiocfg.mdmcfg4 & 0xf
        drate_m = radiocfg.mdmcfg3

        drate = 1000000.0 * mhz * (256+drate_m) * pow(2,drate_e) / pow(2,28)
        #print "drate_e: %x   drate_m: %x   drate: %f hz" % (drate_e, drate_m, drate)
        return drate
        
        
    def setMdmDeviatn(self, deviatn, mhz=24, radiocfg=None):
        ''' 
        configure the deviation settings for the given modulation scheme
        '''
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        dev_e = None
        dev_m = None
        for e in range(8):
            m = int((deviatn * pow(2,17) / (pow(2,e)* (mhz*1000000.0))-8) + .5)        # rounded evenly
            if m < 8:
                dev_e = e
                dev_m = m
                break
        if dev_e is None:
            raise(Exception("Deviation does not translate into acceptable parameters.  Should you be changing this?"))

        dev = 1000000.0 * mhz * (8+dev_m) * pow(2,dev_e) / pow(2,17)
        print "dev_e: %x   dev_m: %x   deviatn: %f Hz" % (e, m, dev)
        
        self.radiocfg.deviatn = (dev_e << 4) | dev_m
        self.setRFRegister(DEVIATN, self.radiocfg.deviatn)

    def getMdmDeviatn(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        dev_e = radiocfg.deviatn >> 4
        dev_m = radiocfg.deviatn & 0x7 
        dev = 1000000.0 * mhz * (8+dev_m) * pow(2,dev_e) / pow(2,17)
        return dev


    def setMdmSyncWord(self, word, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        radiocfg.sync1 = word >> 8
        radiocfg.sync0 = word & 0xff
        self.setRFRegister(SYNC1, (self.radiocfg.sync1))
        self.setRFRegister(SYNC0, (self.radiocfg.sync0))

    def getMdmSyncMode(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg
        
        return radiocfg.mdmcfg2&0x07

    def setMdmSyncMode(self, syncmode=SYNCM_15_of_16, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        radiocfg.mdmcfg2 &= 0xf8
        radiocfg.mdmcfg2 |= syncmode
        self.setRFRegister(MDMCFG2, (self.radiocfg.mdmcfg2))

    def calculateMdmDeviatn(self, mhz=24, radiocfg=None):
        ''' calculates the optimal DEVIATN setting for the current freq/baud
        * totally experimental *
        from Smart RF Studio:
        1.2 kbaud 5.1khz dev
        2.4 kbaud 5.1khz dev
        38.4 kbaud 20khz dev
        250 kbaud 129khz dev
        '''
        baud = self.getMdmDRate(mhz, radiocfg)
        if baud <= 2400:
            deviatn = 5100
        elif baud <= 38400:
            deviatn = 20000 * ((baud-2400)/36000)
        else:
            deviatn = 129000 * ((baud-38400)/211600)
        self.setMdmDeviatn(deviatn)

    def calculatePktChanBW(self, mhz=24, radiocfg=None):
        ''' calculates the optimal ChanBW setting for the current freq/baud
        * totally experimental *
        from Smart RF Studio:
        1.2 kbaud BW: 63khz
        2.4 kbaud BW: 63khz
        38.4kbaud BW: 94khz
        250 kbaud BW: 600khz
        '''
        freq, freqhex = self.getFreq()
        center_freq = freq + 14000000
        freq_uncertainty =  20e-6 * freq  # +-20ppm
        freq_uncertainty *= 2          # both xmitter and receiver
        #minbw = (2 * freq_uncertainty) + self.getMdmDRate() # uncertainty for both sender/receiver
        minbw = (self.getMdmDRate() + freq_uncertainty) 

        possibles = [ 53e3,63e3,75e3,93e3,107e3,125e3,150e3,188e3,214e3,250e3,300e3,375e3,428e3,500e3,600e3,750e3, ]
        for bw in possibles:
            #if (.8 * bw)  > minbw:      # can't occupy more the 80% of BW
            if (bw)  > minbw:
                break
        self.setMdmChanBW(bw, mhz, radiocfg)

    def calculateFsIF(self, mhz=24, radiocfg=None):
        ''' calculates the optimal IF setting for the current freq/baud
        * totally experimental *
        1.2 kbaud IF: 140khz
        2.4 kbaud IF: 140khz
        38.4kbaud IF: 164khz (140khz for "sensitive" version)
        250 kbaud IF: 281khz
        500 kbaud IF: 328khz
        '''
        pass
    def calculateFsOffset(self, mhz=24, radiocfg=None):
        ''' calculates the optimal FreqOffset setting for the current freq/baud
        * totally experimental *
        '''

        pass

    def reprModemConfig(self, mhz=24, radiocfg=None):
        output = []
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        reprMdmModulation = self.reprMdmModulation(radiocfg)
        syncmode = self.getMdmSyncMode(radiocfg)

        #chanbw_e = radiocfg.mdmcfg4>>6
        #chanbw_m = (radiocfg.mdmcfg4>>4) & 0x3
        #bw = 1000000.0*mhz / (8.0*(4+chanbw_m) * pow(2,chanbw_e))
        bw = self.getMdmChanBW(mhz, radiocfg)
        output.append("ChanBW:              %f hz"%bw)

        #drate_e = radiocfg.mdmcfg4 & 0xf
        #drate_m = radiocfg.mdmcfg3
        #drate = 1000000.0 * mhz * (256+drate_m) * pow(2,drate_e) / pow(2,28)
        drate = self.getMdmDRate(mhz, radiocfg)
        output.append("DRate:               %f hz"%drate)

        #output.append("DC Filter:           %s" % (("enabled", "disabled")[radiocfg.mdmcfg2>>7]))
        output.append("DC Filter:           %s" % (("enabled", "disabled")[self.getEnableMdmDCFilter(radiocfg)]))

        output.append(reprMdmModulation)
        output.append("DEVIATION:           %f hz" % self.getMdmDeviatn(mhz, radiocfg))

        output.append("Sync Mode:           %s" % SYNCMODES[syncmode])

        mchstr = self.getEnableMdmManchester(radiocfg)
        output.append("Manchester Encoding: %s" %  (("disabled","enabled")[mchstr]))

        #fec = radiocfg.mdmcfg1>>7
        fec = self.getEnableMdmFEC(radiocfg)
        output.append("Fwd Err Correct:     %s" % (("disabled","enabled")[fec]))
        
        num_preamble = (radiocfg.mdmcfg1>>4)&7
        output.append("Min TX Preamble:     %d bytes" % (NUM_PREAMBLE[num_preamble]) )

        #chanspc_e = radiocfg.mdmcfg1&3
        #chanspc_m = radiocfg.mdmcfg0
        #chanspc = 1000000.0 * mhz/pow(2,18) * (256 + chanspc_m) * pow(2, chanspc_e)
        chanspc = self.getMdmChanSpc(mhz, radiocfg)
        output.append("Chan Spacing:        %f hz" % chanspc)


        return "\n".join(output)

    def getRSSI(self):
        rssi = self.peek(RSSI)
        return rssi

    def getLQI(self):
        lqi = self.peek(LQI)
        return lqi

       
    def reprRadioTestSignalConfig(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        output = []
        output.append("GDO2_INV:            %s" % ("do not Invert Output", "Invert output")[(radiocfg.iocfg2>>6)&1])
        output.append("GDO2CFG:             0x%x" % (radiocfg.iocfg2&0x3f))
        output.append("GDO_DS:              %s" % (("minimum drive (>2.6vdd","Maximum drive (<2.6vdd)")[radiocfg.iocfg1>>7]))
        output.append("GDO1_INV:            %s" % ("do not Invert Output", "Invert output")[(radiocfg.iocfg1>>6)&1])
        output.append("GDO1CFG:             0x%x"%(radiocfg.iocfg1&0x3f))
        output.append("GDO0_INV:            %s" % ("do not Invert Output", "Invert output")[(radiocfg.iocfg0>>6)&1])
        output.append("GDO0CFG:             0x%x"%(radiocfg.iocfg0&0x3f))
        output.append("TEST2:               0x%x"%radiocfg.test2)
        output.append("TEST1:               0x%x"%radiocfg.test1)
        output.append("TEST0:               0x%x"%(radiocfg.test0&0xfd))
        output.append("VCO_SEL_CAL_EN:      0x%x"%((radiocfg.test2>>1)&1))
        return "\n".join(output)


    def reprFreqConfig(self, mhz=24, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        output = []
        freq,num = self.getFreq(mhz, radiocfg)
        output.append("Frequency:           %f hz (%s)" % (freq,num))

        output.append("Channel:             %d" % radiocfg.channr)


        #freq_if = (radiocfg.fsctrl1&0x1f) * (1000000.0 * mhz / pow(2,10))
        #freqoff = radiocfg.fsctrl0
        freq_if = self.getFsIF(mhz, radiocfg)
        freqoff = self.getFsOffset(mhz, radiocfg)
        
        output.append("Intermediate freq:   %d hz" % freq_if)
        output.append("Frequency Offset:    %d +/-" % freqoff)

        return "\n".join(output)

    def reprPacketConfig(self, radiocfg=None):
        if radiocfg==None:
            self.getRadioConfig()
            radiocfg = self.radiocfg

        output = []
        output.append("Sync Bytes:      %.2x %.2x" % (radiocfg.sync1, radiocfg.sync0))
        output.append("Packet Length:       %d" % radiocfg.pktlen)
        output.append("Configured Address: 0x%x" % radiocfg.addr)

        #pqt = radiocfg.pktctrl1>>5
        pqt = self.getPktPQT(radiocfg)
        output.append("Preamble Quality Threshold: 4 * %d" % pqt)

        append = (radiocfg.pktctrl1>>2) & 1
        output.append("Append Status:       %s" % ("No","Yes")[append])

        adr_chk = radiocfg.pktctrl1&3
        output.append("Rcvd Packet Check:   %s" % ADR_CHK_TYPES[adr_chk])

        #whitedata = (radiocfg.pktctrl0>>6)&1
        whitedata = self.getEnablePktDataWhitening(radiocfg)
        output.append("Data Whitening:      %s" % ("off", "ON (but only with cc2400_en==0)")[whitedata])

        pkt_format = (radiocfg.pktctrl0>>5)&3
        output.append("Packet Format:       %s" % PKT_FORMATS[pkt_format])

        #crc = (radiocfg.pktctrl0>>2)&1
        crc = self.getEnablePktCRC(radiocfg)
        output.append("CRC:                 %s" % ("disabled", "ENABLED")[crc])

        length_config = radiocfg.pktctrl0&3
        output.append("Length Config:       %s" % LENGTH_CONFIGS[length_config])

        return "\n".join(output)
    """
    SYNC1       = 0xa9;
    SYNC0       = 0x47;
    PKTLEN      = 0xff;
    PKTCTRL1    = 0x04;             // APPEND_STATUS
    PKTCTRL0    = 0x01;             // VARIABLE LENGTH, no crc, no whitening
    ADDR        = 0x00;
    CHANNR      = 0x00;
    FSCTRL1     = 0x0c;             // IF
    FSCTRL0     = 0x00;
    FREQ2       = 0x25;
    FREQ1       = 0x95;
    FREQ0       = 0x55;
    MDMCFG4     = 0x1d;             // chan_bw and drate_e
    MDMCFG3     = 0x55;             // drate_m
    MDMCFG2     = 0x13;             // gfsk, 30/32+carrier sense sync 
    MDMCFG1     = 0x23;             // 4-preamble-bytes, chanspc_e
    MDMCFG0     = 0x11;             // chanspc_m
    DEVIATN     = 0x63;
    MCSM2       = 0x07;             // RX_TIMEOUT
    MCSM1       = 0x30;             // CCA_MODE RSSI below threshold unless currently recvg pkt
    MCSM0       = 0x18;             // fsautosync when going from idle to rx/tx/fstxon
    FOCCFG      = 0x1d;             
    BSCFG       = 0x1c;             // bit sync config
    AGCCTRL2    = 0xc7;
    AGCCTRL1    = 0x00;
    AGCCTRL0    = 0xb0;
    FREND1      = 0xb6;
    FREND0      = 0x10;
    FSCAL3      = 0xea;
    FSCAL2      = 0x2a;
    FSCAL1      = 0x00;
    FSCAL0      = 0x1f;
    TEST2       = 0x88;
    TEST1       = 0x31;
    TEST0       = 0x09;
    PA_TABLE0   = 0x83;
"""

    def reprRadioState(self, radiocfg=None):
        output = []
        try:
            if radiocfg==None:
                self.getRadioConfig()
                radiocfg = self.radiocfg

            output.append("     MARCSTATE:      %s (%x)" % (self.getMARCSTATE(radiocfg)))
            output.append("     DONGLE RESPONDING:  mode :%x, last error# %d"%(self.getDebugCodes()))
        except:
            output.append(repr(sys.exc_info()))
            output.append("     DONGLE *not* RESPONDING")

        return "\n".join(output)

    def reprClientState(self):
        output = []
        output.append('     client thread cycles:      %d' % self.threadcounter)
        output.append('     client errored cycles:     %d' % self._usberrorcnt)
        output.append('     recv_queue:\t\t (%d bytes) "%s"'%(len(self.recv_queue),repr(self.recv_queue)[:len(self.recv_queue)%39+20]))
        output.append('     trash:     \t\t (%d bytes) "%s"'%(len(self.trash),repr(self.trash)[:min(len(self.trash),39)+20]))
        output.append('     recv_mbox  \t\t (%d keys)  "%s"'%(len(self.recv_mbox),repr(self.recv_mbox)[:min(len(repr(self.recv_mbox)),79)]))
        for app in self.recv_mbox.keys():
            appbox = self.recv_mbox[app]
            output.append('       app 0x%x\t (%d records)  "%s"'%(app,len(appbox),repr(appbox)[:min(len(repr(appbox)),79)]))
            for cmd in appbox.keys():
                strlen = min(len(repr(appbox[cmd])),79)
                output.append('             [0x%x]\t (%d records)  "%s"'%(cmd, len(appbox[cmd]), repr(appbox[cmd])[:strlen]))
        return "\n".join(output)


    ######## APPLICATION METHODS ########
    def setup900MHz(self):
        self.getRadioConfig()
        rc = self.radiocfg
        rc.iocfg0     = 0x06
        rc.sync1      = 0x0b
        rc.sync0      = 0x0b
        rc.pktlen     = 0xff
        rc.pktctrl1   = 0xe5
        rc.pktctrl0   = 0x04
        rc.fsctrl1    = 0x12
        rc.fsctrl0    = 0x00
        rc.addr       = 0x00
        rc.channr     = 0x00
        rc.mdmcfg4    = 0x3e
        rc.mdmcfg3    = 0x55
        rc.mdmcfg2    = 0x73
        rc.mdmcfg1    = 0x23
        rc.mdmcfg0    = 0x55
        rc.mcsm2      = 0x07
        rc.mcsm1      = 0x30
        rc.mcsm0      = 0x00
        rc.deviatn    = 0x16
        rc.foccfg     = 0x17
        rc.bscfg      = 0x6c
        rc.agcctrl2  |= AGCCTRL2_MAX_DVGA_GAIN
        rc.agcctrl2   = 0x03
        rc.agcctrl1   = 0x40
        rc.agcctrl0   = 0x91
        rc.frend1     = 0x56
        rc.frend0     = 0x10
        rc.fscal3     = 0xEA
        rc.fscal2     = 0x2A
        rc.fscal1     = 0x00
        rc.fscal0     = 0x1F
        rc.test2      = 0x88
        rc.test1      = 0x31
        rc.test0      = 0x09
        rc.pa_table0  = 0xc0
        self.setRadioConfig()

    def setup900MHzHopTrans(self):
        self.getRadioConfig()
        rc = self.radiocfg
        rc.iocfg0     = 0x06
        rc.sync1      = 0x0b
        rc.sync0      = 0x0b
        rc.pktlen     = 0xff
        rc.pktctrl1   = 0x04
        rc.pktctrl0   = 0x05
        rc.addr       = 0x00
        rc.channr     = 0x00
        rc.fsctrl1    = 0x06
        rc.fsctrl0    = 0x00
        rc.mdmcfg4    = 0xee
        rc.mdmcfg3    = 0x55
        rc.mdmcfg2    = 0x73
        rc.mdmcfg1    = 0x23
        rc.mdmcfg0    = 0x55
        rc.mcsm2      = 0x07
        rc.mcsm1      = 0x30
        rc.mcsm0      = 0x18
        rc.deviatn    = 0x16
        rc.foccfg     = 0x17
        rc.bscfg      = 0x6c
        rc.agcctrl2   = 0x03
        rc.agcctrl1   = 0x40
        rc.agcctrl0   = 0x91
        rc.frend1     = 0x56
        rc.frend0     = 0x10
        rc.fscal3     = 0xEA
        rc.fscal2     = 0x2A
        rc.fscal1     = 0x00
        rc.fscal0     = 0x1F
        rc.test2      = 0x88
        rc.test1      = 0x31
        rc.test0      = 0x09
        rc.pa_table0  = 0xc0
        self.setRadioConfig()

    def setup900MHzContTrans(self):
        self.getRadioConfig()
        rc = self.radiocfg
        rc.iocfg0     = 0x06
        rc.sync1      = 0x0b
        rc.sync0      = 0x0b
        rc.pktlen     = 0xff
        rc.pktctrl1   = 0x04
        rc.pktctrl0   = 0x05
        rc.addr       = 0x00
        rc.channr     = 0x00
        rc.fsctrl1    = 0x06
        rc.fsctrl0    = 0x00
        rc.freq2      = 0x26
        rc.freq1      = 0x55
        rc.freq0      = 0x55
        rc.mdmcfg4    = 0xee
        rc.mdmcfg3    = 0x55
        rc.mdmcfg2    = 0x73
        rc.mdmcfg1    = 0x23
        rc.mdmcfg0    = 0x55
        rc.mcsm2      = 0x07
        rc.mcsm1      = 0x30
        rc.mcsm0      = 0x18
        rc.deviatn    = 0x16
        rc.foccfg     = 0x17
        rc.bscfg      = 0x6c
        rc.agcctrl2   = 0x03
        rc.agcctrl1   = 0x40
        rc.agcctrl0   = 0x91
        rc.frend1     = 0x56
        rc.frend0     = 0x10
        rc.fscal3     = 0xEA
        rc.fscal2     = 0x2A
        rc.fscal1     = 0x00
        rc.fscal0     = 0x1F
        rc.test2      = 0x88
        rc.test1      = 0x31
        rc.test0      = 0x09
        rc.pa_table0  = 0xc0
        self.setRadioConfig()

    def setup_rfstudio_902PktTx(self):
        self.getRadioConfig()
        rc = self.radiocfg
        rc.iocfg2     = 0x00
        rc.iocfg1     = 0x00
        rc.iocfg0     = 0x06
        rc.sync1      = 0x0b
        rc.sync0      = 0x0b
        rc.pktlen     = 0xff
        rc.pktctrl1   = 0x04
        rc.pktctrl0   = 0x05
        rc.addr       = 0x00
        rc.channr     = 0x00
        rc.fsctrl1    = 0x0c
        rc.fsctrl0    = 0x00
        rc.freq2      = 0x25
        rc.freq1      = 0x95
        rc.freq0      = 0x55
        rc.mdmcfg4    = 0x1d
        rc.mdmcfg3    = 0x55
        rc.mdmcfg2    = 0x13
        rc.mdmcfg1    = 0x23
        rc.mdmcfg0    = 0x11
        rc.mcsm2      = 0x07
        rc.mcsm1      = 0x30
        rc.mcsm0      = 0x18
        rc.deviatn    = 0x63
        rc.foccfg     = 0x1d
        rc.bscfg      = 0x1c
        rc.agcctrl2   = 0xc7
        rc.agcctrl1   = 0x00
        rc.agcctrl0   = 0xb0
        rc.frend1     = 0xb6
        rc.frend0     = 0x10
        rc.fscal3     = 0xEA
        rc.fscal2     = 0x2A
        rc.fscal1     = 0x00
        rc.fscal0     = 0x1F
        rc.test2      = 0x88
        rc.test1      = 0x31
        rc.test0      = 0x09
        rc.pa_table7  = 0x00
        rc.pa_table6  = 0x00
        rc.pa_table5  = 0x00
        rc.pa_table4  = 0x00
        rc.pa_table3  = 0x00
        rc.pa_table2  = 0x00
        rc.pa_table1  = 0x00
        #rc.pa_table0  = 0x8e
        rc.pa_table0  = 0xc0
        self.setRadioConfig()

    def testTX(self, data="XYZABCDEFGHIJKL"):
        while (sys.stdin not in select.select([sys.stdin],[],[],0)[0]):
            time.sleep(.4)
            print "transmitting %s" % repr(data)
            self.RFxmit(data)
        sys.stdin.read(1)

    def lowball(self, level=1):
        '''
        this configures the radio to the lowest possible level of filtering, potentially allowing complete radio noise to come through as data.  very useful in some circumstances.
        level == 0 changes the Sync Mode to SYNCM_NONE (wayyy more garbage)
        level == 1 (default) sets the Sync Mode to SYNCM_CARRIER (requires a valid carrier detection for the data to be considered a packet)
        '''
        if hasattr(self, '_last_radiocfg') and len(self._last_radiocfg):
            raise(Exception('i simply will not allow you to run lowball() twice in a row!  lowballRestore() to restore the radio config from before last time you ran lowball'))
        self._last_radiocfg = self.getRadioConfig()

        self.makePktFLEN(250)
        self.setEnablePktCRC(False)
        self.setEnableMdmFEC(False)
        self.setEnablePktDataWhitening(False)
        self.setMdmSyncWord(0xaaaa)
        self.setPktPQT(0)
        
        if (level == 3):
            self.setMdmSyncMode(SYNCM_CARRIER_16_of_16)
        elif (level == 2):
            self.setMdmSyncMode(SYNCM_15_of_16)
        elif (level == 1):
            self.setMdmSyncMode(SYNCM_CARRIER)
        else:
            self.setMdmSyncMode(SYNCM_NONE)


    def lowballRestore(self):
        if not hasattr(self, '_last_radiocfg'):
            raise(Exception("lowballRestore requires that lowball have been executed first (it saves radio config state!)"))
        self.setRadioConfig(self._last_radiocfg)
        self._last_radiocfg = ''

   
    def discover(self, debug=None, lowball=1, SyncWordMatchList=None):
        oldebug = self._debug
        print "Entering Lowball mode and searching for possible SyncWords"
        self.lowball()
        self.makePktFLEN(30)
        if debug is not None:
            self._debug = debug
        while not len(select.select([sys.stdin],[],[],0)[0]):

            try:
                y, t = self.RFrecv()
                print "(%5.3f) Received:  %s" % (t, y.encode('hex'))
                if lowball:
                    y = '\xaa\xaa' + y
                poss = bits.findDword(y)
                if len(poss):
                    print "  possible Sync Dwords: %s" % repr([hex(x) for x in poss])

                if SyncWordMatchList is not None:
                    for x in poss:
                        if x in SyncWordMatchList:
                            print "MATCH WITH KNOWN SYNC WORD:" + hex(x)
            except CC111xTimeoutException:
                pass

        sys.stdin.read(1)
        self._debug = oldebug
        self.lowballRestore()
        print "Exiting..."


    def checkRepr(self, matchstr, checkval, maxdiff=0):
        starry = self.reprRadioConfig().split('\n')
        line,val = getValueFromReprString(starry, matchstr)
        try:
            f = checkval.__class__(val.split(" ")[0])
            if abs(f-checkval) <= maxdiff:
                print "  passed: reprRadioConfig test: %s %s" % (repr(val), checkval)
            else:
                print " *FAILED* reprRadioConfig test: %s %s %s" % (repr(line), repr(val), checkval)

        except ValueError, e:
            print "  ERROR checking repr: %s" % e


def unittest(self, mhz=24):
    print "\nTesting USB ping()"
    self.ping(3)
    
    print "\nTesting USB ep0Ping()"
    self.ep0Ping()
    
    print "\nTesting USB enumeration"
    print "getString(0,100): %s" % repr(self._do.getString(0,100))
    
    print "\nTesting USB EP MAX_PACKET_SIZE handling (ep0Peek(0xf000, 100))"
    print repr(self.ep0Peek(0xf000, 100))

    print "\nTesting USB EP MAX_PACKET_SIZE handling (peek(0xf000, 300))"
    print repr(self.peek(0xf000, 400))

    print "\nTesting USB poke/peek"
    data = "".join([chr(c) for c in xrange(120)])
    where = 0xf300
    self.poke(where, data)
    ndata = self.peek(where, len(data))
    if ndata != data:
        print " *FAILED*\n '%s'\n '%s'" % (data.encode("hex"), ndata.encode("hex"))
        raise(Exception(" *FAILED*\n '%s'\n '%s'" % (data.encode("hex"), ndata.encode("hex"))))
    else:
        print "  passed  '%s'" % (ndata.encode("hex"))

    print "\nTesting getValueFromReprString()"
    starry = self.reprRadioConfig().split('\n')
    print repr(getValueFromReprString(starry, 'hz'))

    print "\nTesting reprRadioConfig()"
    print self.reprRadioConfig()

    print "\nTesting Frequency Get/Setters"
    # FREQ
    freq0,freq0str = self.getFreq()

    testfreq = 902000000
    self.setFreq(testfreq)
    freq,freqstr = self.getFreq()
    if abs(testfreq - freq) < 1024:
        print "  passed: %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)
    else:
        print " *FAILED* %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)

    testfreq = 868000000
    self.setFreq(testfreq)
    freq,freqstr = self.getFreq()
    if abs(testfreq - freq) < 1024:
        print "  passed: %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)
    else:
        print " *FAILED* %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)

    testfreq = 433000000
    self.setFreq(testfreq)
    freq,freqstr = self.getFreq()
    if abs(testfreq - freq) < 1024:
        print "  passed: %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)
    else:
        print " *FAILED* %d : %f  (diff: %f)" % (testfreq, freq, testfreq-freq)
   
    self.checkRepr("Frequency:", float(testfreq), 1024)
    self.setFreq(freq0)

    # CHANNR
    channr0 = self.getChannel()
    for x in range(15):
        self.setChannel(x)
        channr = self.getChannel()
        if channr != x:
            print " *FAILED* get/setChannel():  %d : %d" % (x, channr)
        else:
            print "  passed: get/setChannel():  %d : %d" % (x, channr)
    self.checkRepr("Channel:", channr)
    self.setChannel(channr0)

    # IF and FREQ_OFF
    freq_if = self.getFsIF()
    freqoff = self.getFsOffset()
    for fif, foff in ((164062,1),(140625,2),(187500,3)):
        self.setFsIF(fif)
        self.setFsOffset(foff)
        nfif  = self.getFsIF()
        nfoff = self.getFsOffset()
        if abs(nfif - fif) > 5:
            print " *FAILED* get/setFsIFandOffset():  %d : %f (diff: %f)" % (fif,nfif,nfif-fif)
        else:
            print "  passed: get/setFsIFandOffset():  %d : %f (diff: %f)" % (fif,nfif,nfif-fif)

        if foff != nfoff:
            print " *FAILED* get/setFsIFandOffset():  %d : %d (diff: %d)" % (foff,nfoff,nfoff-foff)
        else:
            print "  passed: get/setFsIFandOffset():  %d : %d (diff: %d)" % (foff,nfoff,nfoff-foff)
    self.checkRepr("Intermediate freq:", fif, 11720)
    self.checkRepr("Frequency Offset:", foff)
    
    self.setFsIF(freq_if)
    self.setFsOffset(freqoff)

    ### continuing with more simple tests.  add completeness later?
    # Modem tests

    mod = self.getMdmModulation(self.radiocfg)
    self.setMdmModulation(mod, self.radiocfg)
    modcheck = self.getMdmModulation(self.radiocfg)
    if mod != modcheck:
        print " *FAILED* get/setMdmModulation():  %d : %d " % (mod, modcheck)
    else:
        print "  passed: get/setMdmModulation():  %d : %d " % (mod, modcheck)

    chanspc = self.getMdmChanSpc(mhz, self.radiocfg)
    self.setMdmChanSpc(chanspc, mhz, self.radiocfg)
    chanspc_check = self.getMdmChanSpc(mhz, self.radiocfg)
    if chanspc != chanspc_check:
        print " *FAILED* get/setMdmChanSpc():  %d : %d" % (chanspc, chanspc_check)
    else:
        print "  passed: get/setMdmChanSpc():  %d : %d" % (chanspc, chanspc_check)

    chanbw = self.getMdmChanBW(mhz, self.radiocfg)
    self.setMdmChanBW(chanbw, mhz, self.radiocfg)
    chanbw_check = self.getMdmChanBW(mhz, self.radiocfg)
    if chanbw != chanbw_check:
        print " *FAILED* get/setMdmChanBW():  %d : %d" % (chanbw, chanbw_check)
    else:
        print "  passed: get/setMdmChanBW():  %d : %d" % (chanbw, chanbw_check)

    drate = self.getMdmDRate(mhz, self.radiocfg)
    self.setMdmDRate(drate, mhz, self.radiocfg)
    drate_check = self.getMdmDRate(mhz, self.radiocfg)
    if drate != drate_check:
        print " *FAILED* get/setMdmDRate():  %d : %d" % (drate, drate_check)
    else:
        print "  passed: get/setMdmDRate():  %d : %d" % (drate, drate_check)

    deviatn = self.getMdmDeviatn(mhz, self.radiocfg)
    self.setMdmDeviatn(deviatn, mhz, self.radiocfg)
    deviatn_check = self.getMdmDeviatn(mhz, self.radiocfg)
    if deviatn != deviatn_check:
        print " *FAILED* get/setMdmdeviatn():  %d : %d" % (deviatn, deviatn_check)
    else:
        print "  passed: get/setMdmdeviatn():  %d : %d" % (deviatn, deviatn_check)

    syncm = self.getMdmSyncMode(self.radiocfg)
    self.setMdmSyncMode(syncm, self.radiocfg)
    syncm_check = self.getMdmSyncMode(self.radiocfg)
    if syncm != syncm_check:
        print " *FAILED* get/setMdmSyncMode():  %d : %d" % (syncm, syncm_check)
    else:
        print "  passed: get/setMdmSyncMode():  %d : %d" % (syncm, syncm_check)

    mchstr = self.getEnableMdmManchester(self.radiocfg)
    self.setEnableMdmManchester(mchstr, self.radiocfg)
    mchstr_check = self.getEnableMdmManchester(self.radiocfg)
    if mchstr != mchstr_check:
        print " *FAILED* get/setMdmManchester():  %d : %d" % (mchstr, mchstr_check)
    else:
        print "  passed: get/setMdmManchester():  %d : %d" % (mchstr, mchstr_check)

    fec = self.getEnableMdmFEC(self.radiocfg)
    self.setEnableMdmFEC(fec, self.radiocfg)
    fec_check = self.getEnableMdmFEC(self.radiocfg)
    if fec != fec_check:
        print " *FAILED* get/setEnableMdmFEC():  %d : %d" % (fec, fec_check)
    else:
        print "  passed: get/setEnableMdmFEC():  %d : %d" % (fec, fec_check)

    dcf = self.getEnableMdmDCFilter(self.radiocfg)
    self.setEnableMdmDCFilter(dcf, self.radiocfg)
    dcf_check = self.getEnableMdmDCFilter(self.radiocfg)
    if dcf != dcf_check:
        print " *FAILED* get/setEnableMdmDCFilter():  %d : %d" % (dcf, dcf_check)
    else:
        print "  passed: get/setEnableMdmDCFilter():  %d : %d" % (dcf, dcf_check)


    # Pkt tests
    pqt = self.getPktPQT(self.radiocfg)
    self.setPktPQT(pqt, self.radiocfg)
    pqt_check = self.getPktPQT(self.radiocfg)
    if pqt != pqt_check:
        print " *FAILED* get/setEnableMdmFEC():  %d : %d" % (pqt, pqt_check)
    else:
        print "  passed: get/setEnableMdmFEC():  %d : %d" % (pqt, pqt_check)

def getValueFromReprString(stringarray, line_text):
    for string in stringarray:
        if line_text in string:
            idx = string.find(":")
            val = string[idx+1:].strip()
            return (string,val)

def mkFreq(freq=902000000, mhz=24):
    freqmult = (0x10000 / 1000000.0) / mhz
    num = int(freq * freqmult)
    freq2 = num >> 16
    freq1 = (num>>8) & 0xff
    freq0 = num & 0xff
    return (num, freq2,freq1,freq0)



if __name__ == "__main__":
    idx = 0
    if len(sys.argv) > 1:
        idx = int(sys.argv.pop())
    d = USBDongle(idx=idx)

