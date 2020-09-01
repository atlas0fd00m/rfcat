#!/usr/bin/env ipython3 -i --no-banner

from __future__ import print_function
from __future__ import absolute_import

from builtins import str
from builtins import range
from .chipcon_nic import *
import rflib.bits as rfbits

RFCAT_START_SPECAN  = 0x40
RFCAT_STOP_SPECAN   = 0x41

MAX_FREQ = 936e6

class RfCat(FHSSNIC):
    def RFdump(self, msg="Receiving", maxnum=100, timeoutms=1000):
        try:
            for x in range(maxnum):
                y, t = self.RFrecv(timeoutms)
                print("(%5.3f) %s:  %s" % (t, msg, hexlify(y)))
        except ChipconUsbTimeoutException:
            pass

    def scan(self, basefreq=902e6, inc=250e3, count=104, delaysec=2, drate=38400, lowball=1):
        '''
        scan for signal over a range of frequencies
        '''
        self.RFdump("Clearing")
        self.lowball(lowball)
        self.setMdmDRate(drate)
        print("Scanning range:  ")
        while not keystop():
            try:
                print("(press Enter to quit)")
                for freq in range(int(basefreq), int(basefreq+(inc*count)), int(inc)):
                    print("Scanning for frequency %d..." % freq)
                    self.setFreq(freq)
                    self.RFdump(timeoutms=delaysec*1000)
                    if keystop():
                        break
            except KeyboardInterrupt:
                print("Please press <enter> to stop")

        sys.stdin.read(1)
        self.lowballRestore()

    def specan(self, centfreq=915e6, inc=250e3, count=104):
        '''
        Enter Spectrum Analyzer mode.
        this sets the mode of the dongle to send data, and brings up the GUI.

        centfreq is the center frequency
        '''
        freq, delta = self._doSpecAn(centfreq, inc, count)

        import rflib.ccspecan as rfspecan
        rfspecan.ensureQapp()

        fhigh = freq + (delta*(count+1))

        window = rfspecan.Window(self, freq, fhigh, delta, 0)
        window.show()
        rfspecan._qt_app.exec_()
        
    def _doSpecAn(self, centfreq, inc, count):
        '''
        store radio config and start sending spectrum analysis data
        
        centfreq = Center Frequency
        '''
        if count>255:
            raise Exception("sorry, only 255 samples per pass... (count)")

        spectrum = (count * inc) 
        halfspec = spectrum / 2.0
        basefreq = centfreq - halfspec
        if (count * inc) + basefreq > MAX_FREQ:
            raise Exception("Sorry, %1.3f + (%1.3f * %1.3f) is higher than %1.3f" %
                    (basefreq, count, inc))
        self.getRadioConfig()
        self._specan_backup_radiocfg = self.radiocfg

        self.setFreq(basefreq)
        self.setMdmChanSpc(inc)

        freq, fbytes = self.getFreq()
        delta = self.getMdmChanSpc()

        self.send(APP_NIC, RFCAT_START_SPECAN, b"%c" % (count) )
        return freq, delta

    def _stopSpecAn(self):
        ''' 
        stop sending rfdata and return radio to original config
        '''
        self.send(APP_NIC, RFCAT_STOP_SPECAN, '')
        self.radiocfg = self._specan_backup_radiocfg
        self.setRadioConfig()


    def rf_configure(self, *args, **kwargs):
        self.setRFparameters(*args, **kwargs)

    def rf_redirection(self, fdtup, use_rawinput=False, printable=False):
        buf = b''

        if len(fdtup)>1:
            fd0i, fd0o = fdtup 
        else:
            fd0i, = fdtup 
            fd0o, = fdtup 

        fdsock = False      # socket or fileio?
        if hasattr(fd0i, 'recv'):
            fdsock = True

        try:
            while True:
                #if self._pause:
                #    continue

                try:
                    x,y,z = select.select([fd0i ], [], [], .1)
                    if fd0i in x:
                        # FIXME: make this aware of VLEN/FLEN and the proper length
                        if fdsock:
                            data = fd0i.recv(self.max_packet_size)
                        else:
                            data = fd0i.read(self.max_packet_size)

                        if not len(data):       # terminated socket
                            break

                        buf += data
                        pktlen, vlen = self.getPktLEN()
                        if vlen:
                            pktlen = ord(buf[0])

                        #FIXME: probably want to take in a length struct here and then only send when we have that many bytes...
                        data = buf[:pktlen]
                        if use_rawinput:
                            data = eval('"%s"'%data)

                        if len(buf) >= pktlen:
                            self.RFxmit(data)

                except ChipconUsbTimeoutException:
                    pass

                try:
                    data, time = self.RFrecv(1)

                    if printable:
                        data = "\n"+str(time)+": "+repr(data)
                    else:
                        data = struct.pack("<L", time) + struct.pack("<H", len(data)) + data

                    if fdsock:
                        fd0o.sendall(data)
                    else:
                        fd0o.write(data)

                except ChipconUsbTimeoutException:
                    pass

                #special handling of specan dumps...  somewhat set in solid jello
                try:
                    data, time = self.recv(APP_SPECAN, 1, 1)
                    data = struct.pack("<L", time) + struct.pack("<H", len(data)) + data
                    if fdsock:
                        fd0o.sendall(data)
                    else:
                        fd0o.write(data)

                except ChipconUsbTimeoutException:
                    #print "this is a valid exception, run along... %x"% APP_SPECAN
                    pass

        except KeyboardInterrupt:
            self.setModeIDLE()

