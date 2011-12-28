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

from __future__ import print_function
from cgi import FieldStorage
from psycopg2 import connect
from re import split, sub
from urllib import urlopen

packages = {'sid': {'maintained': {}, 'team': {}, 'NMUed': {},
                    'QA/other': {}, 'sponsored': {}},
            'experimental': {'maintained': {}, 'team': {}, 'NMUed': {},
                             'QA/other': {}, 'sponsored': {}}}
architectures = set()
suites = ('sid', 'experimental')
roles = ('maintained', 'team', 'NMUed', 'QA/other', 'sponsored')
name = FieldStorage().getvalue('maint')
wbstatus = {'BD-Uninstallable': ('bduninstallable', 'BD-Uninstallable', '∉'),
            'Build-Attempted': ('buildattempted', 'Build-Attempted', '∿'),
            'Building': ('building', 'Building', '⚒'),
            'Maybe-Failed': ('maybefailed', 'Maybe-Failed', '(✘)'),
            'Successful': ('maybesuccessful', 'Maybe-Successful', '(✔)'),
            'Built': ('built', 'Built', '☺'),
            'Failed': ('failed', 'Failed', '✘'),
            'Failed-Removed': ('failed', 'Failed', '✘'),
            'Dep-Wait': ('depwait', 'Dep-Wait', '⌚'),
            'Installed': ('installed', 'Installed', '✔'),
            'Needs-Build': ('needsbuild', 'Needs-Build', '⌂'),
            'Uploaded': ('uploaded', 'Uploaded', '♐'),
            'Not-For-Us': ('notforus', 'Not-For-Us', '⎇'),
            'Auto-Not-For-Us': ('', '', '')}
query = '''WITH last_sources AS (
                 SELECT source, max(version) AS version,
                 maintainer, uploaders, release
                 FROM sources_uniq
                 WHERE release IN ('sid', 'experimental')
                 AND architecture != 'all'
                 GROUP BY source, maintainer, uploaders, release )
               SELECT s.source, s.maintainer, s.uploaders,
               u.changed_by, u.signed_by, u.nmu, s.release,
               w.architecture, w.state
               FROM last_sources s
               JOIN upload_history u
               ON u.source = s.source
               AND u.version = s.version
               JOIN wannabuild w
               ON w.source = s.source
               AND w.distribution = s.release
               WHERE s.maintainer LIKE '%%%(name)s%%'
               OR s.uploaders LIKE '%%%(name)s%%'
               OR u.changed_by LIKE '%%%(name)s%%'
               OR u.signed_by LIKE '%%%(name)s%%'
               ORDER BY s.source''' % {'name': name}

print('''Content-Type: text/html\n\n
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Maintainer's buildd status</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
<link rel="StyleSheet" type="text/css"
href="https://buildd.debian.org/status/media/pkg.css" />
<link rel="StyleSheet" type="text/css"
href="https://buildd.debian.org/status/media/status.css" />
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
</head>
<body>
<table id="header" width="100%%">
<tr>
<td><img src="http://www.debian.org/logos/openlogo.svg"
alt="Debian Logo" height="60" /></td>
<td><h1 class="header">Maintainer's buildd status</h1></td>
</tr>
</table>
<hr/>''')

if name:
    conn = connect(database='udd', port=5441, host='localhost', user='guest')
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    for row in rows:
        if name in row[1]:
            if not row[0] in packages[row[6]]['maintained']:
                packages[row[6]]['maintained'][row[0]] = {}
            packages[row[6]]['maintained'][row[0]][row[7]] = row[8]
        elif row[2] and name in row[2]:
            if not row[0] in packages[row[6]]['team']:
                packages[row[6]]['team'][row[0]] = {}
            packages[row[6]]['team'][row[0]][row[7]] = row[8]
        elif name in row[4]:
            if row[5]:
                if not row[0] in packages[row[6]]['NMUed']:
                    packages[row[6]]['NMUed'][row[0]] = {}
                packages[row[6]]['NMUed'][row[0]][row[7]] = row[8]
            else:
                if name not in row[1] and (not row[2] or name not in row[2]):
                    if name in row[3]:
                        if not row[0] in packages[row[6]]['QA/other']:
                            packages[row[6]]['QA/other'][row[0]] = {}
                        packages[row[6]]['QA/other'][row[0]][row[7]] = row[8]
                    else:
                        if not row[0] in packages[row[6]]['sponsored']:
                            packages[row[6]]['sponsored'][row[0]] = {}
                        packages[row[6]]['sponsored'][row[0]][row[7]] = row[8]
        architectures.add(row[7])

    for suite in suites:
        for role in roles:
            if not len(packages[suite][role]):
                continue
            print('<h3>Buildd status for %s packages in %s</h3>' %
                  (role, suite))
            print('<table class="data"><tr><th>Package</th>')
            for architecture in sorted(architectures):
                print('<th><a href="https://buildd.debian.org', sep='', end='')
                print('/status/architecture.php?a=%s&amp;suite=%s">%s' %
                      (architecture, suite, architecture))
                print('</a></th>')
            print('</tr>')
            for package in sorted(packages[suite][role]):
                print('<tr>')
                print('<td><a href="https://buildd.debian.org', sep='', end='')
                print('/status/package.php?p=%s&amp;suite=%s">%s</a></td>' %
                      (package, suite, package))
                for architecture in sorted(architectures):
                    if architecture in packages[suite][role][package]:
                        wbstate = packages[suite][role][package][architecture]
                        status = '<td class="status compact status-%s" ' % \
                                  wbstatus[wbstate][0]
                        status += 'title="%s">%s</td>' % \
                                  (wbstatus[wbstate][1], wbstatus[wbstate][2])
                    else:
                        status = '<td> </td>'
                    print(status)
                print('</tr>')
            print('</table>')
else:
    print('<form method="post" action="buildd.cgi">')
    print('<p>Maintainer name: <input type="text" name="maint"/>')
    print('<input type="submit" value="Submit"/></p></form>')

print('''<hr/><p><a href="http://validator.w3.org/check?uri=referer"><img
src="http://www.w3.org/Icons/valid-xhtml11" alt="Valid XHTML 1.1" height="31"
width="88"/></a><a href="http://jigsaw.w3.org/css-validator/check/referer">
<img src="http://jigsaw.w3.org/css-validator/images/vcss" alt="Valid CSS!"
height="31" width="88" /></a></p>''')
print('</body></html>')
