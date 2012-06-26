#!/usr/bin/python
#
# Copyright (C) 2010-2011 Luca Falavigna <dktrkranz@debian.org>
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
# Extract from UDD Python packages with outstanding noteworthy bugs

from psycopg2 import connect

query_rc = """
SELECT DISTINCT all_bugs.id, all_bugs.source, title, severity
FROM all_bugs
INNER JOIN sources_uniq
ON sources_uniq.source = all_bugs.source
WHERE status != 'done'
AND severity in ('critical', 'grave', 'serious')
AND release = 'sid'
AND (maintainer LIKE '%python-apps-team%'
OR maintainer LIKE '%python-modules-team%'
OR uploaders LIKE '%python-apps-team%'
OR uploaders LIKE '%python-modules-team%')
ORDER BY all_bugs.source;"""

query_help = """
SELECT DISTINCT all_bugs.id, all_bugs.source, title, severity
FROM all_bugs
INNER JOIN sources_uniq
ON sources_uniq.source = all_bugs.source
INNER JOIN bugs_tags
ON all_bugs.id = bugs_tags.id
WHERE status != 'done'
AND release = 'sid'
AND tag LIKE '%help%'
AND (maintainer LIKE '%python-apps-team%'
OR maintainer LIKE '%python-modules-team%'
OR uploaders LIKE '%python-apps-team%'
OR uploaders LIKE '%python-modules-team%')
ORDER BY all_bugs.source;"""

query_usertag = """
SELECT DISTINCT all_bugs.id, all_bugs.source, title, severity
FROM all_bugs
INNER JOIN sources_uniq
ON sources_uniq.source = all_bugs.source
INNER JOIN bugs_usertags
ON all_bugs.id = bugs_usertags.id
WHERE status != 'done'
AND release = 'sid'
AND email LIKE '%debian-python@lists.debian.org%'
AND (maintainer LIKE '%python-apps-team%'
OR maintainer LIKE '%python-modules-team%'
OR uploaders LIKE '%python-apps-team%'
OR uploaders LIKE '%python-modules-team%')
ORDER BY all_bugs.source;"""

conn = connect(database="udd", port=5452, host="localhost", user="guest")
cur = conn.cursor()
cur.execute(query_rc)
rc = cur.fetchall()
cur.close()
cur = conn.cursor()
cur.execute(query_help)
help = cur.fetchall()
cur.close()
cur = conn.cursor()
cur.execute(query_usertag)
usertag = cur.fetchall()
cur.close()
conn.close()

print '''Content-Type: text/html\n\n
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<title>Bugs for DPMT/PAPT packages</title>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8">
</head>
<body>
<h1>Release Critical bugs</h1>
<table>
<tr>
<td><b>ID</b></td>
<td><b>Package</b></td>
<td><b>Title</b></td>
<td><b>Severity</b></td>
</tr>'''
for d in rc:
    print '''<tr>
<td><a href="http://bugs.debian.org/%s">#%s</a></td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
</tr>''' % (d[0], d[0], d[1], d[2], d[3])
print '''</table>
<h1>Bugs needing help</h1>'''
print '''<table>
<tr><td><b>ID</b></td>
<td><b>Package</b></td>
<td><b>Title</b></td>
<td><b>Severity</b></td>
</tr>'''
for d in help:
    print '''<tr>
<td><a href="http://bugs.debian.org/%s">#%s</a></td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
</tr>''' % (d[0], d[0], d[1], d[2], d[3])
print '''</table>
<h1>Bugs with usertag debian-python@lists.debian.org</h1>'''
print '''<table>
<tr>
<td><b>ID</b></td>
<td><b>Package</b></td>
<td><b>Title</b></td>
<td><b>Severity</b></td>
</tr>'''
for d in usertag:
    print '''<tr>
<td><a href="http://bugs.debian.org/%s">#%s</a></td>
<td>%s</td>
<td>%s</td>
<td>%s</td>
</tr>''' % (d[0], d[0], d[1], d[2], d[3])
print '''</table>
</body>
</html>'''