class InverseCat(RfCat):
    def setMdmSyncWord(self, word, radiocfg=None):
        FHSSNIC.setMdmSyncWord(self, word ^ 0xffff, radiocfg)

    def RFrecv(self, timeout=1000):
        global data
        data,timestamp = RfCat.RFrecv(self, timeout)
        return rfbits.invertBits(data),timestamp

    def RFxmit(self, data):
        return RfCat.RFxmit(self, rfbits.invertBits(data) )

def cleanupInteractiveAtExit():
    try:
        if d.getDebugCodes():
           d.setModeIDLE()
        pass
    except:
        pass

def interactive(idx=0, DongleClass=RfCat, intro=''):
    global d
    import rflib.chipcon_nic as rfnic
    import atexit

    d = DongleClass(idx=idx)
    d.setModeRX()       # this puts the dongle into receive mode
    atexit.register(cleanupInteractiveAtExit)

    gbls = globals()
    lcls = locals()

    shellfailed = False

    try:
        from IPython.terminal.interactiveshell import TerminalInteractiveShell
        ipsh = TerminalInteractiveShell()
        ipsh.user_global_ns.update(gbls)
        ipsh.user_global_ns.update(lcls)
        ipsh.autocall = 2       # don't require parenthesis around *everything*.  be smart!
        print(intro)
        ipsh.mainloop()
    except ImportError as e:
        shellfailed = True

    if shellfailed:
        try:
            import IPython.Shell
            ipsh = IPython.Shell.IPShell(argv=[''], user_ns=lcls, user_global_ns=gbls)
            print(intro)
            ipsh.mainloop()

        except ImportError as e:
            shellfailed = True

    if shellfailed:
        try:
            from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell
            ipsh = TerminalInteractiveShell()
            ipsh.user_global_ns.update(gbls)
            ipsh.user_global_ns.update(lcls)
            ipsh.autocall = 2       # don't require parenthesis around *everything*.  be smart!

            print(intro)
            ipsh.mainloop()
        except ImportError as e:
            shellfailed = True

    if shellfailed:
        print("falling back to straight Python... (%r)" % e)
        shell = code.InteractiveConsole(gbls)
        print(intro)
        shell.interact()


if __name__ == "__main__":
    idx = 0
    if len(sys.argv) > 1:
        idx = int(sys.argv.pop())

    interactive(idx)
