import sys
import os
import codecs
import setuptools

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
    REV = os.popen('./revision.sh').readline().encode('UTF-8')
    if len(REV):
        open('rflib/rflib_version.py', 'wb').write(b"RFLIB_VERSION=%s" % REV)
except:
    sys.excepthook(*sys.exc_info())

requirements = open('requirements.txt').read().split('\n')


# Readme function to show readme as a desription in pypi
def readme():
    with codecs.open('README.rst', encoding='utf-8') as f:
        return f.read()


setuptools.setup  (name  = 'rfcat',
        version          = '1.9.2',
        description      = "the swiss army knife of subGHz",
        long_description = readme(),
        author           = 'atlas of d00m',
        author_email     = 'atlas@r4780y.com',
        url              = 'https://github.com/atlas0fd00m/rfcat',
        download_url     = 'https://github.com/atlas0fd00m/rfcat/archive/v1.9.1.tar.gz',
        keywords         = ['radio', 'subghz', 'cc1111', 'chipcon', 'hacking', 'reverse engineering'],
        packages         = setuptools.find_packages(),
        package_data     = pkgdata,
        ext_modules      = mods,
        scripts          = scripts,
        install_requires = requirements,
        classifiers      = [
                            # How mature is this project? Common values are
                            #   3 - Alpha
                            #   4 - Beta
                            #   5 - Production/Stable
                            'Development Status :: 5 - Production/Stable',

                            # Indicate who your project is intended for: See info here: https://pypi.python.org/pypi/classifiers
                            'Intended Audience :: Telecommunications Industry',
                            'Topic :: Communications',

                            # Pick your license as you wish (should match "license" above)
                             'License :: OSI Approved :: BSD License',

                            # Specify the Python versions you support here. In particular, ensure
                            # that you indicate whether you support Python 2, Python 3 or both.
                            'Programming Language :: Python :: 2',
                            'Programming Language :: Python :: 2.7',
                            'Programming Language :: Python :: 3',
                            'Programming Language :: Python :: 3.8',
                            #'Operating System :: OS Indepentent',
                           ],
        python_requires  = '>=2.7'
        )
