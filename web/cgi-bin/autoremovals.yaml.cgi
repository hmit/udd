#!/usr/bin/python
#-*- coding: utf8
#

from psycopg2 import connect
from psycopg2.extras import DictCursor
from datetime import datetime
from datetime import timedelta
import yaml;
import pprint;

print "Content-Type: text/plain\n";

query = "select * from testing_autoremovals order by first_seen";

conn = connect(database='udd', port=5452, host='localhost', user='guest')
cur = conn.cursor(cursor_factory=DictCursor)
cur.execute(query)
rows = cur.fetchall()
cur.close()
conn.close()

data = {}

for row in rows:
  entry = {}
  entry['source'] = row['source']
  entry['version'] = row['version']
  if row['bugs'] == "":
    entry['bugs'] = []
    entry['dependencies_only'] = True
  else:
    entry['bugs'] = row['bugs'].split(",")
    entry['dependencies_only'] = False
  if row['rdeps'] != "":
    entry['rdeps'] = row['rdeps'].split(",")
  if row['buggy_deps'] != "":
    entry['buggy_dependencies'] = row['buggy_deps'].split(",")
  if row['bugs_deps'] != "":
    entry['bugs_dependencies'] = row['bugs_deps'].split(",")
  entry['last_checked'] = datetime.utcfromtimestamp(row['last_checked'])
  entry['removal_date'] = datetime.utcfromtimestamp(row['removal_time'])
  data[row['source']] = entry

print yaml.dump(data, default_flow_style=False)

