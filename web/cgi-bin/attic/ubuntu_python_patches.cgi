#!/usr/bin/python                                 
#
# Copyright (C) 2009-2010 Luca Falavigna <dktrkranz@debian.org>
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
# Extract from UDD Python packages with Ubuntu patches

import apt_pkg
from psycopg2 import connect

lower = 0
higher = 0
tbl = str()
rel = {'d':'sid', 'u':'natty'}
apt_pkg.InitSystem()
conn = connect(database="udd", port=5441, host="localhost", user="guest")
cur = conn.cursor()                    

query = """
SELECT sources_uniq.source, sources_uniq.version, ubuntu_sources.version
FROM sources_uniq, ubuntu_sources
WHERE sources_uniq.distribution='debian'
AND sources_uniq.release='%s'
AND ubuntu_sources.distribution='ubuntu'
AND ubuntu_sources.release='%s'
AND sources_uniq.source = ubuntu_sources.source
AND sources_uniq.version != ubuntu_sources.version
AND ubuntu_sources.version ~ 'ubuntu'
AND sources_uniq.source IN
(
    SELECT DISTINCT source
    FROM packages
    WHERE release = 'sid'
    AND depends ~ 'python[^-]+'
)
ORDER BY source;""" % (rel['d'], rel['u'])

cur.execute(query)
data = cur.fetchall()
cur.close()
conn.close()

for row in data:
    pack = row[0]
    d_ver = row[1]
    u_ver = row[2]
    if pack.startswith('lib'):
        base = pack[:4]
    else:
        base = pack[0]
    qa = '<a href="http://packages.qa.debian.org/%s/%s.html">%s</a>' % (base, pack, pack)
    patch = '<a href="http://patches.ubuntu.com/%s/%s/%s_%s.patch">%s_%s.patch</a>' % (base, pack, pack, u_ver, pack, u_ver)
    debian = '<a href="http://packages.debian.org/changelogs/pool/main/%s/%s/current/changelog">%s</a>' % (base, pack, d_ver)
    ubuntu = '<a href="https://launchpad.net/ubuntu/+source/%s/%s">%s</a>' % (pack, u_ver, u_ver)
    if apt_pkg.VersionCompare(d_ver, u_ver) > 0:
        higher = higher + 1
        tbl = tbl + '<tr>\n<td>%s</td>\n<td><b>%s</b></td>\n<td>%s</td>\n<td>%s</td>\n</tr>' % (qa, debian, ubuntu, patch)
    elif apt_pkg.VersionCompare(d_ver, u_ver) < 0:
        lower = lower + 1
        tbl = tbl + '<tr bgcolor="#FFCC66">\n<td>%s</td>\n<td>%s</td>\n<td><b>%s</b></td>\n<td>%s</td>\n</tr>' % (qa, debian, ubuntu, patch)
    else:
        pass

print 'Content-Type: text/html\n\n'
print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">'
print '<html>\n<head>\n<title>Python packages with Ubuntu modifications</title>'
print '<meta http-equiv="Content-Type" content="text/html;charset=utf-8">\n</head>\n<body>'
print '<font size=5>Debian version higher than Ubuntu one: %d</font>\n<br>' % higher
print '<font size=5 color="#FFCC66">Debian version lower than Ubuntu one: %s</font>\n<br><br><br>' % lower
print '<table border=2>\n<tr>\n<td align=center><b><font size=5>Package</font></b></td>'
print '<td align="center"><b><font size=5>Debian Version (%s)</font></b></td>' % rel['d']
print '<td align="center"><b><font size=5>Ubuntu Version (%s)</font></b></td>' % rel['u']
print '<td align=center><b><font size=5>Patch</font></b></td>\n</tr>%s' % tbl
print '</table>\n<p>\n<a href="http://validator.w3.org/check?uri=referer">'
print '<img src="http://www.w3.org/Icons/valid-html401" alt="Valid HTML 4.01 Transitional" height="31" width="88">\n</a>\n</p>\n</body>\n</html>'
