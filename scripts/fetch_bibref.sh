#!/bin/sh

set -e

TARGETDIR=$1
FETCHURL=$2
mkdir -p $TARGETDIR
rm -rf $TARGETDIR
svn export $FETCHURL $TARGETDIR >/dev/null
