#!/usr/bin/env python
from __future__ import print_function
import sys

sn_header = """// Serial number
               10,                      // bLength
               USB_DESC_STRING,         // bDescriptorType
"""

try:
    f = open('.serial', 'r')
    ser = int(f.read(), 16) #+ 1
    f.close()
except IOError:
    ser = 0

print("[--- new serial number: %.4x ---]" % ser, file=sys.stderr)

f = open('.serial', 'w')
f.write("%.4x" % ser)
f.close()

sertxt = "%.4x" % ser

for c in sertxt:
    n = ord(c)
    sys.stdout.write("%s,0," % n)

