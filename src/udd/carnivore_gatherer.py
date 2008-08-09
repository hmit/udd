#!/usr/bin/env python

"""
This script imports the carnivore data into the database
See merkel.debian.org:/org/qa.debian.org/carnivore/
"""

from aux import quote
import sys
import gzip
from gatherer import gatherer
import re

def get_gatherer(connection, config):
  return carnivore_gatherer(connection, config)

class carnivore_gatherer(gatherer):
  field_ignores = ["Packages", "X-MIA", "X-Warning"]
  field_to_DB_map = {
    "Using emails":    {"name": "emails", "content-type": "comma-separated"},
    "Known as":        {"name": "names", "content-type": "comma-separated"},
    "DD":              {"name": "login", "content-type": "unique-login"},
    "Key in keyring":  {"name": "keyring_key", "content-type": "multiple entries"},
    "Key in ldap":     {"name": "ldap_key", "content-type": "multiple entries"},
    "Key in emeritus": {"name": "emeritus_key", "content-type": "multiple entries"},
    "Key in removed":  {"name": "removed_key", "content-type": "multiple entries"},
  }

  def __init__(self, connection, config):
    gatherer.__init__(self, connection, config)

  def run(self, source):
    try:
      my_config = self.config[source]
    except:
      raise

    #check that the config contains everything we need:
    for key in ['path', 'emails-table', 'names-table', 'keys-table', 'login-table']:
      if not key in my_config:
        raise aux.ConfigException, "%s not configured for source %s" % (key, source)

    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    for table in ['emails', 'names', 'keys', 'login']:
      cur.execute("DELETE FROM %s" % my_config["%s-table" % table])

    cur.execute("""PREPARE carnivore_email_insert 
      AS INSERT INTO %s (id, email) 
      VALUES ($1, $2)""" % (my_config['emails-table']))
    cur.execute("""PREPARE carnivore_name_insert
      AS INSERT INTO %s (id, name)
      VALUES ($1, $2)""" % (my_config['names-table']))
    cur.execute("""PREPARE carnivore_keys_insert
      AS INSERT INTO %s (id, key, key_type)
      VALUES ($1, $2, $3)""" % (my_config['keys-table']))
    cur.execute("""PREPARE carnivore_login_insert
      AS INSERT INTO %s (id, login)
      VALUES ($1, $2)""" % (my_config['login-table']))

    carnivore_data = open(my_config['path'])
    (line_number, record_number) = (0, 1);
    record = {}
    for line in carnivore_data:
      line_number += 1
      if len(line) == 0 or line.isspace():
        #We require a minimum of data in each record:
        if 'emails' in record and 'names' in record:
          #collect all queries:
          qs = []
          for email in record["emails"]:
            qs.append("EXECUTE carnivore_email_insert (%d, %s)" % (record_number, quote(email)))
          for name in record["names"]:
            qs.append("EXECUTE carnivore_name_insert (%d, %s)" % (record_number, quote(name)))
          if "login" in record:
            qs.append("EXECUTE carnivore_login_insert (%d, %s)" % (record_number, quote(record["login"])))
          for key_type in ['keyring', 'ldap', 'emeritus', 'removed']:
            if ("%s_key" % key_type) in record:
              for key in record["%s_key" % key_type]:
                qs.append("EXECUTE carnivore_keys_insert (%d, %s, '%s')" % (record_number, quote(key), key_type))
          for query in qs:
            cur.execute(query)
        record_number += 1
        record = {}
      else:
        (field, content) = line.split(': ', 1)
        if not (len(field) and len(content)):
          print "Couldn't parse line %d: %s" % (line_number, line)
        else:
          field_info = {}
          if field in carnivore_gatherer.field_ignores:
            continue
          elif carnivore_gatherer.field_to_DB_map[field]:
            info = carnivore_gatherer.field_to_DB_map[field]
          else:
            print "Unknown field in line %d: %s" % (line_number, field)
            continue
      
          if   info["content-type"] == "unique-login":
            match = re.compile('(\w+)@debian.org').search(content)
            record[info["name"]] = match.group(1) 
          elif info["content-type"] == "comma-separated":
            record[info["name"]] = content.rstrip().split(", ")
          elif info["content-type"] == "multiple entries":
            if info["name"] not in record:
              record[info["name"]] = []
            record[info["name"]].append(content.rstrip())

if __name__ == '__main__':
  main()
