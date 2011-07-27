#!/usr/bin/env python

# This file is a part of the Ultimate Debian Database
# <http://wiki.debian.org/UltimateDebianDatabase>
#
# Copyright (C) 2009 Serafeim Zanikolas <serzan@hellug.gr>
#
# This file is distributed under the terms of the General Public
# License version 3 or (at your option) any later version.

""" import data about the removal of packages (from the debian archive) in UDD

Raw data source: http://ftp-master.debian.org/removals-full.txt

Sample removal batch from the above file:

=========================================================================
[Date: Tue,  9 Jan 2001 20:52:51 -0500] [ftpmaster: James Troup]
Removed the following packages from unstable:

        dsniff |      2.3-1 | source, i386
Closed bugs: 81709

------------------- Reason -------------------
ROM; moved to non-US (now depends on libssl)
----------------------------------------------
=========================================================================

Note that a removal batch may have many packages removed (unlike the one
above, where only dsniff is removed).

This script when ran as a standalone script will not connect to the database
but will instead run a basic sanity test (to make sure that the input file
hasn't changed in a way that would break the script).
"""

import sys
import re

from gatherer import gatherer
from aux import quote

def fail(msg):
    sys.stderr.write("%s\n" % msg)
    exit(1)

def parse_removals(stream):
    # We expect lines to appear in the order below. parser.curr_func is set to
    # one of several functions based on how we expect to show up next in the
    # file.
    #
    # date; ftp-master name
    # distrib
    # skip_line*
    # pkg name | version | arch[, arch] <-- >=1 lines like these
    # skip_line*
    #------------------- Reason -------------------
    # requestor; reasons

    parser = Parser()
    for line in stream:
        if parser.skip_line(line):
            continue
        if parser.curr_func(line):
            continue
    return parser.removal_batches

def get_gatherer(connection, config, source):
    return removals_gatherer(connection, config, source)

class removals_gatherer(gatherer):
    """import removals into the database"""

    def __init__(self, connection, config, source):
        gatherer.__init__(self, connection, config, source)
        self.assert_my_config('path', 'table')

    def run(self):
        conf = self.my_config

        try:
            input_fd = open(conf['path'])
        except IOError:
            fail('failed to open %s' % conf['path'])

        batch_removals = parse_removals(input_fd)

        pkg_removal_table = conf['table']
        pkg_removal_batch_table = "%s_batch" % conf['table']

        cur = self.cursor()
        cur.execute('DELETE FROM %s' % pkg_removal_table)
        cur.execute('DELETE FROM %s' % pkg_removal_batch_table)

        # insert data for batches of removals
        cur.execute('PREPARE batch_removals_insert ' \
                        'AS INSERT INTO %s (id, time, ftpmaster, ' \
                                           'distribution, requestor, ' \
                                           'reasons)' \
                        'VALUES ($1, $2, $3, $4, $5, $6)' \
                    % pkg_removal_batch_table)
        for i, batch_removal in enumerate(batch_removals):
            cur.execute('EXECUTE batch_removals_insert ' \
                              '(%s, %s, %s, %s, %s, %s)' \
                            % (i, quote(batch_removal.timestamp),
                               quote(batch_removal.ftpmaster),
                               quote(batch_removal.distribution),
                               quote(batch_removal.requestor),
                               quote(batch_removal.reasons)))
        cur.execute('DEALLOCATE batch_removals_insert')
        cur.execute("VACUUM ANALYZE %s" % pkg_removal_batch_table)

        # insert data for removals of individual packages
        cur.execute('PREPARE pkg_removal_insert ' \
                        'AS INSERT INTO %s (batch_id, name, version, ' \
                                           'arch_array)' \
                        'VALUES ($1, $2, $3, $4)' % pkg_removal_table)
        for i, batch_removal in enumerate(batch_removals):
            for pkg in batch_removal.packages:
                cur.execute('EXECUTE pkg_removal_insert (%s, %s, %s, %s)' \
                                % (i, quote(pkg.name), quote(pkg.version),
                                    quote("{%s}" % ",".join(pkg.arches))))
        cur.execute('DEALLOCATE pkg_removal_insert')
        cur.execute("VACUUM ANALYZE %s" % pkg_removal_table)

