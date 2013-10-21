#!/bin/sh -e
#
# Clean up hashes from Blends metadata importer
# ---------------------------------------------
# The Blends metadata importer stores hashes for every single tasks
# file in UDD to speed up the import drastically by making sure
# that old data are not importet again and again for no use.
# Sometimes (basically for development / debuging) it is needed
# to do the reimport and thus cleaning up the hashes to force a new
# import is needed.  This can be done with this script.
# If 'all' as argument is given all Blends are cleaned up.
#
# Author: Andreas Tille <tille@debian.org>
# License: GPL

if [ $# -lt 1 ] ; then
    echo "Usage: $0 {<blendname>|all}"
    exit
fi

WHERE=''
if [ "$1" != "all" ] ; then
    WHERE="WHERE blend = '$1'"
fi

psql udd <<EOT
    UPDATE blends_tasks SET hashkey = '' $WHERE ;
EOT

