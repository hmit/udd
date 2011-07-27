#!/usr/bin/env python

"""
This script imports some fields from the Debian LDAP into the database
"""

from aux import quote
from gatherer import gatherer
import ldap
import re

def get_gatherer(connection, config, source):
  return ldap_gatherer(connection, config, source)

class ldap_gatherer(gatherer):

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config()

  def run(self):
    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    cur.execute("DELETE FROM ldap")

    cur.execute("""PREPARE ldap_insert 
      AS INSERT INTO ldap
      (uid, login, cn, sn, expire, location, country, activity_from, activity_from_info, activity_pgp, activity_pgp_info, gecos, birthdate, gender, fingerprint)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)""")

    entries = []
    con = ldap.initialize('ldap://db.debian.org')
    for e in con.search_s('ou=users,dc=debian,dc=org', ldap.SCOPE_SUBTREE, '(&(objectclass=debianAccount)(objectclass=debianDeveloper))'):
      f = e[1]
      if 'activity-from' in f:
        af_date, af_info = f['activity-from'][0].split('] ',2)
        af_date = af_date[1:]
      else:
        af_date = None
        af_info = None
      if 'activity-pgp' in f:
        ag_date, ag_info = f['activity-pgp'][0].split('] ',2)
        ag_date = ag_date[1:]
      else:
        ag_date = None
        ag_info = None


      birthdate = f['birthDate'][0] if 'birthDate' in f else None
      gecos = f['gecos'][0] if 'gecos' in f else None
      gender = int(f['gender'][0]) if 'gender' in f else None
      loc = f['l'][0] if 'l' in f else None
      country = f['c'][0] if 'c' in f else None
      fp = f['keyFingerPrint'][0] if 'keyFingerPrint' in f else None
      expired = ('shadowExpire' in f)

      entries.append((int(f['uidNumber'][0]), f['uid'][0], f['cn'][0], f['sn'][0], expired, loc, country, af_date, af_info, ag_date, ag_info, gecos, birthdate, gender, fp))

    cur.executemany("EXECUTE ldap_insert (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", entries)
    cur.execute("DEALLOCATE ldap_insert")
    cur.execute("VACUUM ANALYZE ldap")

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
