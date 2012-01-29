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

print("[--- new serial number: %.4d ---]" % ser)

file(".serial", 'wb').write("%.4d" % ser)
sertxt = "%.4d" % ser

sf = file("cc1111usb.c", 'r+')
sfile = sf.read()
idx = sfile.find('// Serial number')
eos = sfile.find('// END OF STRINGS')

sf.seek(idx)
sf.write(sn_header)

for c in sertxt:
    sf.write("              '%s', 0,\n" % c)

sf.write(" "*(eos-sf.tell()-1))
sf.write('\n')

sf.close()
