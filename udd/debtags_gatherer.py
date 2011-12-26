#!/usr/bin/env python

# This file is a part of the Ultimate Debian Database
# <http://wiki.debian.org/UltimateDebianDatabase>
#
# Copyright (C) 2008 Stefano Zacchiroli <zack@debian.org>
#
# This file is distributed under the terms of the General Public
# License version 3 or (at your option) any later version.

""" import debtags data into the database

tags information are downloaded from SVN (though via http/websvn to
avoid an extra dependency on svn), see the "update-command"
configuration of the debtags gatherer
"""

import re
import sys

from gatherer import gatherer
from aux import quote


# a "live" instance of the tag database, whose lines should match the regexp
# below, is at: http://svn.debian.org/viewsvn/*checkout*/debtags/tagdb/tags
tag_line_RE = re.compile(r'^(?P<pkg>[a-z0-9+-\.]+):\s+(?P<tags>[\w:+-]+(,\s+[\w:+-]+)*)$')
tag_sep_RE = re.compile(r',\s+')
# field_sep_RE = re.compile(r':\s+')

def parse_tags(fname):
    global tag_line_RE, tag_sep_RE

    line_no = 0
    tags_db = file(fname)
    for line in tags_db:
        line_no += 1
        # Packages without tags are represented as ^package$; ignore these
        if not ": " in line:
            continue
        line = line.strip()
        parsed_line = tag_line_RE.match(line)
        if not parsed_line:
            print >> sys.stderr, \
                "debtags: can not parse line %d: %s" % (line_no, line)
        else:
            parts = parsed_line.groupdict()
            pkg = parts['pkg']
            for tag in tag_sep_RE.split(parts['tags']):
                yield (pkg, tag)
    tags_db.close()


def get_gatherer(connection, config, source):
    return debtags_gatherer(connection, config, source)


class debtags_gatherer(gatherer):
    """import debtags data into the database"""
    
    def __init__(self, connection, config, source):
        gatherer.__init__(self, connection, config, source)
        self.assert_my_config('path', 'table')

    def run(self):
        conf = self.my_config
        cur = self.cursor()
        cur.execute('DELETE FROM %s' % conf['table'])
        cur.execute('PREPARE debtags_insert ' \
                        'AS INSERT INTO %s (package, tag) VALUES ($1, $2)' \
                        % conf['table'])
        for (pkg, tag) in parse_tags(conf['path']):
            cur.execute('EXECUTE debtags_insert (%s, %s)' \
                            % (quote(pkg), quote(tag)))
        cur.execute('DEALLOCATE debtags_insert')
        cur.execute("ANALYZE %s" % conf['table'])


def test():
    """given a filename on the cmdline, print all tuples <pkg, tag>
    that would be inserted in the db. For debugging/testing purposes.
    """
    for (pkg, tag) in parse_tags(sys.argv[1]):
        print "%s\t%s" % (pkg, tag)

if __name__ == '__main__':
    test()
