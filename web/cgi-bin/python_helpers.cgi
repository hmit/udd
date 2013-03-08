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
helpers_list = ('central', 'support')
query = '''WITH tagged_bugs AS (
             SELECT b.source, b.id
             FROM bugs b
             JOIN bugs_usertags bt ON bt.id = b.id
             WHERE bt.email = 'debian-python@lists.debian.org'
             AND bt.tag = 'py%(helper)s-deprecation')
           SELECT s.source, max(s.version) AS version,
           s.maintainer_name AS maintainer, s.release, b.id AS bug
           FROM sources_uniq s
           LEFT OUTER JOIN tagged_bugs b ON (b.source = s.source
             AND b.source = s.source)
           WHERE s.release IN ('sid', 'experimental')
           AND (s.build_depends LIKE '%%python-%(helper)s%%'
             OR s.build_depends_indep LIKE '%%python-%(helper)s%%')
           GROUP BY s.source, s.maintainer_name, s.release, b.id
           ORDER BY s.source, version DESC'''

conn = connect(database='udd', port=5452, host='localhost', user='guest')
cur = conn.cursor()
for helper in helpers_list:
    cur.execute(query % {'helper': helper})
    helpers['python-%s' % helper] = cur.fetchall()
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

for helper in helpers_list:
    print('''<h1>Packages build-depending on python-%s</h1>
<table border="1" cellpadding="3">
<tr>
<th>Package</th>
<th>Version</th>
<th>Maintainer</th>
<th>Release</th>
<th>Transition bug</th>
</tr>''' % helper)
    for row in helpers['python-%s' % helper]:
        print('<tr>')
        print('<td><a href="http://packages.qa.debian.org/%s">%s</a></td>' %
           (row[0], row[0]))
        print('<td>%s</td>' % row[1])
        print('<td>%s</td>' % row[2])
        print('<td>%s</td>' % row[3])
        if row[4]:
            print('<td><a href="http://bugs.debian.org/%s">%s</a></td>' %
                  (row[4], row[4]))
        else:
            print('<td></td>')
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
