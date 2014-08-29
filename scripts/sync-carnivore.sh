#!/bin/bash

set -e
umask 002
pw=$(</srv/udd.debian.org/udd-qa.debian.org-password)
TARGET=/srv/udd.debian.org/mirrors/qa.debian.org-carnivore-report
echo https://udd:${pw}@qa.debian.org/carnivore-report | wget -q -O $TARGET -i -
