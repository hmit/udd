#!/usr/bin/python

import cgi
from psycopg2 import connect
import json

form = cgi.FieldStorage()

term = form.getvalue('term') or ''
term = '%' + term + '%'

query = "SELECT DISTINCT maintainer_email AS value, maintainer AS label FROM sources WHERE maintainer LIKE %s"

conn = connect(database='udd', port=5452, host='localhost', user='guest')
cur = conn.cursor()
cur.execute(query, [term])
rows = cur.fetchall()
cur.close()
conn.close()

# FIXME: Surely there's a way to get this straight out of the DB.
result = []
for row in rows:
	temp = {}
	temp["value"] = row[0]
	temp["label"] = row[1]
	result.append(temp)

print "Content-Type: text/json\n\n";
print json.dumps(result)
