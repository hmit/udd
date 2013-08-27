#!/bin/sh

TARGETDIR=/srv/udd.debian.org/mirrors/piuparts
mkdir -p $TARGETDIR
rm -rf $TARGETDIR/*

SCRIPTDIR=`dirname $0`

BASEURL=https://piuparts.debian.org/

wget -q ${BASEURL}/sections.yaml -O ${TARGETDIR}/sections.yaml
cd $TARGETDIR
$SCRIPTDIR/piuparts_files.py | while read file
do
	wget -q ${BASEURL}/$file/sources.yaml -O ${TARGETDIR}/$file.yaml
done

