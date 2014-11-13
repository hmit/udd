#!/usr/bin/env python
# Browse usertags on the BTS
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
import re
import urllib

import psycopg2

DATABASE = {'database': 'udd',
            'port': 5452,
            'host': 'localhost',
            'user': 'guest',
           }


class AttrDict(dict):
    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            self[key] = value

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError, e:
            raise AttributeError(e)


def query(query, cols, *parameters):
    conn = psycopg2.connect(**DATABASE)
    cursor = conn.cursor()
    cursor.execute(query, parameters)
    for row in cursor.fetchall():
        yield AttrDict(**dict(zip(cols, row)))
    cursor.close()
    conn.close()


def strip_tags(soup):
    return re.sub(r'<[^>]*?>', '', soup)


def urlencode(params):
    s = urllib.urlencode(params)
    return re.sub(r'&(?!(\w+|#\d+);)', '&amp;', s)


def head(title):
    head_title = 'Debian BTS Usertag Browser'
    if title != 'Home':
        head_title = title + ' &mdash; ' + head_title
    print("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
  <style type="text/css">
    label {
      display: inline-block;
      width: 5ex;
    }
    table {
      border-collapse: collapse;
    }
    table, th, td {
      border: 1px solid gray;
      padding: 3px;
    }
    tr.done td {
      text-decoration: line-through;
    }
  </style>
  <title>%(head_title)s</title>
</head>
<body>
<h1>%(title)s</h1>
""".lstrip() % {
        'head_title': head_title,
        'title': title,
    })


def foot(linkhome=True):
    if linkhome:
        print '<p><a href="?">Home</a></p>'
    print """<script type="text/javascript" src="../static/sorttable.js"></script>
</body>
</html>
""".strip()


def thead(*cols):
    print '<table class="sortable">'
    print '  <thead><tr>'
    for col in cols:
        print '    <th>%s</th>' % col
    print '  </tr></thead>'


def tr(*cols, **kwargs):
    attrs = ['%s="%s"' % attr for attr in kwargs.get('attrs', {}).iteritems()]
    if attrs:
        print '  <tr %s>' % ' '.join(attrs)
    else:
        print '  <tr>'
    for col in cols:
        print '    <td>%s</td>' % col
    print '  </tr>'


def tfoot():
    print '</table>'


def index():
    head("Home")
    print("""
<h2>Search</h2>
<form action="?" accept-charset="UTF-8">
  <label for="user">User:</label>
  <input type="email" name="user" id="user"><br />
  <label for="tag">Tag:</label>
  <input type="text" name="tag" id="tag"><br />
  <input type="submit" formnovalidate value="Search">
</form>
<h2>By Bug</h2>
<form action="?" accept-charset="UTF-8">
  <label for="bug">Bug:</label>
  <input type="number" name="bug" id="bug" placeholder="Bug #"><br />
  <input type="submit" value="Search">
</form>
<h2>Browse</h2>
<ul>
  <li><a href="?browse=users">By user</a></li>
</ul>
""".lstrip())
    foot(False)


def by_user(user):
    r = query("""SELECT tag, COUNT(*) AS count
                 FROM bugs_usertags INNER JOIN bugs USING (id)
                 WHERE email = %s GROUP BY tag
                 ORDER BY tag
              """, ('tag', 'count'), user)
    head('User %s' % strip_tags(user))
    thead('Tag', 'Bugs')
    for result in r:
        tr('<a href="?%(params)s">%(tag)s</a>' % {
              'tag': result.tag,
              'params': urlencode({'user': user,
                                   'tag': result.tag}),
           },
           result.count)
    tfoot()
    foot()


def tagged_bugs(user, tag):
    r = query("""SELECT id, package, source, title, done != '' AS done
                   FROM bugs INNER JOIN bugs_usertags USING (id)
                   WHERE bugs_usertags.email = %s AND bugs_usertags.tag = %s
                   ORDER BY id
              """, ('id', 'package', 'source', 'title', 'done'), user, tag)
    head('Tagged %(tag)s by <a href="?%(params)s">%(user)s</a>'
         % {
            'tag': strip_tags(tag),
            'user': strip_tags(user),
            'params': urlencode({'user': user}),
         })
    thead('Bug', 'Package', 'Title', 'Other tags')
    for result in r:
        attrs = {}
        if result.done:
            attrs['class'] = 'done'
        tr('<a href="http://bugs.debian.org/%(id)s">#%(id)s</a>'
           % {'id': result.id},
           '<a href="http://packages.qa.debian.org/%(source)s">%(target)s</a>'
           % {'source': result.source,
               'target': ('src:' if result.source == result.package else '')
                         + result.package,
              },
           result.title,
           '<a href="?bug=%s">list usertags</a>' % result.id,
           attrs=attrs)
    tfoot()
    foot()


def search_result(user, tag):
    r = query("""SELECT email, tag, COUNT(*) AS count
                 FROM bugs_usertags INNER JOIN bugs USING (id)
                 WHERE email LIKE %s AND tag LIKE %s GROUP BY email, tag
                 ORDER BY email, tag
              """, ('email', 'tag', 'count'), user, tag)
    head('Search Result')
    thead('User', 'Tag', 'Bugs')
    for result in r:
        tr('<a href="?%(params)s">%(email)s</a>' % {
              'email': result.email,
              'params': urlencode({'user': result.email}),
           },
           '<a href="?%(params)s">%(tag)s</a>' % {
              'tag': result.tag,
              'params': urlencode({'user': result.email,
                                          'tag': result.tag}),
           },
           result.count)
    tfoot()
    foot()


def by_bug(bug):
    r = query("""SELECT email, tag
                 FROM bugs_usertags
                 WHERE id = %s
                 ORDER BY email, tag
              """, ('email', 'tag'), bug)
    head('Bug <a href="http://bugs.debian.org/%(bug)i">#%(bug)i</a>'
         % {'bug': bug})
    thead('User', 'Tag')
    for result in r:
        tr('<a href="?%(params)s">%(email)s</a>' % {
              'email': result.email,
              'params': urlencode({'user': result.email}),
           },
           '<a href="?%(params)s">%(tag)s</a>' % {
              'tag': result.tag,
              'params': urlencode({'user': result.email, 'tag': result.tag}),
           })
    tfoot()
    foot()


def user_list():
    r = query("""SELECT email, COUNT(*) AS count
                 FROM bugs_usertags INNER JOIN bugs USING (id)
                 GROUP BY email
                 ORDER BY email
              """, ('email', 'count'))
    head('User List')
    thead('User', 'Bugs')
    for result in r:
        tr('<a href="?%(params)s">%(email)s</a>' % {
              'email': result.email,
              'params': urlencode({'user': result.email}),
           },
           result.count)
    tfoot()
    foot()


def main():
    print 'Content-Type: text/html; charset=utf-8'
    print ''
    cgitb.enable()
    form = cgi.FieldStorage()
    if 'browse' in form and form.getfirst('browse', '') == 'users':
        user_list()
    elif 'user' in form or 'tag' in form:
        user = form.getfirst('user', '*').replace('*', '%')
        tag = form.getfirst('tag', '*').replace('*', '%')
        if '%' not in user and tag == '%':
            by_user(user)
        elif '%' not in user and '%' not in tag:
            tagged_bugs(user, tag)
        else:
            search_result(user, tag)
    elif 'bug' in form and form.getfirst('bug', ''):
        by_bug(int(form.getfirst('bug', '')))
    else:
        index()


if __name__ == '__main__':
    main()
