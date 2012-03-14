import sys
import os
from distutils.core import setup, Extension

packages = ['clients.rfcat']
mods = []
pkgdata = {}
scripts = []
for s in os.listdir('scripts'):
    if s != '.svn':
            scripts.append('scripts/%s'%s)


setup  (name        = 'rfcat',
        version     = '1.0',
        description = "the swiss army knife of subGHz",
        author = 'atlas of d00m',
        author_email = 'atlas@r4780y.com',
        #include_dirs = ['psyco','PyElf-0.8',],
        packages  = packages,
        package_data = pkgdata,
        ext_modules = mods,
        scripts = scripts
       )

