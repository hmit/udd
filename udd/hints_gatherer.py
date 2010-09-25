# Last-Modified: <Sun Aug 17 12:13:02 2008>
# This file is part of the Ultimate Debian Database Project

from gatherer import gatherer
import aux
from glob import glob
import gzip
import psycopg2
import sys
import email.Utils
import os.path
import re

def get_gatherer(config, connection, source):
  return hints_gatherer(config, connection, source)

class Hint(object):
    """Base clase for representing a hint.

    It also acts as a factory: Hint(hintame, *args) will return an object of
    the appropriate class (eg. UnstableToTestingHint).
    """

    def __init__(self, type, *args):
        starts_with_letter = re.compile(r'(?i)^[a-z]')

        self.type = type
        self.pkgs = []
        self.versionmap = {} # original versions on the hint
        self.archmap = {}

        for pkg in args:
            if '/' in pkg:
                pkg, ver = pkg.split('/', 1)
                if starts_with_letter.search(ver):
                    # Package names start with digits, so assume
                    # this is an architecture.  This will break if
                    # an architecture name ever starts with a digit
                    # but that seems unlikely.
                    if '/' in ver:
                        arch, ver = ver.split('/', 1)
                    else:
                        arch = ver
                        ver = ''
                else:
                    arch = ''
            else:
                ver = ''
                arch = ''

            src = pkg
            if src.startswith('-'):
                src = src[1:]
            self.pkgs.append(src)

            self.versionmap[src] = ver
            if len(arch) > 0:
                if src not in self.archmap:
                    self.archmap[src] = set()
                self.archmap[src].add(arch)

class hints_gatherer(gatherer):
  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    if not 'path' in self.my_config:
      raise aux.ConfigException('path not specified for source ' + source)

  def tables(self):
    return [ 'hints' ]

  RE_COMMENT = re.compile(r'^\s*#')
  RE_BLANKLINE = re.compile(r'^\s*$')
  def parse_hints(self, path):
    files = glob(path + '/*')
    files.sort()
    hints = []
    for file in files:
        f = open(file)
        comments = []
        lc = 0
        for line in f:
            lc += 1
            line = line.rstrip('\r\n')
            if self.RE_COMMENT.search(line):
                comments.append(line)
                continue
            elif self.RE_BLANKLINE.search(line):
                comments = []
                continue
            elif line.startswith('finished'):
                break
            hint = Hint(*line.split())
            hints.append([hint, os.path.basename(file), '\n'.join(comments)])
    return hints

  def run(self):
    path = self.my_config['path']

    hints = self.parse_hints(path)

    cursor = self.cursor()
    cursor.execute("PREPARE h_insert AS INSERT INTO hints (source, version, architecture, type, file, comment) VALUES ($1, $2 , $3, $4, $5, $6)")
    cursor.execute("DELETE FROM hints")
    query = "EXECUTE h_insert(%(source)s, %(version)s, %(arch)s, %(type)s, %(file)s, %(comment)s)"
    hs = []
    for hint in hints:
        h = {}
        h['file'] = hint[1]
        h['comment'] = hint[2]
        h['type'] = hint[0].type
        for src in hint[0].pkgs:
            h['source'] = src
            if hint[0].versionmap.has_key(src):
                h['version'] = hint[0].versionmap[src]
                if h['version'] == '':
                    h['version'] = None
            else:
                h['version'] = None
            if hint[0].archmap.has_key(src):
                h['arch'] = ' '.join(hint[0].archmap[src])
            else:
                h['arch'] = None
            hs.append(h.copy())
    cursor.executemany(query, hs)
    cursor.execute("DEALLOCATE h_insert")
    cursor.execute("ANALYZE hints")
