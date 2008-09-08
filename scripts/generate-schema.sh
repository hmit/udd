#!/bin/sh

set -e
set -x
mkdir -p /org/udd.debian.net/udd/web/schema
cd /org/udd.debian.net/udd/web/schema
postgresql_autodoc -d udd -t html
postgresql_autodoc -d udd -t dot
dot -Tpng udd.dot > udd.png
