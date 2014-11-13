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
# Display orphaned packages with Ubuntu changes

from psycopg2 import connect
from re import split, sub
import yaml
f = open('../ubuntu-releases.yaml')
urel = yaml.safe_load(f)['devel']

query = 'SELECT s.source, s.version, u.version FROM sources_uniq s JOIN ubuntu_sources u ON u.source = s.source WHERE s.source IN ( SELECT source FROM orphaned_packages WHERE type = \'O\' UNION SELECT source FROM sources_uniq WHERE maintainer_name LIKE \'%Debian QA%\' AND release = \'sid\' ) AND s.release = \'sid\' AND u.release = \''+urel+'\' AND u.version LIKE \'%ubuntu%\' ORDER BY s.source'

conn = connect(database='udd', port=5452, host='localhost', user='guest')
cur = conn.cursor()
cur.execute(query)
rows = cur.fetchall()
cur.close()
conn.close()

print '''Content-Type: text/html\n\n
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Orphaned packages with Ubuntu changes</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
</head>
<body>
<table border="1">
<tr>
<th>Package</th>
<th>Debian version</th>
<th>Ubuntu version</th>
<th>Ubuntu patches</th>
</tr>
'''

for row in rows:
    print '<tr><td>%s</td>' % row[0]
    print ('<td><a href="http://packages.qa.debian.org/%s">%s</a></td>' %
           (row[0], row[1]))
    print ('<td><a href="http://launchpad.net/ubuntu/+source/%s">%s</a></td>' %
           (row[0], row[2]))
    print ('''<td><a href="http://ubuntudiff.debian.net/?query=%s">
              Show patch</a>''' % row[0])
    print '</td></tr>'

print '''</table>
<hr/>
<p>
<a href="http://validator.w3.org/check?uri=referer">
<img src="http://www.w3.org/Icons/valid-xhtml11"
alt="Valid XHTML 1.1" height="31" width="88" />
</a>
</p>
</body>
</html>'''
