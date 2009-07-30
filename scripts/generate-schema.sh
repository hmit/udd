#!/bin/sh

set -e
mkdir -p /org/udd.debian.org/udd/web/schema
cd /org/udd.debian.org/udd/web/schema
P=/org/udd.debian.org/udd/scripts/pg_autodoc/
$P/postgresql_autodoc -l $P -d udd -p 5441 -t html | grep -v 'Producing '
$P/postgresql_autodoc -l $P -d udd -p 5441 -t dot | grep -v 'Producing '
dot -Tpng udd.dot > udd.png
dot -Tsvg udd.dot > udd.svg
