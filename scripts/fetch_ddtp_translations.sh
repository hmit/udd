#!/bin/sh
TARGETPATH=`grep "^\s*path:" /org/udd.debian.net/udd/config_ddtp.yaml | sed 's/^\s*path:\s*//'`
RELEASES=`grep "^\s*releases:" /org/udd.debian.net/udd/config_ddtp.yaml | sed 's/^\s*releases:\s*//'`
MIRROR=`grep "^\s*mirror:" /org/udd.debian.net/udd/config_ddtp.yaml | sed 's/^\s*mirror:\s*//'`
HTTPMIRROR="http://$MIRROR"
# RSYNCMIRROR="$MIRROR::debian/"
# rm -rf "$TARGETPATH"
for rel in $RELEASES; do
    TARGETDIR="$TARGETPATH"/${rel}
    rm -rf "$TARGETDIR"
    [ -d $TARGETDIR ] || mkdir -p $TARGETDIR
    `dirname $0`/getlinks.pl "$HTTPMIRROR"/dists/${rel}/main/i18n/ "$TARGETPATH"/${rel} 'Translation-.*' # \.gz$'
    gzip "$TARGETPATH"/${rel}/Translation-*
    # rsync -a --no-motd --include "Translation-*.gz" --exclude "*" "$RSYNCMIRROR"/dists/${rel}/main/i18n/ $TARGETDIR
done

exit 0

# alternatively use wget
cd "$TARGETPATH"
wget -erobots=off -m $HTTPMIRROR
