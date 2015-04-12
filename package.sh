echo  "=== set revision: `./revision.sh` ==="

echo  "=== build firmwares ==="
cd firmware
./buildall.sh
cd ..

DATESTAMP=`date +%y%m%d`
TARGETDIR="rfcat_$DATESTAMP"
TARGETPATH="../$TARGETDIR"
echo "=== make archive ==="
rm -rf $TARGETPATH
hg archive -r tip $TARGETPATH

echo "=== touch up archive ==="
cp .revision $TARGETPATH
cp firmware/bins/*$DATESTAMP.hex $TARGETPATH/firmware/bins/

echo "=== package up archive $TARGETDIR.tgz ==="
cd ..
tar zcf $TARGETDIR.tgz $TARGETDIR
