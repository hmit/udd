#!/bin/sh

set -e

TARGETDIR=/org/udd.debian.org/mirrors/bibref
FETCHURL=http://blends.debian.net/packages-metadata/packages-metadata.tar.bz2
ARCHIVE=`basename $FETCHURL`
set -x
rm -rf $TARGETDIR
mkdir -p $TARGETDIR
wget -q ${FETCHURL} -O ${TARGETDIR}/${ARCHIVE}
cd $TARGETDIR
tar -xjf ${ARCHIVE}
rm -rf ${ARCHIVE}
