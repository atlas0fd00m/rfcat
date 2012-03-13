CC=sdcc
CFLAGS=-Iinclude
CFLAGSold=--no-pack-iram $(CF)
LFLAGS=--xram-loc 0xF000 

apps2531 = global.rel
apps2531d3 = global.reld3

apps1111 = cc1111rf.rel global.rel
apps1111c = cc1111rf.relc global.relc
apps1111d = cc1111rf.reld global.reld
apps1111i = cc1111rf.reli global.reli
appsid = cc1111rf.relid global.relid

libsvcom = cc1111_vcom.rel cc1111_vcomdesc.rel chipcon_usbdebug.rel #chipcon_usb.rel
libsvcomc = cc1111_vcom.relc cc1111_vcomdesc.relc chipcon_usbdebug.relc #chipcon_usb.rel
libsvcomd = cc1111_vcom.reld cc1111_vcomdesc.reld chipcon_usbdebug.reld #chipcon_usb.rel
libsvcomi = cc1111_vcom.reli cc1111_vcomdesc.reli chipcon_usbdebug.reli #chipcon_usb.rel

libsusb  = chipcon_usb.rel chipcon_usbdebug.rel
libsusbc  = chipcon_usb.rc chipcon_usbdebug.relc
libsusbd3 = chipcon_usb.rd3 chipcon_usbdebug.reld3
libsusbd  = chipcon_usb.rd chipcon_usbdebug.reld
libsusbi  = immeusb.reli immeusbdebug.reli

libsimme  = $(appsi) immeio.reli immekeys.reli immefont.reli   #  immedisplay.rel immeterm.rel
libsimmed  = $(appsid) immeio.relid immekeys.relid immefont.relid   #  immedisplay.rel immeterm.rel
libsi  = $(apps) immeio.rel immekeys.rel immefont.rel   #  immedisplay.rel immeterm.rel
#srcs = $(libs,.rel=.c) 


all: chronosapplication.hex
donfw: donsapplication.hex
immefw: immeapplication.hex
testrecv: testrecvapplication.hex
testxmit: testxmitapplication.hex


chipcon_usb.rc : chipcon_usb.c
	./new_serial.py
	$(CC) $(CFLAGS) -DCHRONOSDONGLE -DCC1111 -c chipcon_usb.c

chipcon_usb.rd3 : chipcon_usb.c
	./new_serial.py
	$(CC) $(CFLAGS) -DCC2531 -c chipcon_usb.c

chipcon_usb.rd : chipcon_usb.c
	./new_serial.py
	$(CC) $(CFLAGS) -DDONSDONGLES -DCC1111 -c chipcon_usb.c

%.relc : %.c
	$(CC) $(CFLAGS) -DCHRONOSDONGLE -DCC1111 -c $<

%.reld3 : %.c
	$(CC) $(CFLAGS) -DCC2531 -c $<

%.reld : %.c
	$(CC) $(CFLAGS) -DDONSDONGLES -DCC1111 -c $<

%.reli : %.c
	$(CC) $(CFLAGS) -DIMME -c $<

%.relid : %.c
	$(CC) $(CFLAGS) -DIMME -DIMMEDONGLE -c $<

chronosapplication.hex: application.c $(libsusbc) $(apps1111c)
	sdcc $(CFLAGS) $(LFLAGS) application.c $(libsusb) $(apps1111) -DCHRONOSDONGLE -DCC1111
	packihx <application.ihx >bins/application.hex

cc2531.hex: appCC2531.c $(libsusbd3) $(apps2531d3)
	sdcc $(CFLAGS) $(LFLAGS) appCC2531.c $(libsusb) $(apps2531) -DCC2531
	packihx <appCC2531.ihx >bins/appCC2531.hex

donsapplication.hex: application.c $(libsusbd) $(apps1111d)
	sdcc $(CFLAGS) $(LFLAGS) application.c $(libsusb) $(apps1111) -DDONSDONGLES
	packihx <application.ihx >bins/application.hex

chronostestusbonly.hex: usbonly.c chipcon_usb.rc global.relc
	sdcc $(CFLAGS) $(LFLAGS) usbonly.c chipcon_usb.rel global.rel -DCHRONOSDONGLE
	packihx <usbonly.ihx >bins/usbonly.hex

donstestusbonly.hex: usbonly.c chipcon_usb.rc global.reld
	sdcc $(CFLAGS) $(LFLAGS) usbonly.c chipcon_usb.rel global.rel -DDONSDONGLES
	packihx <usbonly.ihx >bins/usbonly.hex

