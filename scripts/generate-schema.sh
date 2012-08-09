#!/bin/sh

set -e
mkdir -p /srv/udd.debian.org/udd/web/schema
cd /srv/udd.debian.org/udd/web/schema
P=/srv/udd.debian.org/udd/scripts/pg_autodoc/
$P/postgresql_autodoc -l $P -d udd -p 5452 -t html | grep -v 'Producing ' || test $? -eq 1
$P/postgresql_autodoc -l $P -d udd -p 5452 -t dot | grep -v 'Producing ' || test $? -eq 1
dot -Tpng udd.dot > udd.png
dot -Tsvg udd.dot > udd.svg
