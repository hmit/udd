#!/bin/sh
# Translation files will be taken from the mirror available on the local machine
# However, we are doing some housekeeping to register what translations did really
# changed and need to be importet and which one are not touched by translators
# and thus can be ignored.

set -e

TARGETPATH=$1
MIRROR=$2

for indexdir in `find $MIRROR -name i18n -type d | sed "s?$MIRROR/\(.\+\)/i18n?\1?"` ; do
    # rel=`echo $index | sed "s?$MIRROR/*\([^/]\+\)/.*?\1?"`
    targetfile="${TARGETPATH}/${indexdir}"
    mkdir -p `dirname $targetfile`
    index=${MIRROR}/$indexdir/i18n/Index
    if [ -f $index ] ; then
	grep "\.bz2" $index | sed -e 's/^ //' -e 's/ \+/ /g' > $targetfile
    else
	rm -f $targetfile
	for trans in `find ${MIRROR}/$indexdir/i18n -mindepth 1 -maxdepth 1 -name "*.bz2"` ; do
	    echo "`sha1sum $trans | cut -d' ' -f1``ls -l $trans | sed 's/^[-rwlx]\+ [0-9]\+ [^ ]\+ [^ ]\+\([ 0-9]\+[0-9]\) .*/\1/'` `basename $trans`" >> $targetfile
	done
    fi
done

exit 0
