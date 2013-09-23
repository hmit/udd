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

query = "select * from key_packages order by source";

conn = connect(database='udd', port=5452, host='localhost', user='guest')
cur = conn.cursor(cursor_factory=DictCursor)
cur.execute(query)
rows = cur.fetchall()
cur.close()
conn.close()

data = []

for row in rows:
  entry = {}
  entry['source'] = row['source']
  data.append(entry)

print yaml.dump(data, default_flow_style=False)

