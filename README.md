Welcome to the official rfcat project that works for `PandwaRF` and `PandwaRF Rogue`, modified to also work with legacy rfcat dongles such as `Yard Stick One`.  
See the legacy readme [here](#legacy-readme).  

## How to install RfCat python  

There are multiple ways to install rfcat, including a docker way, but for now, if you are using docker, you won't be able to use the `rfcat -s` feature (the Spectrum Analyser) since it require a GUI (Graphical User Interface).  

### On Linux

- (Recommended) Install using docker and our custom image by simply running `./run_rfcat_docker.sh`
- Install using the [legacy install](#installing-client)

### On Windows

On windows you can use rfcat with `WSL 2` and the `Ubuntu distribution for WSL 2`. You can :  
- (Recommended) Install using `Docker Desktop` by simply running `run_rfcat_docker.bat`
- Install using the [legacy install](#installing-client) of rfcat inside `WSL 2`.

In both cases, after installation, you will need to follow this [guide](https://devblogs.microsoft.com/commandline/connecting-usb-devices-to-wsl/) to expose your PandwaRF / Yard Stick One USB Dongle to the `WSL 2 / Docker instance`. The guide is working on `Windows 10` even if it says you need `Windows 11`.  

## How to use RfCat python without root permissions  

(You don't need to do this if you are using the docker method)  

You may have tried to run `rfcat -r` and saw a `Permission Denied` error, and then simply did `sudo rfcat -r` to make it work, but you can avoid the `sudo` by allowing user access to the RfCat USB Dongles by doing the following:  

```bash
sudo cp etc/udev/rules.d/20-rfcat.rules /etc/udev/rules.d
sudo udevadm control --reload-rules
# Then you may need to reboot to apply changes
```

## How to use RfCat python

After having followed the above guide on how to install the rfcat python client, you can simply type `rfcat -r` to interact with the Dongle. You can also create scripts to use the Dongle, and some example script for the `PandwaRF` are provided in the [examples](./examples/) folder.  
You can also check the [legacy Using rfcat](#using-rfcat) for additional info.




# Legacy Readme

Welcome to the rfcat project

## Table of Contents

- [Legacy Readme](#legacy-readme)
  - [Table of Contents](#table-of-contents)
  - [GOALS](#goals)
  - [REQUIREMENTS](#requirements)
    - [Other requirements](#other-requirements)
    - [Build requirements](#build-requirements)
  - [DEVELOPMENT](#development)
    - [Gotchas](#gotchas)
  - [INSTALLING ON HARDWARE](#installing-on-hardware)
    - [allowing non-root dongle access](#allowing-non-root-dongle-access)
    - [supported dongles](#supported-dongles)
      - [GoodFET](#goodfet)
      - [Chronos Dongle](#chronos-dongle)
      - [EMK Dongle](#emk-dongle)
      - [YARD Stick One](#yard-stick-one)
  - [INSTALLING WITH BOOTLOADER](#installing-with-bootloader)
    - [Steps required for all firmware installs and updates](#steps-required-for-all-firmware-installs-and-updates)
    - [Steps for bootloader + firmware installs via hardware debugger](#steps-for-bootloader--firmware-installs-via-hardware-debugger)
    - [Steps for firmware updates via USB port](#steps-for-firmware-updates-via-usb-port)
  - [Installing client](#installing-client)
    - [Dependencies](#dependencies)
    - [Installation](#installation)
      - [Installation with pip](#installation-with-pip)
  - [Using rfcat](#using-rfcat)
  - [External Projects](#external-projects)
  - [Epilogue](#epilogue)

## GOALS

The goals of the project are to reduce the time for security researchers to create needed tools for analyzing unknown targets, to aid in reverse-engineering of hardware, and to satiate my rf lust.

## REQUIREMENTS

RfCat currently requires Python 2.7.  the only suspected incompatibilities with Python 3.x are minimal, mostly print("stuff") versus print "stuff" and other str/bytes issues.

### Other requirements

* python usb
* libusb - should be able to work with either 1.x or 0.1 versions.  please let us know if you run into issues.
* pyreadline (especially for Windows)
* PySide2 (for Spectrum Analyzer GUI):  (Ubuntu 18.10+: python-pyside2)
    PySide2 is no longer installed automatically, due to support concerns for RPi platforms.  You can install it (if available for your platform) using pip:
    $ sudo pip install PySide2  

### Build requirements

* Make
* SDCC

## DEVELOPMENT

New development efforts should copy the "application.c" file to "appWhateverMyToolIs.c" and attempt to avoid making changes to other files in the repo if at all possible.  that is only a recommendation, because future bug-fixes in other libraries/headers will go much more smoothely for you.

### Gotchas

A couple [gotchas](https://en.wikipedia.org/wiki/Gotcha_(programming)) to keep in mind while developing for the cc1111

* The memory model includes both "RAM" and "XDATA" concepts, and standard RAM variables and XDATA variables have different assembly instructions that are used to access them.  this means that you may find oddities when using a function written for XDATA on a standard RAM variable, and vice-versa.
* Variables should be defined in a single .c file, and then "externs" declared in a .h file that can be included in other modules.  this is pretty standard for c programs, but both this and the previous point caused me difficulties at some points, and i found myself unsure what was causing my troubles.
* RAM memory is not cheap.  use it sparingly.
* You need to set the radio into IDLE mode before reconfiguring it
* You need to set the radio into TX mode *before* writing to the RFD register (firmware) as it is a 1-byte FIFO.


## INSTALLING ON HARDWARE

Installing and getting up to speed with rfcat...

First things first. Using rfcat requires that you either use the python client in root mode (sudo works well), or configure udev to allow non-root users full access to the dongle. you must also have one of the supported dongles flashed with the necessary application firmware.

### allowing non-root dongle access

```
sudo cp etc/udev/rules.d/20-rfcat.rules /etc/udev/rules.d
sudo udevadm control --reload-rules
```
Please make sure any user accounts you want to allow access to the RfCat dongle are members of the `dialout` group.

This tool is created, maintained, and used primarily on linux.  make and sdcc must be installed for creating new firmware and some of the helper functions we provide through make.

### supported dongles

* [YARDStick One](https://greatscottgadgets.com/yardstickone)
* cc1111emk (aka DONSDONGLES)
* chronos watch dongle (aka CHRONOSDONGLE)
* imme (limited support for both IMME and IMMEDONGLE)
    * imme dongle is not really usable as of 1/31/2012



#### GoodFET
  
```

            --------------------------------
            |                         1  2 |
            |                         3  4 |
       ------                         5  6 |  
       | USB                          7  8 |
       ------                         9 10 |
            |                        11 12 |
            | GoodFET                13 14 |
            --------------------------------
```


#### Chronos Dongle

```
            --------------------------------
            |                              |
            |             RST 1  2 TP      ------
            |             GND 3  4 VCC      USB |
            |         DC/P2_2 5  6 DD/P2_1 ------
            | Chronos                      |
            --------------------------------

               GoodFET            Chronos           GreatFET            Chronos
                 PIN                PIN              PIN                  PIN

                  1 <----- DD -----> 6              J1.37 <----- DD -----> 6
                  2 <----- VCC ----> 4               J1.2 <----- VCC ----> 4
                  5 <----- RST ----> 1              J1.40 <----- RST ----> 1
                  7 <----- DC -----> 5              J1.39 <----- DC -----> 5
                  9 <----- GND ----> 3               J1.1 <----- GND ----> 3
```

#### EMK Dongle

```
            --------------------------------
            | 2 4 6 8 10   2 4 6 8 10      |
            | 1 3 5 7 9    1 3 5 7 9       |
            |-TEST-PINS----DEBUG-PINS------|
            |                              |
       ------                              |
       | USB                               |
       ------                              |
            | Don's Dongle (EMK)           |
            --------------------------------

               GoodFET              EMK               GreatFET             EMK  
                 PIN             DEBUG PIN              PIN            DEBUG PIN

                  1 <----- DD -----> 4              J1.37 <----- DD -----> 4
                  2 <----- VCC ----> 2               J1.2 <----- VCC ----> 2
                  5 <----- RST ----> 7              J1.40 <----- RST ----> 7
                  7 <----- DC -----> 3              J1.39 <----- DC -----> 3
                  9 <----- GND ----> 1               J1.1 <----- GND ----> 1
```

#### YARD Stick One

Pogo pads on the back are clearly marked, but if you want to use the header...

```
            -----------------------------------------
            | YARD Stick One      2 4 6 8 10 12 14  |
            |                     1 3 5 7 9  11 13  ------
            |                                        USB |
            |                                       ------
            |                                       |
            -----------------------------------------

    
               GoodFET           YARD Stick One       GreatFET           YARD Stick One
                 PIN                 PIN               PIN                 PIN

                  1 <----- DD -----> 1               J1.37 <----- DD -----> 1
                  2 <----- VCC ----> 2                J1.2 <----- VCC ----> 2
                  5 <----- RST ----> 5               J1.40 <----- RST ----> 5
                  7 <----- DC -----> 7               J1.39 <----- DC -----> 7
                  9 <----- GND ----> 9                J1.1 <----- GND ----> 9
```


## INSTALLING WITH BOOTLOADER

### Steps required for all firmware installs and updates


You will also need to install the build requirements of python-usb, libusb-1.0.0, make, and sdcc.

* python-usb
* libusb-1.0.0
* make
* sdcc

```
sudo apt install python-usb libusb-1.0.0 make sdcc
```

For sdcc and its dependency, sdcc-libraries, you may need to download it from a earlier release's repository if you are on a newer version of Debian or Ubuntu  such as:

* https://packages.debian.org/stretch/sdcc

Next, your user must have read/write access to the dongle when it shows up to the operating system.  
For most Linux distros, this means you have to be a member of the "dialout" group.

```
usermod -a -G sudo $USER
su - $USER
```

You will also need permanent symlinks to the USB serial devices that will communicate with the CHRONOS, DONSDONGLE or YARDSTICKONE
bootloader when required. If you haven't done this step already (see above), then run:

```
sudo cp etc/udev/rules.d/20-rfcat.rules /etc/udev/rules.d
sudo udevadm control --reload-rules
```

### Steps for bootloader + firmware installs via hardware debugger

To prepare your dongle for the first time, you'll need to hook up your debugger as described above 

Intended development model is using a [GoodFET](http://goodfet.sf.net) although one of our developers uses the chipcon debugger from Texas Instruments.

```
cd rfcat/firmware/
make testgoodfet
```

This will read info from your dongle using the GoodFET. you should see something like:

```
SmartRF not found for this chip.
Ident   CC1111/r1103/ps0x0400
Freq         0.000 MHz
RSSI    00
```

* `make backupdongle` will read the current firmware from your dongle to the file `.../bins/original-dongle-hex.backup`.
  (`make restoredongle`) to revert to the original firmware. 
* `make clean installRfCatChronosDongle` will clean, build, and install the RfCat (`appFHSSNIC.c`) firmware for a Chronos dongle.
* `make clean installRfCatDonsDongle` will clean, build, and install the RfCat (`appFHSSNIC.c`) firmware for a cc1111emk.
* `make clean installimmesnifffw` will clean, build, and install the RfSniff firmware for the IMME girls toy from girltech 


Dependencies: Fergus Noble's CC-Bootloader (slightly modified). For your convenience, hex files are provided in 
the CCBootloader sub-directory in firmware. 

Source can be found here
* https://github.com/AdamLaurie/CC-Bootloader

Which is branched from here
* https://github.com/fnoble/CC-Bootloader

and do:

(install `rfcat_bootloader` from the CC-Bootloader subdirectory to somewhere on your execution path)

`cd firmware`

for EMK/DONSDONGLE:
  `make installdonsbootloader`

for CHRONOS:
  `make installchronosbootloader`

for YARDSTICKONE:
  `make installys1bootloader`

now unplug the debugger and plug in your USB dongle.

If you have just installed the bootloader, the dongle should be in bootloader mode, indicated by a solid LED. 

### Steps for firmware updates via USB port

If you are re-flashing a dongle that is already running rfcat firmware, such as a YarstickOne, the Makefile targets will force it into bootloader
mode for you, but you can manually put it into bootloader mode either by holding down the EMK/DONS button as you plug 
it into USB (on the CHRONOS or YARDSTICKONE jumper P2_2/DC to GROUND), or by issuing the command `d.bootloader()` to rfcat in interactive 
mode (`rfcat -r`), or by issuing the command `rfcat --bootloader --force` from the command line.

Once you have a solid LED, or if you're running an rfcat dongle, you can do the following:

`cd firmware`

for EMK/DONSDONGLE:
* `make installRfCatDonsDongleCCBootloader`

for CHRONOS:
* `make installRfCatChronosDongleCCBootloader`

for YARDSTICKONE:
* `make installRfCatYS1CCBootloader`

The new version will be installed, and bootloader exited.

## Installing client

### Dependencies

* python-usb
* libusb

Install rfcat onto your system.  on most linux systems, this will place `rfcat` and `rfcat_server` in `/usr/local/bin/` and `rflib` into `/usr/*/lib/python2.x/dist-packages`

### Installation

* cd into the rfcat directory (created by unpacking the tarball or by git clone)
* sudo python setup.py install
* I highly recommend installing `ipython`
  * For deb/ubuntu folk: `apt-get install ipython`

#### Installation with pip
* cd into the rfcat directory (created by unpacking the tarball or by git clone)
* ```pip install -e .```  (installs in editable mode and runs from the unpacked or checked out location)

## Using rfcat

If you have configured your system to allow non-root use:

* type "rfcat -r"   (if your system is not configured to allow non-root use, prepend "sudo" or you must run as root)
    you should have now entered an interactive python shell, where tab-completion and other aids should make a very powerful experience
    i love the raw-byte handling and introspection of it all.

* try things like:
    * d.ping()
    * d.discover()
    * d.debug()
    * d.RFxmit('blahblahblah')
    * d.RFrecv()
    * print(d.reprRadioConfig())
    * d.setMdmDRate(19200)      # this sets the modem baud rate (or DataRate)
    * d.setPktPQT(0)            # this sets the preamble quality threshold to 0
    * d.setEnableMdmFEC(True)   # enables the convolutional Forward Error Correction built into the radio


while the toolset was created to make communicating with <ghz much easier, you will find the cc1111 manual from ti a great value.  the better you understand the radio, the better your experience will be.
play with the radio settings, but i recommend playing in small amounts and watch for the effects.  several things in the radio configuration settings are mandatory to get right in order to receive or transmit anything (one of those odd requirements is the TEST2/1/0 registers!)

If you watched any of my talks on rfcat, you will likely remember that you need to put the radio in **IDLE state** before configuring. (I said it three times, in a row, in different inflections).

However, you will find that I've done that for you in the client for most things.  The only time you need to do this yourself are:
    * If you are doing the changes in firmware
    * If you are using the "d.poke()" functionality
        * if you use "d.setRFRegister()", this is handled for you
        * `use d.setRFRegister()`

## External Projects
[ZWave Attack](https://www.initbrain.fr/security/2016/z-attack/):  [https://github.com/initbrain/Z-Attack](https://github.com/initbrain/Z-Attack)

## Epilogue

Other than that, hack fun, and feel free to share any details you can about successes and questions about failures you are able!

@ and the rest of the development team.

