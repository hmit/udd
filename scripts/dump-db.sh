#!/bin/sh

set -e
cd /srv/udd.debian.org/udd/web/dumps/
umask 022
# exclude dumps from backups, at DSA's request (ivodd 20140101)
touch .nobackup

pg_dump --no-owner -p 5452 -n history udd | gzip > udd-history.sql.gz.new
mv udd-history.sql.gz.new udd-history.sql.gz
pg_dump --no-owner -p 5452 -T ldap -T really_active_dds -T pts udd | gzip > udd.sql.gz.new
mv udd.sql.gz.new udd.sql.gz
pg_dump --no-owner -p 5452 \
        -t bugs -t bugs_blockedby -t bugs_blocks -t bugs_fixed_in -t bugs_found_in -t bugs_merged_with -t bugs_packages -t bugs_tags -t bugs_usertags \
        -t archived_bugs -t archived_bugs_packages -t archived_bugs_merged_with -t archived_bugs_found_in -t archived_bugs_fixed_in -t archived_bugs_tags -t archived_bugs_blocks -t archived_bugs_blockedby \
    udd | xz > udd-bugs.sql.xz.new
mv udd-bugs.sql.xz.new udd-bugs.sql.xz

pg_dump --no-owner -p 5452 \
        -t popcon -t popcon_src udd | xz > udd-popcon.sql.xz.new
mv udd-popcon.sql.xz.new udd-popcon.sql.xz

