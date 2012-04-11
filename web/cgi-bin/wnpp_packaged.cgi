#!/usr/bin/python
#-*- coding: utf8
#
# Copyright (C) 2011 Luca Falavigna <dktrkranz@debian.org>
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Display buildd status for your packages

from psycopg2 import connect


query = '''WITH qabugs AS (
             SELECT substring(title from E': (\\\S+) --') AS package, id, title
             FROM bugs
             WHERE source = 'wnpp'
             AND status != 'done'
             AND title SIMILAR TO '(RF|IT)P:%' )
           SELECT package, id, title, (
             SELECT source
             FROM sources_uniq
             WHERE source = package
             AND release IN ('sid', 'experimental') ) AS available
           FROM qabugs q
           WHERE package IN (
             SELECT DISTINCT source
             FROM upload_history)
           ORDER BY id'''

print '''Content-Type: text/html\n\n
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Open RFP/ITP bugs for already packaged software</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
</head>
<body>
<table id="header" width="100%" border="3">
<tr>
<th>Package</th>
<th>Bug</th>
<th>Title</th>
</tr>'''

conn = connect(database='udd', port=5441, host='localhost', user='guest')
cur = conn.cursor()
cur.execute(query)
rows = cur.fetchall()
cur.close()
conn.close()

for r in rows:
    if r[3]:
        bold = '<b>'
        nobold = '</b>'
    else:
        bold = ''
        nobold = ''
    print '<tr>\n<td>%s' % bold
    print '<a href="http://packages.qa.debian.org/%s">%s</a>' % (r[0], r[0])
    print '%s</td><td>%s' % (nobold, bold)
    print '<a href="http://bugs.debian.org/%s">%s</a>' % (r[1], r[1])
    print '%s</td><td>%s' % (nobold, bold)
    print r[2].replace('<', '&lt;').replace('>', '&gt;')
    print '%s</td></tr>' % nobold

print '''</table>
<p><a href="http://validator.w3.org/check?uri=referer">
<img src="http://www.w3.org/Icons/valid-xhtml11" alt="Valid XHTML 1.1"
height="31" width="88"/></a>
</p>
</body>
</html>'''
