#!/bin/sh
# Sync data that is mirrored from merkel to udd.d.n.
# Use udd.d.n as source: doesn't need to be a DD!

# directory where to put the mirrors 
# (usually /org/udd.debian.net/mirrors/ )

if [ $# -ne 1 ]; then
	echo "missing arg"
	exit 1
fi
TARGET=$1

rsync -avzP \
udd.debian.net:/org/udd.debian.net/mirrors/{qa.debian.org,bugs.debian.org} \
$TARGET