#	may be helpful when we actually have one...
#immedongleapplication.hex: application.c $(libsusbi)
#	sdcc $(CFLAGS) $(LFLAGS) application.c $(libsusb) -DIMMEDONGLE -DIMME
#	packihx <application.ihx >bins/application.hex
#
chronosNIC.hex: appNIC.c $(libsusbc) $(apps1111c)
	sdcc $(CFLAGS) $(LFLAGS) appNIC.c $(libsusb) $(apps1111) -DCHRONOSDONGLE
	packihx <appNIC.ihx >bins/chronosNIC.hex

chronosFHSS.hex: appFHSSNIC.c $(libsusbc) $(apps1111c)
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) $(apps1111) -DCHRONOSDONGLE
	packihx <appFHSSNIC.ihx >bins/chronosFHSS.hex

donsNIC.hex: appNIC.c $(libsusbd) $(apps1111c)
	sdcc $(CFLAGS) $(LFLAGS) appNIC.c $(libsusb) $(apps1111) -DDONSDONGLES
	packihx <appNIC.ihx >bins/donsNIC.hex

donsFHSS.hex: appFHSSNIC.c $(libsusbd) $(apps1111d)
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) $(apps1111) -DDONSDONGLES
	packihx <appFHSSNIC.ihx >bins/donsFHSS.hex

chronosSniff.hex: appSniff.c $(libsusbc) $(apps1111c)
	sdcc $(CFLAGS) $(LFLAGS) appSniff.c $(libsusb) $(apps1111) -DCHRONOSDONGLE
	packihx <appSniff.ihx >bins/chronosSniff.hex

donsSniff.hex: appSniff.c $(libsusbd) $(apps1111d)
	sdcc $(CFLAGS) $(LFLAGS) appSniff.c $(libsusb) $(apps1111) -DCHRONOSDONGLE
	packihx <appSniff.ihx >bins/donsSniff.hex

immeSniff.hex: appSniff.c $(libsimme) $(appsid)
	sdcc $(CFLAGS) $(LFLAGS) appSniff.c $(libsi) $(apps1111) -DIMME
	packihx <appSniff.ihx >bins/immeSniff.hex

chronostestxmitusb.hex: appNetworkTest.c $(libsusbc) $(apps1111c)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) $(apps1111) -DCHRONOSDONGLE -DTRANSMIT_TEST 
	packihx <appNetworkTest.ihx >bins/testxmit.hex

donstestxmitusb.hex: appNetworkTest.c $(libsusbd) $(apps1111d)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) $(apps1111) -DDONSDONGLES -DTRANSMIT_TEST 
	packihx <appNetworkTest.ihx >bins/testxmit.hex

chronostestrecvusb.hex: appNetworkTest.c $(libsusbc) $(apps1111c)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) $(apps1111) -DCHRONOSDONGLE -DRECEIVE_TEST
	packihx <appNetworkTest.ihx >bins/testrecv.hex

donstestrecvusb.hex: appNetworkTest.c $(libsusbd) $(apps1111d)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) $(apps1111) -DDONSDONGLES -DRECEIVE_TEST
	packihx <appNetworkTest.ihx >bins/testrecv.hex

testxmitapplication.hex: appNetworkTest.c $(libsvcomc) $(apps1111c)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsvcom) $(apps1111) -DCHRONOSDONGLE -DVIRTUAL_COM -DTRANSMIT_TEST 
	packihx <appNetworkTest.ihx >bins/testxmit.hex

testrecvapplication.hex: appNetworkTest.c $(libsvcomc) $(apps1111c)
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsvcom) $(apps1111) -DCHRONOSDONGLE -DVIRTUAL_COM -DRECEIVE_TEST
	packihx <appNetworkTest.ihx >bins/testrecv.hex



installchronosfw: chronosapplication.hex
	goodfet.cc erase
	goodfet.cc flash bins/application.hex
	goodfet.cc info

installdonfw: donsapplication.hex
	goodfet.cc erase
	goodfet.cc flash bins/application.hex
	goodfet.cc info

installcc2531: cc2531.hex
	goodfet.cc erase
	goodfet.cc flash bins/appCC2531.hex
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

testgoodfet:
	goodfet.cc info

backupdongle:
	goodfet.cc info
	goodfet.cc dumpcode bins/original-dongle-hex.backup

restoredongle:
	goodfet.cc erase
	goodfet.cc flash bins/original-dongle-hex.backup
	goodfet.cc info

testall: chronosapplication.hex donsapplication.hex chronostestrecvusb.hex donstestrecvusb.hex chronostestxmitusb.hex donstestxmitusb.hex testrecvapplication.hex testxmitapplication.hex chronosNIC.hex donsNIC.hex chronosFHSS.hex donsFHSS.hex chronosSniff.hex donsSniff.hex immeSniff.hex cc2531.hex
##immedongleapplication.hex 

# testing should see that each enumerates correctly in linux

verify: chronosapplication.hex
	goodfet.cc verify bins/application.hex

clean:
	rm -f *.ihx *.rel *.hex *.sym *.asm *.lst *.lnk *.map *.mem *.rst
