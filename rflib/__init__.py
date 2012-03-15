#!/usr/bin/env ipython
from chipcon_nic import *

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
            print
            for freq in xrange(int(basefreq), int(basefreq+(inc*count)), int(inc)):
                print "Scanning for frequency %d..." % freq
                self.setFreq(freq)
                self.RFdump(timeoutms=delaysec*1000)
                if keystop():
                    break

        self.lowballRestore()

if __name__ == "__main__":
    idx = 0
    if len(sys.argv) > 1:
        idx = int(sys.argv.pop())
    d = RfCat(idx=idx)

