#!/bin/sh

# usage:
# /org/udd.debian.net/udd/scripts/sync-dist.sh archive.ubuntu.com::ubuntu/dists/intrepid /org/udd.debian.net/mirrors/ubuntu/intrepid

[ -d $2 ] || mkdir -p $2
rsync -rd --no-motd --include "Packages.gz" --include "Sources.gz" --include "**/" --exclude "*" --exclude ".~tmp~" $1 $2
