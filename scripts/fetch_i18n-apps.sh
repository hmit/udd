#!/bin/sh -e
TARGETDIR=/srv/udd.debian.org/mirrors/i18n-apps
mkdir -p $TARGETDIR
rm -rf $TARGETDIR/*
wget -q http://i18n.debian.net/material/data/unstable.gz -O ${TARGETDIR}/sid.gz
wget -q http://i18n.debian.net/material/data/testing.gz -O ${TARGETDIR}/wheezy.gz

