#!/bin/bash

set -e
umask 002
SRC=he@merkel.debian.org:/org/qa.debian.org/carnivore
TARGET=/org/udd.debian.org/mirrors/qa.debian.org/

mkdir $TARGET &>/dev/null || true

rsync --quiet -e  "ssh -i /org/udd.debian.org/.ssh/id_carnivore_sync" -avz $SRC $TARGET
