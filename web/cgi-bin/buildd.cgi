#!/usr/bin/python                                 
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

from cgi import FieldStorage
from psycopg2 import connect
from re import split, sub
from urllib import urlopen

packages = {}
suites = ('sid', 'experimental')
roles = ('maintained', 'team', 'NMUed', 'sponsored', 'QA/other')
conn = connect(database='udd', port=5441, host='localhost', user='guest')
cur = conn.cursor()
name = FieldStorage().getvalue('maint')

for suite in suites:
    if not name:
        break
    if not packages.has_key(suite):
        packages[suite] = {}

    query = """WITH last_sources AS (
                 SELECT source, max(version) AS version, maintainer
                 FROM sources_uniq
                 WHERE release = '%s'
                 AND architecture != 'all'
                 GROUP BY source, maintainer )
               SELECT s.source
               FROM last_sources s
               WHERE s.maintainer LIKE '%%%s%%'
               ORDER BY s.source""" % (suite, name)
    cur.execute(query)
    rows = cur.fetchall()
    if len(rows):
        packages[suite][roles[0]] = rows

    query = """WITH last_sources AS (
                 SELECT source, max(version) AS version, uploaders
                 FROM sources_uniq
                 WHERE release = '%s'
                 AND architecture != 'all'
                 GROUP BY source, uploaders )
               SELECT s.source
               FROM last_sources s
               WHERE s.uploaders LIKE '%%%s%%'
               ORDER BY s.source""" % (suite, name)
    cur.execute(query)
    rows = cur.fetchall()
    if len(rows):
        packages[suite][roles[1]] = rows

    query = """WITH last_sources AS (
                 SELECT source, max(version) AS version
                 FROM sources_uniq
                 WHERE release = '%s'
                 AND architecture != 'all'
                 GROUP BY source )
               SELECT s.source
               FROM last_sources s
               JOIN upload_history u
               ON u.source = s.source
               AND u.version = s.version
               WHERE u.signed_by LIKE '%%%s%%'
               AND u.nmu = True
               ORDER BY s.source"""  % (suite, name)
    cur.execute(query)
    rows = cur.fetchall()
    if len(rows):
        packages[suite][roles[2]] = rows

    query = """WITH last_sources AS (
                 SELECT source, max(version) AS version, maintainer, uploaders
                 FROM sources_uniq
                 WHERE release = '%(suite)s'
                 AND architecture != 'all'
                 GROUP BY source, maintainer, uploaders )
               SELECT s.source
               FROM last_sources s
               JOIN upload_history u
               ON u.source = s.source
               AND u.version = s.version               
               WHERE u.signed_by LIKE '%%%(name)s%%'
               AND u.nmu = False
               AND s.maintainer NOT LIKE '%%%(name)s%%'
               AND(
                 s.uploaders NOT LIKE '%%%(name)s%%'
                 OR s.uploaders IS NULL )
               ORDER BY s.source""" % {'suite': suite, 'name': name}
    cur.execute(query)
    rows = cur.fetchall()
    if len(rows):
        packages[suite][roles[3]] = rows

    query = """WITH last_sources AS (
                 SELECT source, max(version) AS version, maintainer, uploaders
                 FROM sources_uniq
                 WHERE release = '%(suite)s'
                 AND architecture != 'all'
                 GROUP BY source, maintainer, uploaders )
               SELECT s.source
               FROM last_sources s
               JOIN upload_history u
               ON u.source = s.source
               AND u.version = s.version
               WHERE u.changed_by LIKE '%%%(name)s%%'
               AND u.nmu = False
               AND s.maintainer NOT LIKE '%%%(name)s%%'
               AND(
                 s.uploaders NOT LIKE '%%%(name)s%%'
                 OR s.uploaders IS NULL )
               ORDER BY s.source""" % {'suite': suite, 'name': name}
    cur.execute(query)
    rows = cur.fetchall()
    if len(rows):
        packages[suite][roles[4]] = rows

cur.close()
conn.close()

print """Content-Type: text/html\n\n
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Maintainer's buildd status</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<link rel="StyleSheet" type="text/css" href="https://buildd.debian.org/status/media/pkg.css" />
<link rel="StyleSheet" type="text/css" href="https://buildd.debian.org/status/media/status.css" >
<style type="text/css">
#header {
    height:90px;
    margin:0 0 10px 0;
    font-size:0.9em;
    background:#f4f4f4 bottom left repeat-x;
    line-height:20px;
    border-collapse:collapse;
    border:1px solid #d8d8d8;
}
</style>
<script type="text/javascript">
function toggleBuildd(suite) {
    var children = document.getElementsByTagName("*");
    for (var i = 0; i < children.length; i++) {
        if(!children[i].hasAttribute("class"))
            continue;
        c = children[i].getAttribute("class").split(" ");
        for(var j = 0; j < c.length; j++) {
            if(c[j] == suite) {
                if (children[i].style.display == '')
                    children[i].style.display = 'none';
                else children[i].style.display = '';
            }
        }
    }
}
</script>
</head>
<body>
<table id="header" width="100%%">
<tr>
<td><img src="http://www.debian.org/logos/openlogo.svg" alt="Debian Logo" height="60" /></td>
<td><h1 class="header">Maintainer's buildd status</h1></td>
</tr>
</table>
<hr>"""

if name:
    for suite in suites:
        for role in roles:
            if not packages[suite].has_key(role):
                continue
            print '<h3>Buildd status for %s packages in %s</h3>' % (role, suite)
            url = 'https://buildd.debian.org/status/package.php?p='
            for row in packages[suite][role]:
                url += "%s%%2C" % row[0].replace('+', '%2B')
            url += '&suite=%s&compact=compact' % suite
            data = urlopen(url).read()
            data = ''.join(split('(<table class="data">)', data)[1:])
            data = split('</div><div id="footer">', data)[0]
            data = split('(</table>)', data, 1)
            print sub(r'<a href="([ap])', r'<a href="https://buildd.debian.org/status/\1', "".join(data[:-1]))
            if "".join(data[2:]).startswith('<p>'):
                print '<h5 onclick="toggleBuildd(\'%s%s\')"> show/hide details</h5>' % (suite, role)
                print '<div class="%s%s" style="display: none">' % (suite, role)
                print "".join(data[2:])
                print '</div>'
            print '<hr>'
else:
    print '<form method="post" action="buildd.cgi">'
    print '<p>Maintainer name: <input type="text" name="maint"/>'
    print '<input type="submit" value="Submit"/></p></form>'

print '</body></html>'

