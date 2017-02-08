#!/usr/bin/env ipython
import sys, threading, time, struct, select
import usb

import bits
from chipcondefs import *
from rflib_defs import *
from rflib_version import *

DEFAULT_USB_TIMEOUT = 1000

EP_TIMEOUT_IDLE     = 400
EP_TIMEOUT_ACTIVE   = 10

USB_MAX_BLOCK_SIZE  = 512
USB_RX_WAIT         = 1000
USB_TX_WAIT         = 10000

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
SYS_CMD_BOOTLOADER              = 0x87
SYS_CMD_RFMODE                  = 0x88
SYS_CMD_COMPILER                = 0x89
SYS_CMD_PARTNUM                 = 0x8e
SYS_CMD_RESET                   = 0x8f
SYS_CMD_CLEAR_CODES             = 0x90

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
# EP5OUT_BUFFER_SIZE must match firmware/include/chipcon_usb.h definition
EP5OUT_BUFFER_SIZE              = 516

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

RCS = {}
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
    if lcl.startswith("RC_"):
        RCS[lcl] = lcls[lcl]
        RCS[lcls[lcl]] = lcl

CHIPS = {
    0x91: "CC2511",
    0x81: "CC2510",
    0x11: "CC1111",
    0x01: "CC1110",
    }


def keystop(delay=0):
    return len(select.select([sys.stdin],[],[],delay)[0])

def getRfCatDevices():
    '''
    returns a list of USB device objects for any rfcats that are plugged in
    NOTE: if any rfcats are in bootloader mode, this will cause python to Exit
    '''
    rfcats = []
    for bus in usb.busses():
        for dev in bus.devices:
            # OpenMoko assigned or Legacy TI
            if (dev.idVendor == 0x0451 and dev.idProduct == 0x4715) or (dev.idVendor == 0x1d50 and (dev.idProduct == 0x6047 or dev.idProduct == 0x6048 or dev.idProduct == 0x605b)):
                rfcats.append(dev)

            elif (dev.idVendor == 0x1d50 and (dev.idProduct == 0x6049 or dev.idProduct == 0x604a)):
                print "Already in Bootloader Mode... exiting"
                exit(0)

    return rfcats

class ChipconUsbTimeoutException(Exception):
    def __str__(self):
        return "Timeout waiting for USB response."

direct=False

