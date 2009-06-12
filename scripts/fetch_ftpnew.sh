#!/bin/sh
TARGETDIR=/org/udd.debian.org/mirrors/ftpnew
mkdir -p $TARGETDIR
rm -rf $TARGETDIR/*
wget -q http://ftp-master.debian.org/new.822 -O ${TARGETDIR}/new.822
cd $TARGETDIR
wget -q -r -N --level=2 --no-parent --no-directories http://ftp-master.debian.org/new/
# Some large packages do contain e huge list of files which just consumes space in our
# cache - so simply delete these entries which are of no use here
#  sed -i '/^[-dlrwx]\+ root\/root/d' ${TARGETDIR}/*.html
# Finally it might be better to keep originals ...
rm -f $TARGETDIR/index.html*
