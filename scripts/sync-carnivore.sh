#!/bin/bash

set -e
umask 002
pw=$(</org/udd.debian.org/udd-qa.debian.org-password)
TARGET=/org/udd.debian.org/mirrors/qa.debian.org-carnivore-report
echo http://udd:${pw}@qa.debian.org/carnivore-report | wget -q -O $TARGET -i -
