#!/usr/bin/env ipython
from chipcon_nic import *

RFCAT_START_SPECAN  = 0x40
RFCAT_STOP_SPECAN   = 0x41

class RfCat(FHSSNIC):
    def RFdump(self, msg="Receiving", maxnum=100, timeoutms=1000):
        try:
            for x in xrange(maxnum):
                y, t = self.RFrecv(timeoutms)
                print "(%5.3f) %s:  %s" % (t, msg, y.encode('hex'))
        except ChipconUsbTimeoutException:
            pass

    def scan(self, basefreq=902e6, inc=250e3, count=104, delaysec=2, drate=38400, lowball=1):
        '''
        scan for signal over a range of frequencies
        '''
        self.RFdump("Clearing")
        self.lowball(lowball)
        self.setMdmDRate(drate)
        print "Scanning range: "
        while not keystop():
            try:
                print
                for freq in xrange(int(basefreq), int(basefreq+(inc*count)), int(inc)):
                    print "Scanning for frequency %d..." % freq
                    self.setFreq(freq)
                    self.RFdump(timeoutms=delaysec*1000)
                    if keystop():
                        break
            except KeyboardInterrupt:
                print "Please press <enter> to stop"

        sys.stdin.read(1)
        self.lowballRestore()

    def specan(self, basefreq=902e6, inc=250e3, count=104):
        freq, delta = self._doSpecAn(basefreq, inc, count)

        import rflib.ccspecan as rfspecan
        if not hasattr(self, "_qt_app") or self._qt_app is None:
            self._qt_app = rfspecan.QtGui.QApplication([])

        fhigh = freq + (delta*(count+1))

        window = rfspecan.Window(self, freq, fhigh, delta, 0)
        window.show()
        self._qt_app.exec_()
        
    def _doSpecAn(self, basefreq, inc, count):
        '''
        store radio config and start sending spectrum analysis data
        '''
        if count>255:
            raise Exception("sorry, only 255 samples per pass... (count)")
        self.getRadioConfig()
        self._specan_backup_radiocfg = self.radiocfg

        self.setFreq(basefreq)
        self.setMdmChanSpc(inc)

        freq, fbytes = self.getFreq()
        delta = self.getMdmChanSpc()

        self.send(APP_NIC, RFCAT_START_SPECAN, "%c" % (count) )
        return freq, delta

    def _stopSpecAn(self):
        ''' 
        stop sending rfdata and return radio to original config
        '''
        self.send(APP_NIC, RFCAT_STOP_SPECAN, '')
        self.radiocfg = self._specan_backup_radiocfg
        self.setRadioConfig()


    def rf_configure(*args, **k2args):
        pass

    def rf_redirection(self, fdtup):
        if len(fdtup)>1:
            fd0i, fd0o = fdtup 
        else:
            fd0i, = fdtup 
            fd0o, = fdtup 

        fdsock = False      # socket or fileio?
        if hasattr(fd0i, 'recv'):
            fdsock = True

        while True:
            x,y,z = select.select([fd0i ], [], [], .1)
            #if self._pause:
            #    continue

            if fd0i in x:
                if fdsock:
                    data = fd0i.recv(self.max_packet_size)
                else:
                    data = fd0i.read(self.max_packet_size)

                if not len(data):       # terminated socket
                    break

                self.RFxmit(data)

            try:
                data = self.RFrecv(0)
                if fdsock:
                    fd0o.sendall(data)
                else:
                    fd0o.write(data)
            except ChipconUsbTimeoutException:
                pass

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

    try:
        import IPython.Shell
        ipsh = IPython.Shell.IPShell(argv=[''], user_ns=lcls, user_global_ns=gbls)
        print intro
        ipsh.mainloop(intro)

    except ImportError, e:
        try:
            from IPython.frontend.terminal.interactiveshell import TerminalInteractiveShell
            ipsh = TerminalInteractiveShell()
            ipsh.user_global_ns.update(gbls)
            ipsh.user_global_ns.update(lcls)
            ipsh.autocall = 2       # don't require parenthesis around *everything*.  be smart!
            ipsh.mainloop(intro)
        except ImportError, e:
            print e
            shell = code.InteractiveConsole(gbls)
            shell.interact(intro)


if __name__ == "__main__":
    idx = 0
    if len(sys.argv) > 1:
        idx = int(sys.argv.pop())

    interactive(idx)