class USBDongle:
    ######## INITIALIZATION ########
    def __init__(self, idx=0, debug=False, copyDongle=None, RfMode=RFST_SRX):
        self.rsema = None
        self.xsema = None
        self._bootloader = False
        self._init_on_reconnect = True
        self._do = None
        self.idx = idx
        self.cleanup()
        self._debug = debug
        self._quiet = False
        self._threadGo = threading.Event()
        self._recv_time = 0
        self.radiocfg = RadioConfig()
        self._rfmode = RfMode
        self._radio_configured = False

        self.ctrl_thread = threading.Thread(target=self.run_ctrl)
        self.ctrl_thread.setDaemon(True)
        self.ctrl_thread.start()

        self.recv_thread = threading.Thread(target=self.runEP5_recv)
        self.recv_thread.setDaemon(True)
        self.recv_thread.start()

        self.send_thread = threading.Thread(target=self.runEP5_send)
        self.send_thread.setDaemon(True)
        self.send_thread.start()

        self.resetup(copyDongle=copyDongle)
        self.max_packet_size = USB_MAX_BLOCK_SIZE

    def cleanup(self):
        self._usberrorcnt = 0;
        self.recv_queue = ''
        self.recv_mbox  = {}
        self.recv_event = threading.Event()
        self.xmit_event = threading.Event()
        self.reset_event = threading.Event()
        self.xmit_queue = []
        self.xmit_event.clear()
        self.reset_event.clear()
        self.trash = []
   
    def setRFparameters(self):
        pass

    def run_ctrl(self):
        '''
        we wait for reset events and run resetup
        '''
        while True:
            self.reset_event.wait()
            self.resetup(False)
            self.reset_event.clear()
            time.sleep(4)

    def setup(self, console=True, copyDongle=None):
        global dongles

        if copyDongle is not None:
            self.devnum = copyDongle.devnum
            self._d = copyDongle._d
            self._do = copyDongle._do
            self._usbmaxi = copyDongle._usbmaxi
            self._usbmaxo = copyDongle._usbmaxo
            self._usbcfg = copyDongle._usbcfg
            self._usbintf = copyDongle._usbintf
            self._usbeps = copyDongle._usbeps
            self._threadGo.set()
            self.ep5timeout = EP_TIMEOUT_ACTIVE
            copyDongle._threadGo.clear()            # we're taking over from here.
            self.rsema = copyDongle.rsema
            self.xsema = copyDongle.xsema
            return

        dongles = []
        self.ep5timeout = EP_TIMEOUT_ACTIVE

        for dev in getRfCatDevices():
            if self._debug: print >>sys.stderr,(dev)
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

        self._threadGo.set()

        self.getRadioConfig()
        chip = self.getPartNum()
        chipstr = CHIPS.get(chip)

        self.chipnum = chip
        self.chipstr = chipstr

        if chip == None:
            print "Older firmware, consider upgrading."
        else:
            self.chipstr = "unrecognized dongle: %s" % chip

        if self._init_on_reconnect:
            if self._radio_configured:
                self._clear_buffers()
                self.setRadioConfig()
            else:
                self.setRFparameters()
                self._radio_configured = True

    def resetup(self, console=True, copyDongle=None):
        self._do=None
        if self._bootloader: 
            return
        #self._threadGo = True
        if self._debug: print >>sys.stderr,("waiting (resetup) %x" % self.idx)
        while (self._do==None):
            try:
                self.setup(console, copyDongle)
                if copyDongle is None:
                    self._clear_buffers(False)
                self.ping(3, wait=10, silent=True)
                self.setRfMode(self._rfmode)

            except Exception, e:
                #if console: sys.stderr.write('.')
                if not self._quiet:
                    print >>sys.stderr,("Error in resetup():" + repr(e))
                #if console or self._debug: print >>sys.stderr,("Error in resetup():" + repr(e))
                time.sleep(1)



    ########  BASE FOUNDATIONAL "HIDDEN" CALLS ########
    def _sendEP0(self, request=0, buf=None, value=0x200, index=0, timeout=DEFAULT_USB_TIMEOUT):
        if buf == None:
            buf = 'HELLO THERE'
        #return self._do.controlMsg(USB_BM_REQTYPE_TGT_EP|USB_BM_REQTYPE_TYPE_VENDOR|USB_BM_REQTYPE_DIR_OUT, request, "\x00\x00\x00\x00\x00\x00\x00\x00"+buf, value, index, timeout), buf
        return self._do.controlMsg(USB_BM_REQTYPE_TGT_EP|USB_BM_REQTYPE_TYPE_VENDOR|USB_BM_REQTYPE_DIR_OUT, request, buf, value, index, timeout), buf

    def _recvEP0(self, request=0, length=64, value=0, index=0, timeout=100):
        retary = ["%c"%x for x in self._do.controlMsg(USB_BM_REQTYPE_TGT_EP|USB_BM_REQTYPE_TYPE_VENDOR|USB_BM_REQTYPE_DIR_IN, request, length, value, index, timeout)]
        if len(retary):
            return ''.join(retary)
        return ""

    def _sendEP5(self, buf=None, timeout=DEFAULT_USB_TIMEOUT):
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
                numwrt = self._do.bulkWrite(5, drain, timeout)
                if numwrt != len(drain):
                    raise Exception("Didn't write all the data!? Sent: %d != Queued: %d.  REqueuing!(this may be the wrong thing to do, swat me if so)" % (numwrt, len(drain)))
            except Exception, e:
                if self._debug: print >>sys.stderr,"requeuing on error '%s' (%s)" % (repr(drain), e)
                self.xsema.acquire()
                msg = self.xmit_queue.insert(0, drain)
                self.xmit_event.set()
                self.xsema.release()
                if self._debug: print >>sys.stderr, repr(self.xmit_queue)
        
    def _recvEP5(self, timeout=100):
        retary = ["%c"%x for x in self._do.bulkRead(0x85, 500, timeout)]
        if self._debug: print >>sys.stderr,"RECV:"+repr(retary)
        if len(retary):
            return ''.join(retary)
        return ''

    def _clear_buffers(self, clear_recv_mbox=False):
        threadGoSet = self._threadGo.isSet()
        self._threadGo.clear()
        if self._debug:
            print >>sys.stderr,("_clear_buffers()")
        if clear_recv_mbox:
            for key in self.recv_mbox.keys():
                self.trash.extend(self.recvAll(key))
        elif self.recv_mbox.get(APP_SYSTEM) != None:
            self.trash.extend(self.recvAll(APP_SYSTEM))
        self.trash.append((time.time(),self.recv_queue))
        self.recv_queue = ''
        # self.xmit_queue = []          # do we want to keep this?
        if threadGoSet: self._threadGo.set()


    ######## TRANSMIT/RECEIVE THREADING ########
    def runEP5_send(self):
        msg = ''
        self.send_threadcounter = 0

        while True:
            self._threadGo.wait()
            self.send_threadcounter = (self.send_threadcounter + 1) & 0xffffffff

            #### transmit stuff.  if any exists in the xmit_queue
            self.xmit_event.wait() # event driven xmit
            msgsent = False

            try:
                if len(self.xmit_queue):
                    self.xsema.acquire()

                    msg = self.xmit_queue.pop(0)
                    if not len(self.xmit_queue): # if there was only one message
                        self.xmit_event.clear() # clear the queue, within the lock
                    
                    self.xsema.release()

                    self._sendEP5(msg)
                    msgsent = True

                else:
                    if self._debug>3: sys.stderr.write("NoMsgToSend ")
            except:
                sys.excepthook(*sys.exc_info())

    def runEP5_recv(self):
        msg = ''
        self.recv_threadcounter = 0

        while True:
            self._threadGo.wait()
            if self._debug>3: sys.stderr.write(".")

            self.recv_threadcounter = (self.recv_threadcounter + 1) & 0xffffffff
            msgrecv = False

            #### handle debug application
            try:
                q = None
                b = self.recv_mbox.get(APP_DEBUG, None)
                if (b != None):
                    for cmd in b.keys():
                        q = b[cmd]
                        if len(q):
                            buf,timestamp = q.pop(0)
                            if self._debug > 1: print >>sys.stderr,("recvthread: buf length: %x\t\t cmd: %x\t\t(%s)"%(len(buf), cmd, repr(buf)))

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
                                print >>sys.stderr, "DEBUG: (%.3f) 0x%x %d"%(timestamp, struct.unpack("B", buf[4:5])[0], struct.unpack("B", buf[4:5])[0])
                            elif (cmd == DEBUG_CMD_HEX16):
                                #print >>sys.stderr, repr(buf)
                                print >>sys.stderr, "DEBUG: (%.3f) 0x%x %d"%(timestamp, struct.unpack("<H", buf[4:6])[0], struct.unpack("<H", buf[4:6])[0])
                            elif (cmd == DEBUG_CMD_HEX32):
                                #print >>sys.stderr, repr(buf)
                                print >>sys.stderr, "DEBUG: (%.3f) 0x%x %d"%(timestamp, struct.unpack("<L", buf[4:8])[0], struct.unpack("<L", buf[4:8])[0])
                            elif (cmd == DEBUG_CMD_INT):
                                print >>sys.stderr, "DEBUG: (%.3f) %d"%(timestamp, struct.unpack("<L", buf[4:8])[0])
                            else:
                                print >>sys.stderr,('DEBUG COMMAND UNKNOWN: %x (buf=%s)'%(cmd,repr(buf)))

            except:
                sys.excepthook(*sys.exc_info())

            #### receive stuff.
            if self._debug>2: print >> sys.stderr, "recvthread: Doing receiving...",self.ep5timeout
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
                elif ('Connection timed out' in errstr):
                    pass
                elif ('Operation timed out' in errstr):
                    pass
                else:
                    if ('could not release intf' in errstr):
                        if self._debug: print "skipping"
                        pass
                    elif ('No such device' in errstr):
                        self._threadGo.clear()
                        #self.resetup(False) ## THIS IS A PROBLEM.
                        self.reset_event.set()
                        print "===== RESETUP set from recv thread"
                    elif ('Input/output error' in errstr):  # USBerror 5
                        self._threadGo.clear()
                        #self.resetup(False) ## THIS IS A PROBLEM.
                        self.reset_event.set()
                        print "===== RESETUP set from recv thread"

                    else:
                        if self._debug: print "Error in runEP5() (receiving): %s" % errstr
                        if self._debug>2: sys.excepthook(*sys.exc_info())
                    self._usberrorcnt += 1
                pass
            except AttributeError,e:
                if "'NoneType' object has no attribute 'bInterfaceNumber'" in str(e):
                    print "Error: dongle went away.  USB bus problems?"
                    self._threadGo.clear()
                    #self.resetup(False)
                    self.reset_event.set()

            except:
                sys.excepthook(*sys.exc_info())

            if self._debug>2: print >> sys.stderr, "recvthread: Sorting mail..."
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
                        #if self._debug > 2: print >> sys.stderr, "Sorting msg", len(msg), msg.encode("hex")
                        while (msglen>=5):                                      # if not enough to parse length... we'll wait.
                            if not self._recv_time:                             # should be 0 to start and when done with a packet
                                self._recv_time = time.time()
                            app = ord(msg[1])
                            cmd = ord(msg[2])
                            length, = struct.unpack("<H", msg[3:5])

                            if self._debug>1: print>>sys.stderr,("recvthread: app=%x  cmd=%x  len=%x"%(app,cmd,length))

                            if (msglen >= length+5):
                                #### if the queue has enough characters to handle the next message... chop it and put it in the appropriate recv_mbox
                                msg = self.recv_queue[1:length+5]                   # drop the initial '@' and chop out the right number of chars
                                self.recv_queue = self.recv_queue[length+5:]        # chop it out of the queue

                                b = self.recv_mbox.get(app,None)

                                if self.rsema.acquire():                            # THREAD SAFETY DANCE
                                    try:
                                        if (b == None):
                                            b = {}
                                            self.recv_mbox[app] = b
                                    except:
                                        sys.excepthook(*sys.exc_info())
                                    finally:
                                        self.rsema.release()                            # THREAD SAFETY DANCE COMPLETE
                               
                                q = b.get(cmd)

                                if self.rsema.acquire():                            # THREAD SAFETY DANCE
                                    try:
                                        if (q is None):
                                            q = []
                                            b[cmd] = q

                                        q.append((msg, self._recv_time))

                                        # notify receivers that a new msg is available
                                        self.recv_event.set()
                                        self._recv_time = 0                         # we've delivered the current message

                                    except:
                                        sys.excepthook(*sys.exc_info())
                                    finally:
                                        self.rsema.release()                            # THREAD SAFETY DANCE COMPLETE
                               
                            else:            
                                if self._debug>1:     sys.stderr.write('=')

                            msg = self.recv_queue
                            msglen = len(msg)
                            # end of while loop

            except:
                sys.excepthook(*sys.exc_info())

            if self._debug>2: print >> sys.stderr, "readthread: Loop finished"
            if not (msgrecv or len(msg)) :
                #time.sleep(.1)
                self.ep5timeout = EP_TIMEOUT_IDLE
            else:
                self.ep5timeout = EP_TIMEOUT_ACTIVE
                if self._debug > 5:  sys.stderr.write(" %s:%d .-P."%(msgrecv,len(msg)))



    ######## APPLICATION API ########
    def recv(self, app, cmd=None, wait=USB_RX_WAIT):
        '''
        high-level USB EP5 receive.  
        checks the mbox for app "app" and command "cmd" and returns the next one in the queue
        if any of this does not exist yet, wait for a RECV event until "wait" times out.
        RECV events are generated by the low-level recv thread "runEP5_recv()"
        '''
        startTime = time.time()
        self.recv_event.clear() # an event is only interesting if we've already failed to find our message

        while (time.time() - startTime)*1000 < wait:
            try:
                b = self.recv_mbox.get(app)
                if b:
                    if self._debug: print>>sys.stderr, "Recv msg",app,b,cmd
                    if cmd is None:
                        keys = b.keys()
                        if len(keys):
                            cmd = b.keys()[-1] # just grab one.   no guarantees on the order

                if b is not None and cmd is not None:
                    q = b.get(cmd)
                    if self._debug: print >>sys.stderr,"debug(recv) q='%s'"%repr(q)

                    if q is not None and self.rsema.acquire(False):
                        if self._debug>3: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],2
                        try:
                            resp, rt = q.pop(0)

                            self.rsema.release()
                            if self._debug>3: print ("rsema.UNlocked", "rsema.locked")[self.rsema.locked()],2

                            # bring it on home...  this is the way out.
                            return resp[4:], rt

                        except IndexError:
                            pass

                        except AttributeError:
                            sys.excepthook(*sys.exc_info())
                            pass

                        self.rsema.release()

                self.recv_event.wait((wait - (time.time() - startTime)*1000)/1000) # wait on recv event, with timeout of remaining time
                self.recv_event.clear() # clear event, if it's set

            except KeyboardInterrupt:
                sys.excepthook(*sys.exc_info())
                break
            except:
                sys.excepthook(*sys.exc_info())

        raise(ChipconUsbTimeoutException())

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

    def send(self, app, cmd, buf, wait=USB_TX_WAIT):
        msg = "%c%c%s%s"%(app,cmd, struct.pack("<H",len(buf)),buf)
        self.xsema.acquire()
        self.xmit_queue.append(msg)
        self.xmit_event.set()
        self.xsema.release()
        if self._debug: print "Sent Msg",msg.encode("hex")
        return self.recv(app, cmd, wait)

    def reprDebugCodes(self, timeout=100):
        codes = self.getDebugCodes(timeout)
        if (codes != None and len(codes) == 2):
            rc1 = LCS.get(codes[0])
            rc2 = LCES.get(codes[0])
            return 'last position: %s\nlast error: %s' % (rc1, rc2)
        return codes

    def getDebugCodes(self, timeout=100):
        '''
        this function uses EP0 (not the normal USB EP5) to check the last state of the dongle.
        this only works if the dongle isn't in a hard-loop or some other corrupted state
        that neglects usbprocessing.

        two values are returned.  
        the first value is lastCode[0] and represents standard tracking messages (we were <here>)
        the second value is lastCode[1] and represents exception information (writing OUT while buffer in use!)

        messages LC_* and LCE_* (respectively) are defined in both global.h and rflib.chipcon_usb
        '''
        x = self._recvEP0(request=EP0_CMD_GET_DEBUG_CODES, timeout=timeout)
        if (x != None and len(x)==2):
            return struct.unpack("BB", x)
        else:
            return x

    def clearDebugCodes(self):
        retval = self.send(APP_SYSTEM, SYS_CMD_CLEAR_CODES, "  ", 1000)
        return LCES.get(retval)

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
            try:
                r = self._recvEP0(request=2, value=count, length=count, timeout=DEFAULT_USB_TIMEOUT)
                print "PING: %d bytes received: %s"%(len(r), repr(r))
            except ChipconUsbTimeoutException, e:
                r = None
                print "Ping Failed.",e
            if r==None:
                bad+=1
            else:
                good+=1
        return (good,bad)

    def debug(self, delay=1):
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

            x,y,z = select.select([sys.stdin],[],[], delay)
            if sys.stdin in x:
                sys.stdin.read(1)
                break

    def getPartNum(self):
        try:
            r = self.send(APP_SYSTEM, SYS_CMD_PARTNUM, "", 10000)
            r,rt = r
        except ChipconUsbTimeoutException, e:
            r = None
            print "SETUP Failed.",e

        return ord(r)


    def ping(self, count=10, buf="ABCDEFGHIJKLMNOPQRSTUVWXYZ", wait=DEFAULT_USB_TIMEOUT, silent=False):
        good=0
        bad=0
        start = time.time()
        for x in range(count):
            istart = time.time()
            
            try:
                r = self.send(APP_SYSTEM, SYS_CMD_PING, buf, wait)
                r,rt = r
                istop = time.time()
                if not silent:
                    print "PING: %d bytes transmitted, received: %s (%f seconds)"%(len(buf), repr(r), istop-istart)
            except ChipconUsbTimeoutException, e:
                r = None
                if not silent:
                    print "Ping Failed.",e
            if r==None:
                bad+=1
            else:
                good+=1
        stop = time.time()
        return (good,bad,stop-start)

    def bootloader(self):
        '''
        switch to bootloader mode. based on Fergus Noble's CC-Bootloader (https://github.com/fnoble/CC-Bootloader)
        this allows the firmware to be updated via USB instead of goodfet/ccdebugger
        '''
        try:
            self._bootloader = True
            r = self.send(APP_SYSTEM, SYS_CMD_BOOTLOADER, "", wait=1)
        except ChipconUsbTimeoutException:
            pass
        
    def RESET(self):
        try:
            r = self.send(APP_SYSTEM, SYS_CMD_RESET, "RESET_NOW\x00")
        except ChipconUsbTimeoutException:
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
            
    def getCompilerInfo(self):
        r, t = self.send(APP_SYSTEM, SYS_CMD_COMPILER, '')
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

    def reprHardwareConfig(self):
        output= []

        hardware = self.getBuildInfo()
        output.append("Dongle:              %s" % hardware.split(' ')[0])
        try:
            output.append("Firmware rev:        %s" % hardware.split('r')[1])
        except:
            output.append("Firmware rev:        Not found! Update needed!")
        try:
            compiler = self.getCompilerInfo()
            output.append("Compiler:            %s" % compiler)
        except:
            output.append("Compiler:            Not found! Update needed!")
        # see if we have a bootloader by loooking for it's recognition semaphores
        # in SFR I2SCLKF0 & I2SCLKF1
        if(self.peek(0xDF46,1) == '\xF0' and self.peek(0xDF47,1) == '\x0D'):
            output.append("Bootloader:          CC-Bootloader")
        else:
            output.append("Bootloader:          Not installed")
        return "\n".join(output)

    def reprSoftwareConfig(self):
        output= []

        output.append("rflib rev:           %s" % RFLIB_VERSION)
        return "\n".join(output)

    def printClientState(self, width=120):
        print self.reprClientState(width)

    def reprClientState(self, width=120):
        output = ["="*width]
        output.append('     client thread cycles:      %d/%d' % (self.recv_threadcounter,self.send_threadcounter))
        output.append('     client errored cycles:     %d' % self._usberrorcnt)
        output.append('     recv_queue:                (%d bytes) %s'%(len(self.recv_queue),repr(self.recv_queue)[:width-42]))
        output.append('     trash:                     (%d blobs) "%s"'%(len(self.trash),repr(self.trash)[:width-44]))
        output.append('     recv_mbox                  (%d keys)  "%s"'%(len(self.recv_mbox),repr([hex(x) for x in self.recv_mbox.keys()])[:width-44]))
        for app in self.recv_mbox.keys():
            appbox = self.recv_mbox[app]
            output.append('       app 0x%x (%d records)'%(app,len(appbox)))
            for cmd in appbox.keys():
                output.append('             [0x%x]    (%d frames)  "%s"'%(cmd, len(appbox[cmd]), repr(appbox[cmd])[:width-36]))
            output.append('')
        return "\n".join(output)



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


if __name__ == "__main__":
    idx = 0
    if len(sys.argv) > 1:
        idx = int(sys.argv.pop())
    d = USBDongle(idx=idx, debug=False)


