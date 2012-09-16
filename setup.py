import sys
import os
from distutils.core import setup, Extension

packages = ['rflib', 'vstruct', 'vstruct.defs']
mods = []
pkgdata = {}
scripts = ['rfcat', 'rfcat_server',
        ]

os.system('echo -n "RFLIB_VERSION=" > rflib/rflib_version.py')
os.system('hg parent --template "{rev}" >> rflib/rflib_version.py')
os.system('echo >> rflib/rflib_version.py')

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


