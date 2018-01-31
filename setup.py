import sys
import os
import codecs
from distutils.core import setup, Extension

packages = ['rflib', 'vstruct', 'vstruct.defs']
mods = []
pkgdata = {}
scripts = ['rfcat',
           'rfcat_server',
           'rfcat_msfrelay',
           'CC-Bootloader/rfcat_bootloader',
           ]

# store the HG revision in an rflib python file
try:
    REV = os.popen('./revision.sh').readline()
    if len(REV):
        file('rflib/rflib_version.py', 'wb').write("RFLIB_VERSION=%s" % REV)
except:
    sys.excepthook(*sys.exc_info())


# Readme function to show readme as a desription in pypi
def readme():
    with codecs.open('README.rst', encoding='utf-8') as f:
        return f.read()


setup  (name             = 'rfcat',
        version          = '1.0.1',
        description      = "the swiss army knife of subGHz",
        long_description = readme(),
        author           = 'atlas of d00m',
        author_email     = 'atlas@r4780y.com',
        url              = 'https://github.com/atlas0fd00m/rfcat',
        download_url     = 'https://github.com/atlas0fd00m/rfcat/archive/1.0.1.tar.gz',
        keywords         = ['radio', 'subghz'],
        #include_dirs = [],
        packages         = packages,
        package_data     = pkgdata,
        ext_modules      = mods,
        scripts          = scripts,
        classifiers      = [
                            # How mature is this project? Common values are
                            #   3 - Alpha
                            #   4 - Beta
                            #   5 - Production/Stable
                            'Development Status :: 3 - Alpha',

                            # Indicate who your project is intended for: See info here: https://pypi.python.org/pypi/classifiers
                            'Intended Audience :: Telecommunications Industry',
                            'Topic :: Communications',

                            # Pick your license as you wish (should match "license" above)
                             'License :: OSI Approved :: BSD License',

                            # Specify the Python versions you support here. In particular, ensure
                            # that you indicate whether you support Python 2, Python 3 or both.
                            'Programming Language :: Python :: 2',
                            'Programming Language :: Python :: 2.6',
                            'Programming Language :: Python :: 2.7',
                            # 'Programming Language :: Python :: 3',
                            # 'Programming Language :: Python :: 3.2',
                            # 'Programming Language :: Python :: 3.3',
                            # 'Programming Language :: Python :: 3.4',
                           ],
        install_requires = ['pyusb>=1.0.0', 'libusb>=1.0.21b2', 'PySide==1.2.2'],
        python_requires  = '>2.0,<3.0.0'
        )
