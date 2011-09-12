#!/usr/bin/env python
# Display bug blockers in a helpful table
# Copyright (C) 2011, Stefano Rivera <stefanor@debian.org>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

import cgi
import cgitb
import sys

import psycopg2


class AttrDict(dict):
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            self[key] = value

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError, e:
            raise AttributeError(e)


def find_blockers(bug):
    conn = psycopg2.connect("service=udd")
    cur = conn.cursor()
    cur.execute("""
    SELECT bugs.id, bugs.source, bugs.severity, bugs.title, bugs.last_modified,
           bugs.affects_testing,
           'pending' IN (SELECT tag FROM bugs_tags
                         WHERE bugs.id = bugs_tags.id) AS pending,
           'patch' IN (SELECT tag FROM bugs_tags
                       WHERE bugs.id = bugs_tags.id) AS patch
    FROM bugs
    WHERE bugs.id IN
      (SELECT DISTINCT LEAST(bugs_blockedby.blocker,
                             MIN(bugs_merged_with.merged_with))
       FROM bugs_blockedby
       LEFT OUTER JOIN bugs_merged_with
         ON (bugs_merged_with.id = bugs_blockedby.blocker)
       WHERE bugs_blockedby.id = %s
       GROUP BY bugs_blockedby.blocker)
    AND bugs.status != 'done'
    ORDER By bugs.id
    """, (bug,))
    keys = ('id source severity title last_modified affects_testing '
            'pending patch').split()
    for blocker in cur.fetchall():
        b = AttrDict(**dict(zip(keys, blocker)))

        b['status'] = ''
        if b.patch:
            b['status'] = 'patch'
        if b.pending:
            b['status'] = 'pending'

        class_ = []
        if b.status:
            class_.append(b.status)
        else:
            class_.append('todo')
        if b.affects_testing:
            class_.append('testing')
        b['attrs'] = {'class': ' '.join(class_)}

        yield b

    cur.close()
    conn.close()

result_template="""
<!DOCTYPE html>
<html>
<head>
    <title>Bugs Blocking #%(bug)s</title>
    <script type="text/javascript" src="../static/sorttable.js"></script>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
    <style type="text/css">
        table {
            border-collapse: collapse;
        }
        tr.todo.testing {
            background-color: #FCC;
        }
        tr.patch, tr.pending {
            background-color: #CFC;
        }
        td.severity-grave, td.severity-critical {
            font-style: italic;
        }
        td.severity-serious, td.severity-grave, td.severity-critical {
            color: red;
        }
        td.severity-important, td.severity-serious, td.severity-grave, td.severity-critical {
            font-weight: bold;
        }
    </style>
</head>
<body>
<h1>Bugs Blocking <a href="http://bugs.debian.org/%(bug)s">#%(bug)s</a></h1>
<table border="1" class="sortable">
    <thead>
        <tr>
            <th>Bug</th>
            <th>Package</th>
            <th>Status</th>
            <th>Severity</th>
            <th>Title</th>
            <th>Last Modified</th>
            <th>Affects Testing?</th>
        </tr>
    </thead>
    <tbody>
%(table)s
    </tbody>
</table>
</body>
</html>
""".strip()

table_template="""
        <tr class="%(class)s">
            <td><a href="http://bugs.debian.org/%(id)s">%(id)s</a></td>
            <td><a href="http://packages.qa.debian.org/%(source)s">%(source)s</a></td>
            <td>%(status)s</td>
            <td class="severity-%(severity)s">%(severity)s</td>
            <td>%(title)s</td>
            <td>%(last_modified)s</td>
            <td>%(affects_testing)s</td>
        </tr>
"""

form_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Bug Blockers</title>
</head>
<body>
<h1>Bug Blockers</h1>
<p>
  <form action="?" accept-charset="UTF-8">
    <label for="bug">Bug:</label>
    <input type="number" name="bug" id="bug" placeholder="Bug #">
    <input type="submit" value="Show Blockers">
  </form>
</p>
</body>
</html>
""".strip()

def render_blockers(bug):
    table = []
    for blocker in find_blockers(bug):
        subst = {
            'class': blocker.attrs['class'],
            'id': blocker.id,
            'source': blocker.source,
            'status': blocker.status,
            'severity': blocker.severity,
            'title': blocker.title,
            'last_modified': blocker.last_modified.strftime('%Y-%m-%d %H:%M'),
            'affects_testing': 'Yes' if blocker.affects_testing else ''
        }
        table.append(table_template % subst)
    subst = {
        'bug': bug,
        'table': ''.join(table),
    }
    sys.stdout.write(result_template % subst)

def render_form():
    sys.stdout.write(form_html)

def main():
    print 'Content-Type: text/html; charset=utf-8'
    print ''
    cgitb.enable()
    form = cgi.FieldStorage()
    if 'bug' in form:
        render_blockers(int(form.getfirst('bug', '')))
    else:
        render_form()

if __name__ == '__main__':
    main()
