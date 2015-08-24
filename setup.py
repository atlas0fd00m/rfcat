import sys
import os
from distutils.core import setup, Extension

packages = ['rflib', 'vstruct', 'vstruct.defs']
mods = []
pkgdata = {}
scripts = ['rfcat', 'rfcat_server', 'CC-Bootloader/rfcat_bootloader',
        ]

# store the HG revision in an rflib python file
try:
    REV = os.popen('./revision.sh').readline()
    if len(REV):
        file('rflib/rflib_version.py', 'wb').write( "RFLIB_VERSION=%s" % REV)
except:
    sys.excepthook(*sys.exc_info())

setup  (name        = 'rfcat',
        version     = '1.0',
        description = "the swiss army knife of subGHz",
        author = 'atlas of d00m',
        author_email = 'atlas@r4780y.com',
        #include_dirs = [],
        packages  = packages,
        package_data = pkgdata,
        ext_modules = mods,
        scripts = scripts
       )


