#!/usr/bin/python
import sys

sn_header = """// Serial number
               10,                      // bLength
               USB_DESC_STRING,         // bDescriptorType
"""

try:
    ser = int(file(".serial", 'rb').read(), 16) #+ 1
except IOError:
    ser = 0

print >>sys.stderr,("[--- new serial number: %.4x ---]" % ser)

file(".serial", 'wb').write("%.4x" % ser)
sertxt = "%.4x" % ser

for c in sertxt:
    n = ord(c)
    sys.stdout.write("%s,0," % n)

