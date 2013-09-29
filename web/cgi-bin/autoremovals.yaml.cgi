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
  entry['bugs'] = row['bugs'].split(",")
  entry['last_checked'] = datetime.utcfromtimestamp(row['last_checked'])
  first_seen = datetime.utcfromtimestamp(row['first_seen'])
  # in the initial stage, the autoremovals happen after 15 days instead of 10
  removal_date = first_seen + timedelta(15)
  entry['removal_date'] = removal_date
  data[row['source']] = entry

print yaml.dump(data, default_flow_style=False)

