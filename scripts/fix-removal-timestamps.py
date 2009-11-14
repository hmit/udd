#!/usr/bin/env python

# This file is a part of the Ultimate Debian Database
# <http://wiki.debian.org/UltimateDebianDatabase>
#
# Copyright (C) 2009 Serafeim Zanikolas <serzan@hellug.gr>
#
# This file is distributed under the terms of the General Public
# License version 3 or (at your option) any later version.

"""
Quick hack to fix broken timestamp entries in ftp-archive package removals
history file.

Before:

    [Date: Tue, 27 Oct 2009 19:41:19 +0000
    ] [ftpmaster: Archive Administrator]

After applying this script:

    [Date: Tue, 27 Oct 2009 19:41:19 +0000] [ftpmaster: Archive Administrator]
"""

import sys

prev_line = None
for line in sys.stdin:
    line = line.rstrip()
    if prev_line is None:
        prev_line = line
        continue
    if line.startswith("] [ftpmaster:"):
        assert prev_line
        print "%s%s" % (prev_line, line)
        prev_line = None
    else:
        print prev_line
        prev_line = line
if prev_line:
    print prev_line
