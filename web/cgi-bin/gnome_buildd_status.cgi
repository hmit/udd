#!/usr/bin/python                                 
#
# Copyright (C) 2010 Luca Falavigna <dktrkranz@debian.org>
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
# Display buildd status for pkg-gnome packages

from psycopg2 import connect
from re import split, sub
from urllib import urlopen

conn = connect(database='udd', port=5441, host='localhost', user='guest')
cur = conn.cursor()

query_sid = """SELECT DISTINCT s.source
               FROM sources_uniq s
               INNER JOIN upload_history u
               ON u.source = s.source
               AND u.version = s.version
               WHERE architecture != 'all'
               AND release ='sid'
               AND (s.maintainer_email = 'pkg-gnome-maintainers@lists.alioth.debian.org'
               OR uploaders LIKE '%pkg-gnome-maintainers@lists.alioth.debian.org%')
               ORDER BY s.source"""
query_exp = """SELECT DISTINCT s.source
               FROM sources_uniq s
               INNER JOIN upload_history u
               ON u.source = s.source
               AND u.version = s.version
               WHERE architecture != 'all'
               AND release ='experimental'
               AND (s.maintainer_email = 'pkg-gnome-maintainers@lists.alioth.debian.org'
               OR uploaders LIKE '%pkg-gnome-maintainers@lists.alioth.debian.org%')
               ORDER BY s.source"""

suites = {}
cur.execute(query_sid)
suites['unstable'] = cur.fetchall()
cur.execute(query_exp)
suites['experimental'] = cur.fetchall()
cur.close()
conn.close()

print """Content-Type: text/html\n\n
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>pkg-gnome buildd status</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<link rel="StyleSheet" type="text/css" href="https://buildd.debian.org/pkg.css" />
<link rel="StyleSheet" type="text/css" href="https://buildd.debian.org/status/status.css" />
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
<table id="header" width="100%">
<tr>
<td><img src="http://pkg-gnome.alioth.debian.org/images/gnome-debian-small-trans.png" alt="Debian Logo" /></td>
<td><h1 class="header">Debian GNOME Packaging - Buildd results</h1></td>
</tr>
</table>"""

for s in 'unstable', 'experimental':
    print '<h3 class="%(s)s" onclick="toggleBuildd(\'%(s)s\')">Click to show buildd results for packages in %(s)s</h3>' % {'s': s}
    print '<h3 class="%(s)s" style="display: none" onclick="toggleBuildd(\'%(s)s\')"> Click to hide buildd results for packages in %(s)s</h3>' % {'s': s}
    print '<div class="%s" style="display: none">' % s
    url = 'https://buildd.debian.org/status/package.php?p='
    for d in suites[s]:
        url += "%s+" % d[0].replace('+', '%2B')
    url += '&suite=%s&compact=compact' % s
    data = urlopen(url).read()
    data = split('<div id="jsmode"></div>', data)[1]
    data = split('</div><div id="footer">', data)[0]
    data = sub(r'<a href="([ap])', r'<a href="https://buildd.debian.org/status/\1', data)
    print data
    print '</div>'

print '</body></html>'
