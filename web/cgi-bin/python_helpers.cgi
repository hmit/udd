#!/usr/bin/python
#-*- coding: utf8
#
# Copyright (C) 2013 Luca Falavigna <dktrkranz@debian.org>
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
# Display packages build-depending on deprecated Python helpers

from psycopg2 import connect

helpers = {}
pycentral = '''SELECT source, max(version) AS version,
               maintainer_name AS maintainer, release
               FROM sources_uniq
               WHERE release IN ('sid', 'experimental')
               AND (build_depends LIKE '%python-central%'
                 OR build_depends_indep LIKE '%python-central%')
               GROUP BY source, maintainer_name, release
               ORDER BY source, version DESC'''

pysupport = '''SELECT source, max(version) AS version,
               maintainer_name AS maintainer, release
               FROM sources_uniq
               WHERE release IN ('sid', 'experimental')
               AND (build_depends LIKE '%python-support%'
                 OR build_depends_indep LIKE '%python-support%')
               GROUP BY source, maintainer_name, release
               ORDER BY source, version DESC'''

conn = connect(database='udd', port=5452, host='localhost', user='guest')
cur = conn.cursor()
cur.execute(pycentral)
helpers['python-central'] = cur.fetchall()
cur.execute(pysupport)
helpers['python-support'] = cur.fetchall()
pysrows = cur.fetchall()
cur.close()
conn.close()

print('''Content-Type: text/html\n\n
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Packages build-depending on deprecated Python helpers</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
</head>
<body>''')

for helper in ('python-central', 'python-support'):
    print('''<h1>Packages build-depending on %s</h1>
<table border="1">
<tr>
<th>Package</th>
<th>Version</th>
<th>Maintainer</th>
<th>Release</th>
</tr>''' % helper)
    for row in helpers[helper]:
        print('<tr>')
        print('<td><a href="http://packages.qa.debian.org/%s">%s</a></td>' %
           (row[0], row[0]))
        print('<td>%s</td>') % row[1]
        print('<td>%s</td>') % row[2]
        print('<td>%s</td>') % row[3]
        print('</tr>')
    print('</table>')

print('''<p>
<a href="http://validator.w3.org/check?uri=referer">
<img src="http://www.w3.org/Icons/valid-xhtml11"
alt="Valid XHTML 1.1" height="31" width="88" />
</a>
</p>
</body>
</html>''')
