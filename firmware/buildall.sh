
DATESTAMP=`date +%y%m%d`
cp .serial /tmp/
make clean RfCatChronos
[ $? -ne 0 ] && printf "\n\n\n FAILURE TO BUILD!!! \n\n\n" && exit
mv bins/RfCatChronos.hex bins/RfCatChronos-$DATESTAMP.hex

cp /tmp/.serial .
make RfCatChronosCCBootloader 
[ $? -ne 0 ] && printf "\n\n\n FAILURE TO BUILD!!! \n\n\n" && exit
mv bins/RfCatChronosCCBootloader.hex bins/RfCatChronosCCBootloader-$DATESTAMP.hex

cp /tmp/.serial .
make clean RfCatDons
[ $? -ne 0 ] && printf "\n\n\n FAILURE TO BUILD!!! \n\n\n" && exit
mv bins/RfCatDons.hex bins/RfCatDons-$DATESTAMP.hex

cp /tmp/.serial .
make RfCatDonsCCBootloader
[ $? -ne 0 ] && printf "\n\n\n FAILURE TO BUILD!!! \n\n\n" && exit
mv bins/RfCatDonsCCBootloader.hex bins/RfCatDonsCCBootloader-$DATESTAMP.hex

cp /tmp/.serial .
make clean RfCatYS1
[ $? -ne 0 ] && printf "\n\n\n FAILURE TO BUILD!!! \n\n\n" && exit
mv bins/RfCatYS1.hex bins/RfCatYS1-$DATESTAMP.hex

cp /tmp/.serial .
make RfCatYS1CCBootloader
[ $? -ne 0 ] && printf "\n\n\n FAILURE TO BUILD!!! \n\n\n" && exit
mv bins/RfCatYS1CCBootloader.hex bins/RfCatYS1CCBootloader-$DATESTAMP.hex

cp /tmp/.serial .
make clean immeSniff
[ $? -ne 0 ] && printf "\n\n\n FAILURE TO BUILD!!! \n\n\n" && exit
mv bins/immeSniff.hex bins/immeSniff-$DATESTAMP.hex
