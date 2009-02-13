#!/bin/sh

set -e
cd /org/udd.debian.org/udd/web/
umask 022
pg_dump --no-owner -p 5441 udd | gzip > udd.sql.gz.new
mv udd.sql.gz.new udd.sql.gz
