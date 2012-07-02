#!/bin/sh
TARGETDIR=/srv/udd.debian.org/mirrors/screenshots
mkdir -p $TARGETDIR
rm -rf $TARGETDIR/*
wget -q http://screenshots.debian.net/json/screenshots -O ${TARGETDIR}/screenshots.json
# packages.json just contains less information - but we want it all ...
# wget -q http://screenshots.debian.net/json/packages -O ${TARGETDIR}/packages.json
