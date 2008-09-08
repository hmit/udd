#!/bin/sh
# Sync data that is mirrored from merkel to udd.d.n.
# Use udd.d.n as source: doesn't need to be a DD!

# directory where to put the mirrors 
# (usually /org/udd.debian.net/mirrors/ )
TARGET=$1

# You will probably need to symlink /org/bugs.debian.org to
# /org/udd.debian.net/mirrors/bugs.debian.org

if [ $# -ne 1 ]; then
	echo "missing arg"
	exit 1
fi

rsync -avzP --delete \
udd.debian.net:/org/udd.debian.net/mirrors/{qa.debian.org,bugs.debian.org} \
$TARGET
