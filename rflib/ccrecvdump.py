#!/usr/bin/python
import sys, serial

port = "ACM0"
if len(sys.argv) > 1:
    port = sys.argv.pop()

dport = "/dev/tty" + port

print "Opening serial port %s for listening..." % dport
s=serial.Serial(dport, 115200)

counter = 0
while True:
    print ("%d: %s" % (counter, repr(s.read(12))))
    counter += 1
    #sys.stdout.write(s.read(1))
    #sys.stdout.flush()
