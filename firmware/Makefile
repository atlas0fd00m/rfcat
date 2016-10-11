# set BOOTLOADER_SIZE to match your bootloader
BOOTLOADER_SIZE = 0x1400
LDFLAGS_FLASH = --code-loc $(BOOTLOADER_SIZE)
USB_DEVICE_SERIAL_NUMBER="`./new_serial.py`"

CC=sdcc
CFLAGS=-Iinclude -DBUILD_VERSION=`../revision.sh`
CFLAGSold=--no-pack-iram $(CF)
LFLAGS=--xram-loc 0xF000 

apps2531 = global.rel
apps1111 = cc1111rf.rel global.rel cc1111_aes.rel
appsimme  = $(apps1111) immeio.rel immekeys.rel immefont.rel chipcon_dma.rel  #  immedisplay.rel immeterm.rel

libsvcom = cc1111_vcom.rel cc1111_vcomdesc.rel chipcon_usbdebug.rel chipcon_dma.rel #chipcon_usb.rel
libsusb  = chipcon_usb.rel chipcon_usbdebug.rel chipcon_dma.rel bootloader.rel
libsimme = 
libsidongle  = $(libsimme) immeusb.rel immeusbdebug.rel chipcon_dma.rel


all: 	RfCatChronos RfCatChronosCCBootloader RfCatDons RfCatDonsCCBootloader RfCatYS1 RfCatYS1CCBootloader
	make clean immeSniff

donfw: 	RfCatDons
immefw: immeSniff
testrecv: testrecvapplication.hex
testxmit: testxmitapplication.hex
ys1fw: RfCatYS1