def test(filename, removal_batches):
    """compare the number of parsed packages against those counted with a
    shell one-liner"""

    from commands import getstatusoutput

    status, npackage_removals_via_grep = getstatusoutput(\
            "egrep '[^ ]+ *\| *[^ ]+ *\| *[^ ]+' %s | " \
            "awk '-F|' '{print $1, $2}' | sed 's/  */ /g' | wc -l" \
                % filename)
    if status != 0:
        fail("failed to extract removed packages with grep")
    npackage_removals_via_grep = int(npackage_removals_via_grep)

    npackage_removals_via_python = 0
    ftpmasters = set()
    distribs = set()
    package_removals_via_python = set()
    for pkg_rm_batch in removal_batches:
        npackage_removals_via_python += len(pkg_rm_batch.packages)
        ftpmasters.add(pkg_rm_batch.ftpmaster)
        distribs.add(pkg_rm_batch.distribution)

    if npackage_removals_via_grep != npackage_removals_via_python:
        fail("%d removed packages have been parsed but %d were expected" % \
                (npackage_removals_via_python, npackage_removals_via_grep))

    print '%d packages were removed from %d distributions, in %d\n' \
          'batches of removals done by %d ftpmaster members' % \
            (npackage_removals_via_python, len(distribs),
             len(removal_batches), len(ftpmasters))


class Package(object):
    """container for a single removed package"""
    def __init__(self, name, version, arches):
        self.name = name
        self.version = version
        self.arches = [arch.strip() for arch in arches.split(",")]

    def __str__(self):
        return '%s-%s' % (self.name, self.version)

class PackageRemovalBatch(object):
    """container for a removal batch (refers to one or more packages)"""
    def __init__(self, timestamp, ftpmaster):
        self.timestamp = timestamp
        self.ftpmaster = ftpmaster
        self.distribution = None
        self.packages = []
        self.requestor = None
        self.reasons = None

    def add_pkg(self, pkg):
        self.packages.append(pkg)

    def __str__(self):
        return "removal of %s at %s by %s from %s" \
                % ("\n".join([str(p) for p in self.packages]), \
                self.timestamp, self.ftpmaster, self.distribution)

class Parser(object):
    date_master_pat = re.compile(r"\[Date: ([^\]]+)] \[ftpmaster: ([^\]]+)\]")
    distrib_pat = re.compile(r"Removed the following packages from ([a-z-]+)[:,]*")
    pkg_version_arches_pat = re.compile(r"\s*(\S*) *\|\s*(\S+)\s*\|\s*(.*)$")
    reason_pat = re.compile("-+\s*Reason\s*-+")
    rene_pat = re.compile("(\[rene[^\]]*\])\s*(.*)")

    def __init__(self):
        self.removal_batch = None
        self.removal_batches = []
        self.curr_func = self.parse_removal

    def skip_line(self, line):
        if line.isspace() or line == "":
            return True

    def parse_removal(self, line):
        match = Parser.date_master_pat.search(line)
        if match:
            timestamp, ftpmaster = match.groups()
            self.removal_batch = PackageRemovalBatch(timestamp, ftpmaster)
            self.curr_func = self.parse_distrib
            return True

    def parse_distrib(self, line):
        match = Parser.distrib_pat.search(line)
        if match:
            self.removal_batch.distribution = match.group(1)
            self.curr_func = self.parse_pkg_version_arch_or_reason_header
            return True

    def parse_pkg_version_arch_or_reason_header(self, line):
        match = Parser.pkg_version_arches_pat.search(line)
        if match:
            pkg, version, arches = match.groups()
            pkg_obj = Package(pkg, version, arches)
            if self.removal_batch:
                self.removal_batch.add_pkg(pkg_obj)
                return True
        elif self.removal_batch:
            match = Parser.reason_pat.search(line)
            if match:
                self.curr_func = self.parse_requestor_reasons
                return True

    def parse_requestor_reasons(self, line):
        match = Parser.rene_pat.search(line)
        if match:
            self.removal_batch.requestor = match.group(1)
            self.removal_batch.reasons = match.group(2)
        else:
            fields = line.split(';')
            if fields == 1: # assume no requestor
                self.removal_batch.requestor = None
                self.removal_batch.reasons = line
            else:
                self.removal_batch.requestor = fields[0]
                self.removal_batch.reasons = ";".join(fields[1:])
        self.curr_func = self.conclude_batch
        return True # assume that we always get fed the correct line

    def conclude_batch(self, line):
        if line.startswith("---------") and self.removal_batch is not None:
            self.removal_batches.append(self.removal_batch)
            self.removal_batch = None
            self.curr_func = self.parse_removal
            return True

if '__main__' == __name__:
    import os

    try:
        filename = sys.argv[1]
        input_fd = open(filename)
    except IndexError:
        fail("syntax: %s <removals-file>\n" \
             "(when run from the command line will only prints stats)" \
                % os.path.basename(sys.argv[0]))
    except IOError:
        fail("failed to open %s" % filename)

    batch_removals = parse_removals(input_fd)
    test(filename, batch_removals)
