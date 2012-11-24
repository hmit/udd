#!/bin/sh

set -e

TARGETDIR=/srv/udd.debian.org/mirrors/clone-bugs
FETCHURL=http://udd.debian.org/udd-bugs.sql.xz

rm -rf $TARGETDIR
mkdir -p $TARGETDIR
cd $TARGETDIR
wget -q ${FETCHURL}
