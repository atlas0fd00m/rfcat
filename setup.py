import sys
import os
from distutils.core import setup, Extension

packages = ['rflib', 'vstruct', 'vstruct.defs']
mods = []
pkgdata = {}
scripts = ['rfcat', 'rfcat_server', 'CC-Bootloader/bootload.py',
        ]

# store the HG revision in an rflib python file
REV = int(os.popen('hg parent --template "{rev}"').readline())
file('rflib/rflib_version.py', 'wb').write( "RFLIB_VERSION=%d" % REV)

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


