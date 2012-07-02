#!/bin/sh

set -e

TARGETDIR=/srv/udd.debian.org/mirrors/bibref
FETCHURL=http://blends.debian.net/packages-metadata/packages-metadata.tar.bz2
ARCHIVE=`basename $FETCHURL`
CURDIR=`pwd`

rm -rf $TARGETDIR
mkdir -p $TARGETDIR
wget -q ${FETCHURL} -O ${TARGETDIR}/${ARCHIVE}
cd $TARGETDIR
tar -xjf ${ARCHIVE}
# There is no point in keeping non-yaml files which later just cause errors
rm -f $CURDIR/bibref_gatherer_fetch.log
for nonyamlfile in `find . -name "*.upstream" -exec file \{\} \; | grep -e HTML -e XML | sed 's/:.*$//'` ; do
    file $nonyamlfile >> $CURDIR/bibref_gatherer_fetch.log
    rm -f $nonyamlfile
done
rm -rf ${ARCHIVE}
