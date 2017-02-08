#!/usr/bin/python

import sys
from rflib.intelhex import IntelHex

WRITEBACK = True
if len(sys.argv) > 1:
    WRITEBACK = False
    ser = int(sys.argv[1])
else:
    try:
        ser = int(file(".serial", 'rb').read(), 16) + 1
    except IOError:
        ser = 0

print >>sys.stderr,("[--- new serial number: %.4x ---]" % ser)

if WRITEBACK:
    file(".serial", 'wb').write("%.13x" % ser)

sertxt = ''
sertmp = "%.13x" % ser
for c in sertmp:
    sertxt += "%s\x00" % c

ihc=IntelHex('CCBootloader/CCBootloader-rfcat-chronosdongle.hex')
ihd=IntelHex('CCBootloader/CCBootloader-rfcat-donsdongle.hex')
ihy=IntelHex('CCBootloader/CCBootloader-rfcat-ys1.hex')
ihc.puts(0x13e0, "@las\x1c\x03" + sertxt)
ihd.puts(0x13e0, "@las\x1c\x03" + sertxt)
ihy.puts(0x13e0, "@las\x1c\x03" + sertxt)
ihc.write_hex_file('CCBootloader/CCBootloader-rfcat-chronosdongle-serial.hex')
ihd.write_hex_file('CCBootloader/CCBootloader-rfcat-donsdongle-serial.hex')
ihy.write_hex_file('CCBootloader/CCBootloader-rfcat-ys1-serial.hex')

