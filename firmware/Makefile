CC=sdcc
CFLAGS=-Iinclude
CFLAGSold=--no-pack-iram $(CF)
LFLAGS=--xram-loc 0xF000 

apps = cc1111rf.rel global.rel
appsc = cc1111rf.relc global.relc
appsd = cc1111rf.reld global.reld
appsi = cc1111rf.reli global.reli
appsid = cc1111rf.relid global.relid

libsvcom = $(apps) cc1111_vcom.rel cc1111_vcomdesc.rel cc1111usbdebug.rel #cc1111usb.rel
libsvcomc = $(appsc) cc1111_vcom.relc cc1111_vcomdesc.relc cc1111usbdebug.relc #cc1111usb.rel
libsvcomd = $(appsd) cc1111_vcom.reld cc1111_vcomdesc.reld cc1111usbdebug.reld #cc1111usb.rel
libsvcomi = $(appsi) cc1111_vcom.reli cc1111_vcomdesc.reli cc1111usbdebug.reli #cc1111usb.rel

libsusb  = $(apps) cc1111usb.rel cc1111usbdebug.rel
libsusbc  = $(appsc) cc1111usb.rc cc1111usbdebug.relc
libsusbd  = $(appsd) cc1111usb.rd cc1111usbdebug.reld
libsusbi  = $(appsi) immeusb.reli immeusbdebug.reli

libsimme  = $(appsi) immeio.reli immekeys.reli immefont.reli   #  immedisplay.rel immeterm.rel
libsimmed  = $(appsid) immeio.relid immekeys.relid immefont.relid   #  immedisplay.rel immeterm.rel
libsi  = $(apps) immeio.rel immekeys.rel immefont.rel   #  immedisplay.rel immeterm.rel
#srcs = $(libs,.rel=.c) 


all: chronosapplication.hex
donfw: donsapplication.hex
immefw: immeapplication.hex
testrecv: testrecvapplication.hex
testxmit: testxmitapplication.hex


cc1111usb.rc : cc1111usb.c
	./new_serial.py
	$(CC) $(CFLAGS) -DCHRONOSDONGLE -c cc1111usb.c

cc1111usb.rd : cc1111usb.c
	./new_serial.py
	$(CC) $(CFLAGS) -DDONSDONGLES -c cc1111usb.c

%.relc : %.c
	$(CC) $(CFLAGS) -DCHRONOSDONGLE -c $<

%.reld : %.c
	$(CC) $(CFLAGS) -DDONSDONGLES -c $<

%.reli : %.c
	$(CC) $(CFLAGS) -DIMME -c $<

%.relid : %.c
	$(CC) $(CFLAGS) -DIMME -DIMMEDONGLE -c $<

chronosapplication.hex: application.c $(libsusbc)
	sdcc $(CFLAGS) $(LFLAGS) application.c $(libsusb) -DCHRONOSDONGLE
	packihx <application.ihx >bins/application.hex

donsapplication.hex: application.c $(libsusbd)
	sdcc $(CFLAGS) $(LFLAGS) application.c $(libsusb) -DDONSDONGLES
	packihx <application.ihx >bins/application.hex

chronostestusbonly.hex: usbonly.c cc1111usb.rc global.relc
	sdcc $(CFLAGS) $(LFLAGS) usbonly.c cc1111usb.rel global.rel -DCHRONOSDONGLE
	packihx <usbonly.ihx >bins/usbonly.hex

donstestusbonly.hex: usbonly.c cc1111usb.rc global.reld
	sdcc $(CFLAGS) $(LFLAGS) usbonly.c cc1111usb.rel global.rel -DDONSDONGLES
	packihx <usbonly.ihx >bins/usbonly.hex

#	may be helpful when we actually have one...
#immedongleapplication.hex: application.c $(libsusbi)
#	sdcc $(CFLAGS) $(LFLAGS) application.c $(libsusb) -DIMMEDONGLE -DIMME
#	packihx <application.ihx >bins/application.hex
#
chronosNIC.hex: appNIC.c $(libsusbc)
	sdcc $(CFLAGS) $(LFLAGS) appNIC.c $(libsusb) -DCHRONOSDONGLE
	packihx <appNIC.ihx >bins/chronosNIC.hex

chronosFHSS.hex: appFHSSNIC.c $(libsusbc)
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) -DCHRONOSDONGLE
	packihx <appFHSSNIC.ihx >bins/chronosFHSS.hex

donsNIC.hex: appNIC.c $(libsusbd)
	sdcc $(CFLAGS) $(LFLAGS) appNIC.c $(libsusb) -DDONSDONGLES
	packihx <appNIC.ihx >bins/donsNIC.hex

donsFHSS.hex: appFHSSNIC.c $(libsusbd)
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) -DDONSDONGLES
	packihx <appFHSSNIC.ihx >bins/donsFHSS.hex

chronosSniff.hex: appSniff.c $(libsusbc)
	sdcc $(CFLAGS) $(LFLAGS) appSniff.c $(libsusb) -DCHRONOSDONGLE
	packihx <appSniff.ihx >bins/chronosSniff.hex

