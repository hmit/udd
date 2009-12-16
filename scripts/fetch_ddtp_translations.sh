#!/bin/sh

set -e

TARGETPATH=$1
MIRROR=$2
shift
shift
RELEASES=$*
HTTPMIRROR="http://$MIRROR"
# RSYNCMIRROR="$MIRROR::debian/"
# rm -rf "$TARGETPATH"
for rel in $RELEASES; do
    TARGETDIR="$TARGETPATH"/${rel}
    find "$TARGETPATH"/${rel} -name '*.md5' -exec mv '{}' '{}'.prev \;
    rm -rf "$TARGETDIR"/*.gz
    [ -d $TARGETDIR ] || mkdir -p $TARGETDIR
    # store a copy of md5 sums of previous files
    `dirname $0`/getlinks.pl "$HTTPMIRROR"/dists/${rel}/main/i18n/ "$TARGETPATH"/${rel} 'Translation-.*\.gz$'
    # create md5 sums of translation files to enable deciding whether processing is needed or not
    for zipfile in `find "$TARGETPATH"/${rel} -name '*.gz'` ; do md5sum $zipfile > "$TARGETPATH"/${rel}/`basename $zipfile .gz`.md5 ; done
    # getlinks.pl always returns 0 independently from success so we have to verify that the target dir is
    # not empty.
    NUMFILES=`ls "$TARGETPATH"/${rel} | wc -l`
    if [ $NUMFILES -le 0 ] ; then
	echo "Downloading translation for release ${rel} failed. Stopped."
	exit 66
    fi
    ## The rsync-able Translations do not (yet) contain package version info
    ## This might happen later but it requires deeper changes in several tools
    ## including apt - so we have to download via http from ddtp directly which
    ## does not support rsync
    # rsync -a --no-motd --include "Translation-*.gz" --exclude "*" "$RSYNCMIRROR"/dists/${rel}/main/i18n/ $TARGETDIR
done

exit 0

# alternatively use wget
cd "$TARGETPATH"
wget -erobots=off -m $HTTPMIRROR
