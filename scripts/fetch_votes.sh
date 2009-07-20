#!/bin/sh
TARGETDIR="/org/udd.debian.org/mirrors/votes"
BASEURL="http://www.debian.org/vote"
WGET="wget --timestamping -q"

mkdir -p $TARGETDIR
rm -rf $TARGETDIR/*

start_year="2006"	# before that, URL scheme was different
this_year=`date +%Y`
for year in `seq $start_year $this_year` ; do
    for i in `seq -w 1 999` ; do
	$WGET -O "$TARGETDIR/${year}_vote_${i}_voters.txt" "$BASEURL/$year/vote_${i}_voters.txt" || break
	$WGET -O "$TARGETDIR/${year}_vote_${i}_tally.txt" "$BASEURL/$year/vote_${i}_tally.txt" || break
    done
done
for f in $TARGETDIR/* ; do	# wget's timestamping leaves around empty files
    test -s $f || rm -f $f
done
