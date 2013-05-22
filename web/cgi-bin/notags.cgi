#!/usr/bin/python
#-*- coding: utf8
#
# Copyright (C) 2013 Stuart Prescott <stuart@debian.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
 Export a list of source and binary packages that are missing debtags
"""

from psycopg2 import connect
from re import split, sub

query = """
SELECT source, string_agg(DISTINCT package, ' ' ORDER BY package) AS packages
  FROM packages
  WHERE package NOT IN (SELECT DISTINCT package FROM debtags)
    AND release = 'sid'
    AND distribution = 'debian'
  GROUP BY source
  ORDER BY source;
"""

conn = connect(database='udd', port=5452, host='localhost', user='guest')
cur = conn.cursor()
cur.execute(query)
rows = cur.fetchall()
cur.close()
conn.close()

print """Content-Type: text/plain

# Packages that have no debtags information in UDD
# Format:
#   source\tpackage1 package2 ...
#"""

for row in rows:
    print "%s\t%s" % (row[0], row[1])
