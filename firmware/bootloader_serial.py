#!/usr/bin/python

import sys
from intelhex import IntelHex

if len(sys.argv) > 1:
    ser = int(sys.argv[1])
else:
    try:
        ser = int(file(".serial", 'rb').read()) + 1
    except IOError:
        ser = 0

print >>sys.stderr,("[--- new serial number: %.4d ---]" % ser)

if len(sys.argv) < 2:
    file(".serial", 'wb').write("%.11d" % ser)

sertxt = "%.10d" % ser

ihc=IntelHex('CCBootloader/CCBootloader-rfcat-chronosdongle.hex')
ihd=IntelHex('CCBootloader/CCBootloader-rfcat-donsdongle.hex')
ihc.puts(0x13f0, "@las\x0a\x03" + sertxt)
ihd.puts(0x13f0, "@las\x0a\x03" + sertxt)
ihc.write_hex_file('CCBootloader/CCBootloader-rfcat-chronosdongle-serial.hex')
ihd.write_hex_file('CCBootloader/CCBootloader-rfcat-donsdongle-serial.hex')

