#!/bin/sh

set -e
set -x
mkdir -p /org/udd.debian.org/udd/web/schema
cd /org/udd.debian.org/udd/web/schema
postgresql_autodoc -d udd -p 5441 -t html
postgresql_autodoc -d udd -p 5441 -t dot
dot -Tpng udd.dot > udd.png