# helper targets 
chipcon_usb.rel: chipcon_usb.c include/*.h
	#./new_serial.py
	$(CC) $(CFLAGS) $(DEFINES)  -DUSB_DEVICE_SERIAL_NUMBER=$(USB_DEVICE_SERIAL_NUMBER) -c chipcon_usb.c

%.rel: %.c include/*.h
	$(CC) $(CFLAGS) $(DEFINES) -c $<

# firmware build targets

## primary RfCat build targets ##
RfCatChronos: 				clean RfCatChronos.hex
RfCatChronosCCBootloader: 	clean RfCatChronosCCBootloader.hex
RfCatDons: 					clean RfCatDons.hex
RfCatDonsCCBootloader: 		clean RfCatDonsCCBootloader.hex
RfCatDons24: 				clean RfCatDons24.hex
RfCatDons24CCBootloader: 	clean RfCatDons24CCBootloader.hex
RfCatYS1: 					clean RfCatYS1.hex
RfCatYS1CCBootloader: 		clean RfCatYS1CCBootloader.hex
immeSniff: 					clean immeSniff.hex

RfCatChronos.hex: DEFINES = -DCHRONOSDONGLE -DCC1111 -DUSBDEVICE
RfCatChronos.hex: $(libsusb) $(apps1111)
	@printf "\n\n==RfCatChronos.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/RfCatChronos.hex

RfCatChronosCCBootloader.hex: DEFINES = -DCHRONOSDONGLE -DCC1111 -DUSBDEVICE -DBOOTLOADER_SIZE=$(BOOTLOADER_SIZE)
RfCatChronosCCBootloader.hex: $(libsusb) $(apps1111)
	@printf "\n\n==RfCatChronosCCBootloader.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) $(LDFLAGS_FLASH) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/RfCatChronosCCBootloader.hex

RfCatDons.hex: DEFINES = -DDONSDONGLES -DCC1111 -DUSBDEVICE -DBOOTLOADER_SIZE=$(BOOTLOADER_SIZE)
RfCatDons.hex: $(libsusb) $(apps1111)
	@printf "\n\n==RfCatDons.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/RfCatDons.hex

RfCatDonsCCBootloader.hex: DEFINES = -DDONSDONGLES -DCC1111 -DUSBDEVICE      
RfCatDonsCCBootloader.hex: appFHSSNIC.c $(libsusb) $(apps1111)
	@printf "\n\n==RfCatDonsCCBootloader.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) $(LDFLAGS_FLASH) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/RfCatDonsCCBootloader.hex

RfCatDons24.hex: DEFINES = -DDONSDONGLES -DCC2511 -DUSBDEVICE -DBOOTLOADER_SIZE=$(BOOTLOADER_SIZE)
RfCatDons24.hex: $(libsusb) $(apps1111)
	@printf "\n\n==RfCatDons24.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/RfCatDons24.hex

RfCatDons24CCBootloader.hex: DEFINES = -DDONSDONGLES -DCC2511 -DUSBDEVICE
RfCatDons24CCBootloader.hex: appFHSSNIC.c $(libsusb) $(apps1111)
	@printf "\n\n==RfCatDons24CCBootloader.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) $(LDFLAGS_FLASH) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/RfCatDons24CCBootloader.hex

RfCatYS1.hex: DEFINES = -DYARDSTICKONE -DCC1111 -DUSBDEVICE
RfCatYS1.hex: $(libsusb) $(apps1111)
	@printf "\n\n==RfCatYS1.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/RfCatYS1.hex

RfCatYS1CCBootloader.hex: DEFINES = -DYARDSTICKONE -DCC1111 -DUSBDEVICE
RfCatYS1CCBootloader.hex: appFHSSNIC.c $(libsusb) $(apps1111)
	@printf "\n\n==RfCatYS1CCBootloader.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) $(LDFLAGS_FLASH) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/RfCatYS1CCBootloader.hex


immeSniff.hex: DEFINES = -DIMME
immeSniff.hex: $(libsimme) $(appsimme)
	@printf "\n\n==immeSniff.hex building==\n", $(DEFINES)
	sdcc $(CFLAGS) $(LFLAGS) appSniff.c $(libsimme) $(appsimme) $(DEFINES)
	packihx <appSniff.ihx >bins/immeSniff.hex


## vanilla build targets ##
chronosapplication.hex: DEFINES= -DCHRONOSDONGLE -DCC1111 -DUSBDEVICE
chronosapplication.hex: $(libsusb) $(apps1111)
	@printf "\n\n==chronosapplication.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) application.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <application.ihx >bins/application.hex

donsapplication.hex: DEFINES= -DDONSDONGLES -DCC1111 -DUSBDEVICE
donsapplication.hex: $(libsusb) $(apps1111)
	@printf "\n\n==donsapplication.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) application.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <application.ihx >bins/application.hex

ys1application.hex: DEFINES= -DYARDSTICKONE -DCC1111 -DUSBDEVICE
ys1application.hex: $(libsusb) $(apps1111)
	@printf "\n\n==ys1application.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) application.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <application.ihx >bins/application.hex


## legacy and test / play build targets ##
chronosFHSS.hex: DEFINES= -DCHRONOSDONGLE -DCC1111 -DUSBDEVICE
chronosFHSS.hex: $(libsusb) $(apps1111)
	@printf "\n\n==chronosFHSS.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/chronosFHSS.hex

donsFHSS.hex: DEFINES= -DDONSDONGLES -DCC1111 -DUSBDEVICE
donsFHSS.hex: $(libsusb) $(apps1111)
	@printf "\n\n==donsFHSS.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/donsFHSS.hex

ys1FHSS.hex: DEFINES= -DYARDSTICKONE -DCC1111 -DUSBDEVICE
ys1FHSS.hex: $(libsusb) $(apps1111)
	@printf "\n\n==ys1FHSS.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appFHSSNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appFHSSNIC.ihx >bins/ys1FHSS.hex

chronosSniff.hex: DEFINES= -DCHRONOSDONGLE -DCC1111 -DUSBDEVICE
chronosSniff.hex: $(libsusb) $(apps1111)
	@printf "\n\n==chronosFHSS.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appSniff.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appSniff.ihx >bins/chronosSniff.hex

donsSniff.hex: DEFINES= -DDONSDONGLES -DCC1111 -DUSBDEVICE
donsSniff.hex: $(libsusb) $(apps1111)
	@printf "\n\n==donsSniff.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appSniff.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appSniff.ihx >bins/donsSniff.hex

ys1Sniff.hex: DEFINES= -DYARDSTICKONE -DCC1111 -DUSBDEVICE
ys1Sniff.hex: $(libsusb) $(apps1111)
	@printf "\n\n==ys1Sniff.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appSniff.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appSniff.ihx >bins/ys1Sniff.hex

chronosNIC.hex: DEFINES= -DCHRONOSDONGLE -DCC1111 -DUSBDEVICE
chronosNIC.hex: appNIC.c $(libsusb) $(apps1111)
	@printf "\n\n==chronosNIC.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appNIC.ihx >bins/chronosNIC.hex

donsNIC.hex: DEFINES= -DDONSDONGLES -DCC1111 -DUSBDEVICE
donsNIC.hex: $(libsusb) $(apps1111)
	@printf "\n\n==donsNIC.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appNIC.ihx >bins/donsNIC.hex

ys1NIC.hex: DEFINES= -DYARDSTICKONE -DCC1111 -DUSBDEVICE
ys1NIC.hex: $(libsusb) $(apps1111)
	@printf "\n\n==ys1NIC.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNIC.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appNIC.ihx >bins/ys1NIC.hex

immeGame1.hex: DEFINES= -DIMME
immeGame1.hex: $(libsimme) $(appsimme)
	@printf "\n\n==immeGame1.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) imme-blackhat-game1.c $(libsiimme) $(appsimme) $(DEFINES)
	packihx <imme-blackhat-game1.ihx >bins/immeGame1.hex

immeGame2.hex: DEFINES= -DIMME
immeGame2.hex: $(libsimme) $(appsimme)
	@printf "\n\n==immeGame2.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) imme-blackhat-game2.c $(libsiimme) $(appsimme) $(DEFINES)
	packihx <imme-blackhat-game2.ihx >bins/immeGame2.hex

cc2531.hex: DEFINES=-DCC2531 -DUSBDEVICE
cc2531.hex: $(libsusb) $(apps2531)
	@printf "\n\n==cc2531.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appCC2531.c $(libsusb) $(apps2531) $(DEFINES)
	packihx <appCC2531.ihx >bins/appCC2531.hex

chronostestusbonly.hex: DEFINES= -DCHRONOSDONGLE -DCC1111 -DUSBDEVICE
chronostestusbonly.hex: usbonly.c chipcon_usb.rel global.rel
	@printf "\n\n==chronosstestusbonly.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) usbonly.c chipcon_usb.rel global.rel $(DEFINES)
	packihx <usbonly.ihx >bins/usbonly.hex

donstestusbonly.hex: DEFINES= -DDONSDONGLES -DCC1111 -DUSBDEVICE
donstestusbonly.hex: usbonly.c chipcon_usb.rel global.rel
	@printf "\n\n==donstestusbonly.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) usbonly.c chipcon_usb.rel global.rel $(DEFINES)
	packihx <usbonly.ihx >bins/usbonly.hex

ys1testusbonly.hex: DEFINES= -DYARDSTICKONE -DCC1111 -DUSBDEVICE
ys1testusbonly.hex: usbonly.c chipcon_usb.rel global.rel
	@printf "\n\n==ys1testusbonly.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) usbonly.c chipcon_usb.rel global.rel $(DEFINES)
	packihx <usbonly.ihx >bins/usbonly.hex

#	may be helpful when we actually have one...
#immedongleapplication.hex: DEFINES=  -DIMMEDONGLE -DIMME
#immedongleapplication.hex: application.c $(libsusb)
#	sdcc $(CFLAGS) $(LFLAGS) application.c $(libsusb) $(DEFINES)
#	packihx <application.ihx >bins/application.hex
#
chronostestxmitusb.hex: DEFINES= -DCHRONOSDONGLE -DCC1111 -DTRANSMIT_TEST  -DUSBDEVICE
chronostestxmitusb.hex: $(libsusb) $(apps1111)
	@printf "\n\n==chronostestxmitusb.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appNetworkTest.ihx >bins/testxmit.hex

donstestxmitusb.hex: DEFINES= -DDONSDONGLES -DCC1111 -DTRANSMIT_TEST  -DUSBDEVICE
donstestxmitusb.hex: appNetworkTest.c $(libsusb) $(apps1111)
	@printf "\n\n==donstestxmitusb.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appNetworkTest.ihx >bins/testxmit.hex

ys1testxmitusb.hex: DEFINES= -DYARDSTICKONE -DCC1111 -DTRANSMIT_TEST  -DUSBDEVICE
ys1testxmitusb.hex: appNetworkTest.c $(libsusb) $(apps1111)
	@printf "\n\n==ys1testxmitusb.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appNetworkTest.ihx >bins/testxmit.hex

chronostest.hex: DEFINES= -DCHRONOSDONGLE -DCC1111 -DRECEIVE_TEST -DUSBDEVICE
chronostest.hex: appTest.c $(libsusb) $(apps1111)
	@printf "\n\n==chronostest.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appTest.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appTest.ihx >bins/test.hex

chronostestCC.hex: DEFINES= -DCHRONOSDONGLE -DCC1111 -DRECEIVE_TEST -DUSBDEVICE -DBOOTLOADER_SIZE=$(BOOTLOADER_SIZE)
chronostestCC.hex: appTest.c $(libsusb) $(apps1111)
	@printf "\n\n==chronostest.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) $(LDFLAGS_FLASH) appTest.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appTest.ihx >bins/test.hex

donstest.hex: DEFINES= -DDONSDONGLES -DCC1111 -DRECEIVE_TEST -DUSBDEVICE
donstest.hex: appTest.c $(libsusb) $(apps1111)
	@printf "\n\n==donstest.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appTest.c $(libsusb) $(apps1111)  $(DEFINES)
	packihx <appTest.ihx >bins/test.hex

donstestCC.hex: DEFINES= -DDONSDONGLES -DCC1111 -DRECEIVE_TEST -DUSBDEVICE -DBOOTLOADER_SIZE=$(BOOTLOADER_SIZE)
donstestCC.hex: appTest.c $(libsusb) $(apps1111)
	@printf "\n\n==donstest.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) $(LDFLAGS_FLASH) appTest.c $(libsusb) $(apps1111)  $(DEFINES)
	packihx <appTest.ihx >bins/test.hex

chronostestrecvusb.hex: DEFINES= -DCHRONOSDONGLE -DCC1111 -DRECEIVE_TEST -DUSBDEVICE
chronostestrecvusb.hex: appNetworkTest.c $(libsusb) $(apps1111)
	@printf "\n\n==chronostestrecvusb.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appNetworkTest.ihx >bins/testrecv.hex

chronostestrecvusbCC.hex: DEFINES= -DCHRONOSDONGLE -DCC1111 -DRECEIVE_TEST -DUSBDEVICE -DBOOTLOADER_SIZE=$(BOOTLOADER_SIZE)
chronostestrecvusbCC.hex: appNetworkTest.c $(libsusb) $(apps1111)
	@printf "\n\n==chronostestrecvusb.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) $(LDFLAGS_FLASH) appNetworkTest.c $(libsusb) $(apps1111) $(DEFINES)
	packihx <appNetworkTest.ihx >bins/testrecv.hex

donstestrecvusb.hex: DEFINES= -DDONSDONGLES -DCC1111 -DRECEIVE_TEST -DUSBDEVICE
donstestrecvusb.hex: appNetworkTest.c $(libsusb) $(apps1111)
	@printf "\n\n==donstestrecvusb.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) $(apps1111)  $(DEFINES)
	packihx <appNetworkTest.ihx >bins/testrecv.hex

donstestrecvusbCC.hex: DEFINES= -DDONSDONGLES -DCC1111 -DRECEIVE_TEST -DUSBDEVICE -DBOOTLOADER_SIZE=$(BOOTLOADER_SIZE)
donstestrecvusbCC.hex: appNetworkTest.c $(libsusb) $(apps1111)
	@printf "\n\n==donstestrecvusb.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) $(LDFLAGS_FLASH) appNetworkTest.c $(libsusb) $(apps1111)  $(DEFINES)
	packihx <appNetworkTest.ihx >bins/testrecv.hex

ys1testrecvusb.hex: DEFINES= -DYARDSTICKONE -DCC1111 -DRECEIVE_TEST -DUSBDEVICE
ys1testrecvusb.hex: appNetworkTest.c $(libsusb) $(apps1111)
	@printf "\n\n==ys1testrecvusb.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsusb) $(apps1111)  $(DEFINES)
	packihx <appNetworkTest.ihx >bins/testrecv.hex

testxmitapplication.hex: DEFINES= -DCHRONOSDONGLE -DVIRTUAL_COM -DTRANSMIT_TEST  -DUSBDEVICE
testxmitapplication.hex: appNetworkTest.c $(libsvcom) $(apps1111)
	@printf "\n\n==testxmitapplication.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsvcom) $(apps1111) $(DEFINES)
	packihx <appNetworkTest.ihx >bins/testxmit.hex

testrecvapplication.hex: DEFINES= -DCHRONOSDONGLE -DVIRTUAL_COM -DRECEIVE_TEST -DUSBDEVICE
testrecvapplication.hex: appNetworkTest.c $(libsvcom) $(apps1111)
	@printf "\n\n==testrecvapplication.hex building==\n"
	sdcc $(CFLAGS) $(LFLAGS) appNetworkTest.c $(libsvcom) $(apps1111) $(DEFINES)
	packihx <appNetworkTest.ihx >bins/testrecv.hex



# installer targets (depend on the firmware build targets above and require a goodfet)

## primary installer targets ##
installRfCatChronosDongle: RfCatChronos.hex
	goodfet.cc erase
	goodfet.cc flash bins/RfCatChronos.hex
	goodfet.cc verify bins/RfCatChronos.hex
	goodfet.cc info

installRfCatChronosDongleCCBootloader: RfCatChronosCCBootloader.hex
	if [ ! -c /dev/RFCAT_BL_C ] ; then ../rfcat --bootloader --force && sleep 1 ; fi ;
	rfcat_bootloader /dev/RFCAT_BL_C erase_all
	rfcat_bootloader /dev/RFCAT_BL_C download bins/RfCatChronosCCBootloader.hex
	rfcat_bootloader /dev/RFCAT_BL_C verify bins/RfCatChronosCCBootloader.hex && rfcat_bootloader /dev/RFCAT_BL_C run

installRfCat24DonsDongle: RfCatDons24.hex
	goodfet.cc erase
	goodfet.cc flash bins/RfCatDons24.hex
	goodfet.cc verify bins/RfCatDons24.hex
	goodfet.cc info

installRfCat24DonsDongleCCBootloader: RfCatDons24CCBootloader.hex
	if [ ! -c /dev/RFCAT_BL_D ] ; then ../rfcat --bootloader --force && sleep 1 ; fi ;
	rfcat_bootloader /dev/RFCAT_BL_D erase_all
	rfcat_bootloader /dev/RFCAT_BL_D download bins/RfCatDons24CCBootloader.hex
	rfcat_bootloader /dev/RFCAT_BL_D verify bins/RfCatDons24CCBootloader.hex && rfcat_bootloader /dev/RFCAT_BL_D run

installRfCatDonsDongle: RfCatDons.hex
	goodfet.cc erase
	goodfet.cc flash bins/RfCatDons.hex
	goodfet.cc verify bins/RfCatDons.hex
	goodfet.cc info

installRfCatDonsDongleCCBootloader: RfCatDonsCCBootloader.hex
	if [ ! -c /dev/RFCAT_BL_D ] ; then ../rfcat --bootloader --force && sleep 1 ; fi ;
	rfcat_bootloader /dev/RFCAT_BL_D erase_all
	rfcat_bootloader /dev/RFCAT_BL_D download bins/RfCatDonsCCBootloader.hex
	rfcat_bootloader /dev/RFCAT_BL_D verify bins/RfCatDonsCCBootloader.hex && rfcat_bootloader /dev/RFCAT_BL_D run

installRfCatYS1: RfCatYS1.hex
	goodfet.cc erase
	goodfet.cc flash bins/RfCatYS1.hex
	goodfet.cc verify bins/RfCatYS1.hex
	goodfet.cc info

installRfCatYS1CCBootloader: RfCatYS1CCBootloader.hex
	if [ ! -c /dev/RFCAT_BL_YS1 ] ; then ../rfcat --bootloader --force && sleep 1 ; fi ;
	rfcat_bootloader /dev/RFCAT_BL_YS1 erase_all
	rfcat_bootloader /dev/RFCAT_BL_YS1 download bins/RfCatYS1CCBootloader.hex
	rfcat_bootloader /dev/RFCAT_BL_YS1 verify bins/RfCatYS1CCBootloader.hex && rfcat_bootloader /dev/RFCAT_BL_YS1 run

installimmesnifffw: immeSniff
	goodfet.cc erase
	goodfet.cc flash bins/immeSniff.hex
	goodfet.cc verify bins/immeSniff.hex
	goodfet.cc info


## legacy and test / play install targets ##
installchronosfhssnicfw: chronosFHSS.hex
	goodfet.cc erase
	goodfet.cc flash bins/chronosFHSS.hex
	goodfet.cc verify bins/chronosFHSS.hex
	goodfet.cc info
	
installdonsfhssnicfw: donsFHSS.hex
	goodfet.cc erase
	goodfet.cc flash bins/donsFHSS.hex
	goodfet.cc verify bins/donsFHSS.hex
	goodfet.cc info
	
installchronosnicfw: chronosNIC.hex
	goodfet.cc erase
	goodfet.cc flash bins/chronosNIC.hex
	goodfet.cc verify bins/chronosNIC.hex
	goodfet.cc info
	
installys1fhssnicfw: ys1FHSS.hex
	goodfet.cc erase
	goodfet.cc flash bins/ys1FHSS.hex
	goodfet.cc verify bins/ys1FHSS.hex
	goodfet.cc info

installdonsnicfw: donsNIC.hex
	goodfet.cc erase
	goodfet.cc flash bins/donsNIC.hex
	goodfet.cc verify bins/donsNIC.hex
	goodfet.cc info

installys1nicfw: ys1NIC.hex
	goodfet.cc erase
	goodfet.cc flash bins/ys1NIC.hex
	goodfet.cc verify bins/ys1NIC.hex
	goodfet.cc info

installchronossnifffw: chronosSniff.hex
	goodfet.cc erase
	goodfet.cc flash bins/chronosSniff.hex
	goodfet.cc verify bins/chronosSniff.hex
	goodfet.cc info

installdonssnifffw: donsSniff.hex
	goodfet.cc erase
	goodfet.cc flash bins/donsSniff.hex
	goodfet.cc verify bins/donsSniff.hex
	goodfet.cc info

installys1snifffw: ys1Sniff.hex
	goodfet.cc erase
	goodfet.cc flash bins/ys1Sniff.hex
	goodfet.cc verify bins/ys1Sniff.hex
	goodfet.cc info

installimmegame1: immeGame1.hex
	goodfet.cc erase
	goodfet.cc flash bins/immeGame1.hex
	goodfet.cc verify bins/immeGame1.hex
	goodfet.cc info

installimmegame2: immeGame2.hex
	goodfet.cc erase
	goodfet.cc flash bins/immeGame2.hex
	goodfet.cc verify bins/immeGame2.hex
	goodfet.cc info

installcc2531: cc2531.hex
	goodfet.cc erase
	goodfet.cc flash bins/appCC2531.hex
	goodfet.cc verify bins/appCC2531.hex
	goodfet.cc info

#installimmefw: immedongleapplication.hex
#	goodfet.cc erase
#	goodfet.cc flash bins/application.hex
#	goodfet.cc info

installchronostestrecvusbfw: chronostestrecvusb.hex
	goodfet.cc erase
	goodfet.cc flash bins/testrecv.hex
	goodfet.cc verify bins/testrecv.hex
	goodfet.cc info

installchronostestrecvusbfwCC: chronostestrecvusbCC.hex
	if [ ! -c /dev/RFCAT_BL_C ] ; then ../rfcat --bootloader --force && sleep 1 ; fi ;
	rfcat_bootloader /dev/RFCAT_BL_C erase_all
	rfcat_bootloader /dev/RFCAT_BL_C download bins/testrecv.hex
	rfcat_bootloader /dev/RFCAT_BL_C verify bins/testrecv.hex && rfcat_bootloader /dev/RFCAT_BL_C run

installdonstestrecvusbfw: donstestrecvusb.hex
	goodfet.cc erase
	goodfet.cc flash bins/testrecv.hex
	goodfet.cc verify bins/testrecv.hex
	goodfet.cc info

installdonstestrecvusbfwCC: donstestrecvusbCC.hex
	if [ ! -c /dev/RFCAT_BL_D ] ; then ../rfcat --bootloader --force && sleep 1 ; fi ;
	rfcat_bootloader /dev/RFCAT_BL_D erase_all
	rfcat_bootloader /dev/RFCAT_BL_D download bins/testrecv.hex
	rfcat_bootloader /dev/RFCAT_BL_D verify bins/testrecv.hex && rfcat_bootloader /dev/RFCAT_BL_D run

installys1testrecvusbfw: ys1testrecvusb.hex
	goodfet.cc erase
	goodfet.cc flash bins/testrecv.hex
	goodfet.cc verify bins/testrecv.hex
	goodfet.cc info

installchronostestxmitusbfw: chronostestxmitusb.hex
	goodfet.cc erase
	goodfet.cc flash bins/testxmit.hex
	goodfet.cc verify bins/testxmit.hex
	goodfet.cc info

installdonstestxmitusbfw: donstestxmitusb.hex
	goodfet.cc erase
	goodfet.cc flash bins/testxmit.hex
	goodfet.cc verify bins/testxmit.hex
	goodfet.cc info

installys1testxmitusbfw: ys1testxmitusb.hex
	goodfet.cc erase
	goodfet.cc flash bins/testxmit.hex
	goodfet.cc verify bins/testxmit.hex
	goodfet.cc info

installtestrecvfw: testrecvapplication.hex
	goodfet.cc erase
	goodfet.cc flash bins/testrecv.hex
	goodfet.cc verify bins/testrecv.hex
	goodfet.cc info

installtestxmitfw: testxmitapplication.hex
	goodfet.cc erase
	goodfet.cc flash bins/testxmit.hex
	goodfet.cc verify bins/testxmit.hex
	goodfet.cc info

installchronosbootloader: 
	./bootloader_serial.py $(USBSERNUM)
	goodfet.cc erase
	goodfet.cc flash CCBootloader/CCBootloader-rfcat-chronosdongle-serial.hex
	goodfet.cc verify CCBootloader/CCBootloader-rfcat-chronosdongle-serial.hex
	goodfet.cc info

installdonsbootloader: 
	./bootloader_serial.py $(USBSERNUM)
	goodfet.cc erase
	goodfet.cc flash CCBootloader/CCBootloader-rfcat-donsdongle-serial.hex
	goodfet.cc verify CCBootloader/CCBootloader-rfcat-donsdongle-serial.hex
	goodfet.cc info

installys1bootloader: 
	./bootloader_serial.py $(USBSERNUM)
	goodfet.cc erase
	goodfet.cc flash CCBootloader/CCBootloader-rfcat-ys1-serial.hex
	goodfet.cc verify CCBootloader/CCBootloader-rfcat-ys1-serial.hex
	goodfet.cc info

installchronosbootloadercctool: 
	./bootloader_serial.py $(USBSERNUM)
	cc-tool -n CC1111 -e -w CCBootloader/CCBootloader-rfcat-chronosdongle-serial.hex
	cc-tool -n CC1111 -v CCBootloader/CCBootloader-rfcat-chronosdongle-serial.hex

installdonsbootloadercctool: 
	./bootloader_serial.py $(USBSERNUM)
	cc-tool -n CC1111 -e -w CCBootloader/CCBootloader-rfcat-donsdongle-serial.hex
	cc-tool -n CC1111 -v CCBootloader/CCBootloader-rfcat-donsdongle-serial.hex

installys1bootloadercctool: 
	./bootloader_serial.py $(USBSERNUM)
	cc-tool -n CC1111 -e -w CCBootloader/CCBootloader-rfcat-ys1-serial.hex
	cc-tool -n CC1111 -v CCBootloader/CCBootloader-rfcat-ys1-serial.hex

testgoodfet:
	goodfet.cc info

backupdongle:
	goodfet.cc info
	goodfet.cc dumpcode bins/original-dongle-hex.backup

restoredongle:
	goodfet.cc erase
	goodfet.cc flash bins/original-dongle-hex.backup
	goodfet.cc verify bins/original-dongle-hex.backup
	goodfet.cc info

testall: clean
testall: RfCatChronosCCBootloader
testall:	RfCatChronos
testall:	chronosFHSS.hex
testall:	chronosapplication.hex
testall:	chronostestrecvusb.hex
testall:	chronostestxmitusb.hex
testall:	chronosNIC.hex
testall:	chronosSniff.hex
testall:	RfCatDons
testall:	RfCatDonsCCBootloader
testall:	RfCatYS1
testall:	RfCatYS1CCBootloader
testall:	donsFHSS.hex
testall:	donsapplication.hex
testall:	donstestrecvusb.hex
testall:	donstestxmitusb.hex
testall:	ys1FHSS.hex
testall:	ys1application.hex
testall:	ys1testrecvusb.hex
testall:	ys1testxmitusb.hex
testall:	testrecvapplication.hex
testall:	testxmitapplication.hex
#testall:	donsNIC.hex
#testall:	cc2531.hex
##testall:	immedongleapplication.hex 
#testall:	donsSniff.hex
	@make clean donsNIC.hex
	@make clean donsSniff.hex
	@make clean immeSniff

# testing should see that each enumerates correctly in linux

verifyRfCatChronosDongle: chronosapplication.hex
	goodfet.cc verify bins/chronosFHSS.hex

verifyRfCatDonsDongle: chronosapplication.hex
	goodfet.cc verify bins/donsFHSS.hex

verifyRfCatYS1: chronosapplication.hex
	goodfet.cc verify bins/ys1FHSS.hex

clean:
	@printf "\n==== CLEANING STUFF UP ====\n"
	rm -f *.ihx *.rel *.hex *.sym *.asm *.lst *.lnk *.map *.mem *.rst
