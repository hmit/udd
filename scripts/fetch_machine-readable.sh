#!/bin/sh
TARGETDIR=/org/udd.debian.org/mirrors/
SUBDIR=machine-readable
rm -rf $TARGETDIR/${SUBDIR}
cd ${TARGETDIR}
wget -q http://blends.alioth.debian.org/machine-readable/machine-readable.tar.bz2 -O - | tar xj 