donsSniff.hex: appSniff.c $(libsusbd)
	sdcc $(CFLAGS) $(LFLAGS) appSniff.c $(libsusb) -DCHRONOSDONGLE
	packihx <appSniff.ihx >bins/donsSniff.hex

immeSniff.hex: appSniff.c $(libsimme) 
	sdcc $(CFLAGS) $(LFLAGS) appSniff.c $(libsi) -DIMME
	packihx <appSniff.ihx >bins/immeSniff.hex

chronostestxmitusb.hex: appNetworkTest.c $(libsusbc)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) -DCHRONOSDONGLE -DTRANSMIT_TEST 
	packihx <appNetworkTest.ihx >bins/testxmit.hex

donstestxmitusb.hex: appNetworkTest.c $(libsusbd)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) -DDONSDONGLES -DTRANSMIT_TEST 
	packihx <appNetworkTest.ihx >bins/testxmit.hex

chronostestrecvusb.hex: appNetworkTest.c $(libsusbc)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) -DCHRONOSDONGLE -DRECEIVE_TEST
	packihx <appNetworkTest.ihx >bins/testrecv.hex

donstestrecvusb.hex: appNetworkTest.c $(libsusbd)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) -DDONSDONGLES -DRECEIVE_TEST
	packihx <appNetworkTest.ihx >bins/testrecv.hex

testxmitapplication.hex: appNetworkTest.c $(libsvcomc)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsvcom) -DCHRONOSDONGLE -DVIRTUAL_COM -DTRANSMIT_TEST 
	packihx <appNetworkTest.ihx >bins/testxmit.hex

testrecvapplication.hex: appNetworkTest.c $(libsvcomc)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsvcom) -DCHRONOSDONGLE -DVIRTUAL_COM -DRECEIVE_TEST
	packihx <appNetworkTest.ihx >bins/testrecv.hex



installchronosfw: chronosapplication.hex
	goodfet.cc erase
	goodfet.cc flash bins/application.hex
	goodfet.cc info

installdonfw: donsapplication.hex
	goodfet.cc erase
	goodfet.cc flash bins/application.hex
	goodfet.cc info

#installimmefw: immedongleapplication.hex
#	goodfet.cc erase
#	goodfet.cc flash bins/application.hex
#	goodfet.cc info

installchronosnicfw: chronosNIC.hex
	goodfet.cc erase
	goodfet.cc flash bins/chronosNIC.hex
	goodfet.cc info

installchronosfhssnicfw: chronosFHSS.hex
	goodfet.cc erase
	goodfet.cc flash bins/chronosFHSS.hex
	goodfet.cc info

installdonsnicfw: donsNIC.hex
	goodfet.cc erase
	goodfet.cc flash bins/donsNIC.hex
	goodfet.cc info

installdonsfhssnicfw: donsFHSS.hex
	goodfet.cc erase
	goodfet.cc flash bins/donsFHSS.hex
	goodfet.cc info

installchronossnifffw: chronosSniff.hex
	goodfet.cc erase
	goodfet.cc flash bins/chronosSniff.hex
	goodfet.cc info

installdonssnifffw: donsSniff.hex
	goodfet.cc erase
	goodfet.cc flash bins/donsSniff.hex
	goodfet.cc info

installimmesnifffw: immeSniff.hex
	goodfet.cc erase
	goodfet.cc flash bins/immeSniff.hex
	goodfet.cc info

installchronostestrecvusbfw: chronostestrecvusb.hex
	goodfet.cc erase
	goodfet.cc flash bins/testrecv.hex
	goodfet.cc info

installdonstestrecvusbfw: donstestrecvusb.hex
	goodfet.cc erase
	goodfet.cc flash bins/testrecv.hex
	goodfet.cc info

installchronostestxmitusbfw: chronostestxmitusb.hex
	goodfet.cc erase
	goodfet.cc flash bins/testxmit.hex
	goodfet.cc info

installdonstestxmitusbfw: donstestxmitusb.hex
	goodfet.cc erase
	goodfet.cc flash bins/testxmit.hex
	goodfet.cc info

installtestrecvfw: testrecvapplication.hex
	goodfet.cc erase
	goodfet.cc flash bins/testrecv.hex
	goodfet.cc info

installtestxmitfw: testxmitapplication.hex
	goodfet.cc erase
	goodfet.cc flash bins/testxmit.hex
	goodfet.cc info


testall: chronosapplication.hex donsapplication.hex chronostestrecvusb.hex donstestrecvusb.hex chronostestxmitusb.hex donstestxmitusb.hex testrecvapplication.hex testxmitapplication.hex chronosNIC.hex donsNIC.hex chronosSniff.hex donsSniff.hex immeSniff.hex
##immedongleapplication.hex 

# testing should see that each enumerates correctly in linux

verify: chronosapplication.hex
	goodfet.cc verify bins/application.hex

clean:
	rm -f *.ihx *.rel *.hex *.sym *.asm *.lst *.lnk *.map *.mem *.rst
