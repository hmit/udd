#!/bin/sh
TARGETDIR=/org/udd.debian.net/mirrors/ftpnew
mkdir -p $TARGETDIR
rm -rf $TARGETDIR/*
wget -q http://ftp-master.debian.org/new.822 -O ${TARGETDIR}/new.822
cd $TARGETDIR
wget -q -r -N --level=2 --no-parent --no-directories http://ftp-master.debian.org/new/
rm -f $TARGETDIR/index.html*
