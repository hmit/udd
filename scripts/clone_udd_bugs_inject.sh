#!/bin/sh
BUGSDUMP=/srv/udd.debian.org/mirrors/clone-bugs/udd-bugs.sql.gz

unset LANG
unset LC_ALL

psql --quiet udd <<EOT
DROP TABLE IF EXISTS bugs CASCADE;
DROP TABLE IF EXISTS bugs_merged_with;
DROP TABLE IF EXISTS bugs_blockedby;
DROP TABLE IF EXISTS bugs_blocks;
DROP TABLE IF EXISTS bugs_fixed_in;
DROP TABLE IF EXISTS bugs_found_in;
DROP TABLE IF EXISTS bugs_packages CASCADE;
DROP TABLE IF EXISTS bugs_tags;
DROP TABLE IF EXISTS bugs_usertags;
EOT

zcat $BUGSDUMP | psql --quiet udd
