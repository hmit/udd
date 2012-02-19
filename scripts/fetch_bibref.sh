#!/bin/sh

set -e

TARGETDIR=/org/udd.debian.org/mirrors/bibref
YAMLFILE=bibref.yaml
mkdir -p $TARGETDIR
rm -rf $TARGETDIR/${YAMLFILE}
wget -q http://upstream-metadata.debian.net/for_UDD/${YAMLFILE} -O ${TARGETDIR}/${YAMLFILE}
