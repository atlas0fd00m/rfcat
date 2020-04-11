#!/usr/bin/env bash
echo  "=== set revision: `./revision.sh` ==="

if ( which sdcc )
then
    echo "'sdcc' found"
else
    echo "'sdcc' not found"
    exit 1;
fi
echo  "=== build firmwares ==="
cd firmware
./buildall.sh
cd ..

DATESTAMP=`date +%y%m%d`
TARGETDIR="rfcat_$DATESTAMP"
TARGETPATH="../$TARGETDIR"
echo "=== make archive ==="
rm -rf $TARGETPATH
if ( which hg )
then
    hg archive -r tip $TARGETPATH
else
    echo "'hg' not found"
fi

echo "=== touch up archive ==="
cp .revision $TARGETPATH
cp firmware/bins/*$DATESTAMP.hex $TARGETPATH/firmware/bins/

echo "=== package up archive $TARGETDIR.tgz ==="
cd ..
tar zcf $TARGETDIR.tgz $TARGETDIR
