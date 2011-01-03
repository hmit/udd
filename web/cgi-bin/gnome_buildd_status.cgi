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

groups = {}
group_list = ('pkg-gnome', 'pkg-gstreamer', 'pkg-telepathy', 'pkg-utopia')
conn = connect(database='udd', port=5441, host='localhost', user='guest')
cur = conn.cursor()

groups['pkg-gnome'] = ('pkg-gnome-maintainers@lists.alioth.debian.org',
                       {'sid':None, 'experimental':None})
groups['pkg-gstreamer'] = ('pkg-gstreamer-maintainers@lists.alioth.debian.org',
                           {'sid':None, 'experimental':None})
groups['pkg-telepathy'] = ('pkg-telepathy-maintainers@lists.alioth.debian.org',
                           {'sid':None, 'experimental':None})
groups['pkg-utopia'] = ('pkg-utopia-maintainers@lists.alioth.debian.org',
                        {'sid':None, 'experimental':None})

for group in group_list:
    for suite in groups[group][1].keys():
       query = """SELECT DISTINCT s.source
                  FROM sources_uniq s
                  INNER JOIN upload_history u
                  ON u.source = s.source
                  AND u.version = s.version
                  WHERE architecture != 'all'
                  AND release = '%(suite)s'
                  AND (s.maintainer_email = '%(mail)s'
                  OR uploaders LIKE '%%%(mail)s%%')
                  ORDER BY s.source""" \
                  % {'mail': groups[group][0], 'suite': suite}
       cur.execute(query)
       groups[group][1][suite] = cur.fetchall()
cur.close()
conn.close()

print """Content-Type: text/html\n\n
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Debian GNOME Team buildd status</title>
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
<td><h1 class="header">Debian GNOME Packaging - Buildd status</h1></td>
</tr>
</table>
<hr>"""

for group in group_list:
    for suite in sorted(groups[group][1].keys(), reverse=True):
        print '<h3 class="%(group)s%(suite)s" onclick="toggleBuildd(\'%(group)s%(suite)s\')"> \
               Click to show buildd status for %(group)s packages in %(suite)s</h3>' \
               % {'group':group, 'suite': suite}
        print '<h3 class="%(group)s%(suite)s" style="display: none" onclick="toggleBuildd(\'%(group)s%(suite)s\')"> \
               Click to hide buildd status for %(group)s packages in %(suite)s</h3>' \
               % {'group':group, 'suite': suite}
        print '<div class="%(group)s%(suite)s" style="display: none">' \
               % {'group':group, 'suite': suite}
        url = 'https://buildd.debian.org/status/package.php?p='
        for row in groups[group][1][suite]:
            url += "%s+" % row[0].replace('+', '%2B')
        url += '&suite=%s&compact=compact' % suite
        data = urlopen(url).read()
        data = split('<div id="jsmode"></div>', data)[1]
        data = split('</div><div id="footer">', data)[0]
        data = sub(r'<a href="([ap])', r'<a href="https://buildd.debian.org/status/\1', data)
        print data
        print '</div>'
    print '<hr>'

print '</body></html>'
