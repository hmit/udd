#!/bin/sh
TARGETDIR=/org/udd.debian.org/mirrors/bibref
mkdir -p $TARGETDIR
rm -rf $TARGETDIR/*
wget -q http://upstream-metadata.debian.net/for_UDD/biblio.yaml -O ${TARGETDIR}/bibref.yaml
