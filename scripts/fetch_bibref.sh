#!/bin/sh

set -e

TARGETDIR=/org/udd.debian.org/mirrors/bibref
FETCHURL=http://upstream-metadata.debian.net/~plessy/biblio.yaml
YAMLFILE=bibref.yaml
mkdir -p $TARGETDIR
# set -x
rm -rf $TARGETDIR/${YAMLFILE}
wget -q ${FETCHURL} -O ${TARGETDIR}/${YAMLFILE}
