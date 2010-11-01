#!/usr/bin/env python

"""
This script imports the deferred queue status from
http://ftp-master.debian.org/deferred/status
"""

from debian_bundle import deb822
from os import access, mkdir, unlink, W_OK
from sys import stderr
import aux
from aux import quote
from gatherer import gatherer
import email.Utils
import re
from time import ctime
from psycopg2 import IntegrityError, ProgrammingError
import urllib

def get_gatherer(connection, config, source):
  return deferred_gatherer(connection, config, source)

DEBUG=0
def to_unicode(value, encoding='utf-8'):
  if isinstance(value, str):
    return value.decode(encoding)
  else:
    return unicode(value)

class deferred_gatherer(gatherer):
  "This class imports the data from Deferred queue into the database"

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('url')

  def run(self):
    my_config = self.my_config

    cur = self.cursor()

    cur.execute("PREPARE d_insert AS INSERT INTO deferred (source, version, distribution, urgency, date, delayed_until, delay_remaining, changed_by, changed_by_name, changed_by_email, maintainer, maintainer_name, maintainer_email, changes) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)")
    q_deferred = "EXECUTE d_insert(%(Source)s, %(Version)s, %(Distribution)s, \
            %(Urgency)s, %(Date)s, %(Delayed-Until)s, %(Delay-Remaining)s, \
            %(Changed-By)s, %(Changed-By_name)s, %(Changed-By_email)s, \
            %(Maintainer)s, %(Maintainer_name)s, %(Maintainer_email)s, \
            %(Changes)s)"
    cur.execute("PREPARE da_insert AS INSERT INTO deferred_architecture (source, version, architecture) VALUES ($1, $2, $3)")
    q_defarch = "EXECUTE da_insert(%(Source)s, %(Version)s, %(Architecture)s)"
    cur.execute("PREPARE da_binary AS INSERT INTO deferred_binary (source, version, package) VALUES ($1, $2, $3)")
    q_defbin = "EXECUTE da_binary(%(Source)s, %(Version)s, %(Package)s)"
    cur.execute("PREPARE da_closes AS INSERT INTO deferred_closes (source, version, id) VALUES ($1, $2, $3)")
    q_defcloses = "EXECUTE da_closes(%(Source)s, %(Version)s, %(Id)s)"

    cur.execute("DELETE FROM deferred_closes")
    cur.execute("DELETE FROM deferred_binary")
    cur.execute("DELETE FROM deferred_architecture")
    cur.execute("DELETE FROM deferred")

    d_list = []
    da_list = []
    db_list = []
    dc_list = []
    for current in deb822.Deb822.iter_paragraphs(urllib.urlopen(my_config['url'])):
      current['Changed-By_name'], current['Changed-By_email'] = email.Utils.parseaddr(current['Changed-By'])
      current['Maintainer_name'], current['Maintainer_email'] = email.Utils.parseaddr(current['Maintainer'])
      d_list.append(current)
      for arch in set(current['Architecture'].split()):
        current_arch = {'Source': current['Source'], 'Version': current['Version']} 
        current_arch['Architecture'] = arch
        da_list.append(current_arch)
      for binary in set(current['Binary'].split()):
        current_binary = {'Source': current['Source'], 'Version': current['Version']} 
        current_binary['Package'] = binary
        db_list.append(current_binary)
      for bug in set(current['Closes'].split()):
        current_c = {'Source': current['Source'], 'Version': current['Version']} 
        current_c['Id'] = bug
        dc_list.append(current_c)

    cur.executemany(q_deferred, d_list)
    cur.executemany(q_defarch, da_list)
    cur.executemany(q_defbin, db_list)
    cur.executemany(q_defcloses, dc_list)
    cur.execute("ANALYZE deferred")
    cur.execute("ANALYZE deferred_architecture")
    cur.execute("ANALYZE deferred_binary")
    cur.execute("ANALYZE deferred_closes")

# vim:set et tabstop=2:0
