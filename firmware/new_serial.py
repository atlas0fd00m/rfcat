#!/usr/bin/python
import sys

sn_header = """// Serial number
               10,                      // bLength
               USB_DESC_STRING,         // bDescriptorType
"""

try:
    ser = int(file(".serial", 'rb').read()) + 1
except IOError:
    ser = 0

print >>sys.stderr,("[--- new serial number: %.4d ---]" % ser)

file(".serial", 'wb').write("%.4d" % ser)
sertxt = "%.4d" % ser

for c in sertxt:
    sys.stdout.write("'%s',0," % c)

