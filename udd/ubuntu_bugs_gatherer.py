#!/usr/bin/env python

"""
This script imports the Ubuntu bugs from Launchpad
"""

from aux import quote
import sys
from gatherer import gatherer
import re
import urllib
from Queue import Queue, Empty
from threading import Thread, currentThread
import time
import httplib
import email

def get_gatherer(connection, config, source):
  return ubuntu_bugs_gatherer(connection, config, source)

class ubuntu_bugs_gatherer(gatherer):
  debug = False

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)

  def run(self):
    my_config = self.my_config
    num_fetchers = 3
    num_writers = 1
    bugs = self.fetch_all_bugs()
    httpq = Queue()
    dbq = Queue()
    for b in bugs:
      if self.debug:
        if b > 10000:
          continue
      httpq.put(b)

    # start workers
    for i in range(num_fetchers):
      t = Thread(target=self.bugfetcher, name="Fetcher-"+str(i),args=[httpq, dbq])
      t.setDaemon(True)
      t.start()

    c = self.cursor()
    c.execute("delete from ubuntu_bugs_subscribers")
    c.execute("delete from ubuntu_bugs_duplicates")
    c.execute("delete from ubuntu_bugs_tags")
    c.execute("delete from ubuntu_bugs_tasks")
    c.execute("delete from ubuntu_bugs")

    ok = True
    while ok:
      try:
        if self.debug:
          print "HTTPQ: ", httpq.qsize(), " DBQ: ", dbq.qsize()
        d = dbq.get(True, 5) # 10 secs timeout
        self.dbimport(c, d)
      except Empty:
        if httpq.qsize() == 0:
          ok = False

  def fetch_all_bugs(self):
    fh = urllib.urlopen('https://launchpad.net/ubuntu/+bugs-text')
    text = fh.read()
    # convert to a list
    bugs = text.split('\n')
    # remove '', or map() will complain
    bugs.remove('')
    # convert each bug (string) to a int
    bugs = map(int, bugs)
    # sort, so that we can remove duplicates in O(n) later
    bugs.sort()
    # remove duplicates. apparently not in lib, see
    # http://www.python.org/dev/peps/pep-0270/
    # FIXME use set()
    nbugs = []
    on = 0
    for n in bugs:
      if n != on:
        nbugs.append(n)
#      else:
#        print "Duplicate bug: " +  str(n)
      on = n
    fh.close()
    return nbugs

  # "worker". Fetch a specific bug as text from launchpad.
  def bugfetcher(self, hq, dq):
    while True:
      conn = httplib.HTTPSConnection('bugs.launchpad.net')
      ok = True
      b = None
      while ok:
        try:
          b = hq.get(False)
        except Empty:
          return
        except:
          print "Other exception raised in bugfetcher. exiting."
          exit(1)

        try:
          conn.request('GET', 'https://edge.launchpad.net/bugs/' + str(b) + '/+text')
          r = conn.getresponse()
          if r.status == 200:
            data = r.read()
            if data != '':
              dq.put(data)
            else:
              print "[", currentThread().getName(), "] Bug ", b, ": Empty data."
              ok = False
              hq.put(b)
          else:
            print "[", currentThread().getName(), "] Bug ", b, ": Wrong status: ", r.status, " ", r.reason
            ok = False
            hq.put(b)
        except httplib.BadStatusLine, line:
          print "[", currentThread().getName(), "] Bug ", b, ": BadStatusLine: ", line
          print str(r.getheaders())
          print r.read()
          ok = False
          hq.put(b)

  parre = re.compile('^\s*(.*) \(([^(]*)\)$')
  def splitpar(self, text):
    mo = re.search(self.parre, text)
    if mo == None:
      return (text, '')
    return mo.groups()

  contenttype = re.compile('^Content-Type: ')
  def dbimport(self, c, data):
    d = data.split('\n\n')
    bug = d[0] + '\n'
    tasks = []
    for di in d[1:-1]:
      if re.match(self.contenttype, di + '\n'):
        break
      else:
        tasks.append(di)
    # OK, we have bugs and tasks.
    bm = email.message_from_string(bug)
    bugno = int(bm['bug'])
    # Check that we are not missing some fields
    # ignore attachments for now
    s = set(bm.keys()) - set(['bug', 'title', 'reporter', 'attachments',
      'subscribers', 'tags', 'duplicate-of', 'duplicates', 'date-reported',
      'date-updated', 'security'])
    if len(s) > 0:
      print s
    name, login = self.splitpar(bm['reporter'])
    if bm['duplicate-of'] != '':
      dup = int(bm['duplicate-of'])
    else:
      dup = None
    reported = time.strptime(bm['date-reported'], "%a, %d %b %Y %H:%M:%S -0000")
    updated = time.strptime(bm['date-updated'], "%a, %d %b %Y %H:%M:%S -0000")
    if bm['security'] != None:
      security = 't'
    else:
      security = 'f'
    treported = time.strftime("%a, %d %b %Y %H:%M:%S +0000", reported)
    tupdated = time.strftime("%a, %d %b %Y %H:%M:%S +0000", updated)
    c.execute('insert into ubuntu_bugs values (%s, %s, %s, %s, %s, %s, %s, %s)',
        (bugno, bm['title'], login, name, dup, treported, tupdated, security))
    # subscribers
    for sub in bm['subscribers'].split('\n'):
      name, login = self.splitpar(sub)
      c.execute('insert into ubuntu_bugs_subscribers values (%s, %s, %s)', (bugno, login, name))
    # duplicates
    for d in bm['duplicates'].split():
      c.execute('insert into ubuntu_bugs_duplicates values (%s, %s)', (bugno, int(d)))
    # tags
    for tag in bm['tags'].split():
      c.execute('insert into ubuntu_bugs_tags values (%s, %s)', (bugno, tag))
    ### Import tasks
    for t in tasks:
      tm = email.message_from_string(t)
      pkg, distro = self.splitpar(tm['task'])
      rep_name, rep_login = self.splitpar(tm['reporter'])
      if tm['assignee'] != '':
        ass_name, ass_login = self.splitpar(tm['assignee'])
      else:
        ass_name = None
        ass_login = None
      created = time.strftime("%a, %d %b %Y %H:%M:%S +0000", 
        time.strptime(tm['date-created'], "%a, %d %b %Y %H:%M:%S -0000"))
      if tm['date-assigned']:
        assigned = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
          time.strptime(tm['date-assigned'], "%a, %d %b %Y %H:%M:%S -0000"))
      else:
        assigned = ''
      if tm['date-closed']:
        closed = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
          time.strptime(tm['date-closed'], "%a, %d %b %Y %H:%M:%S -0000"))
      else:
        closed = ''
      if tm['date-incomplete']:
        incomplete = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
          time.strptime(tm['date-incomplete'], "%a, %d %b %Y %H:%M:%S -0000"))
      else:
        incomplete = ''
      if tm['date-confirmed']:
        confirmed = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
          time.strptime(tm['date-confirmed'], "%a, %d %b %Y %H:%M:%S -0000"))
      else:
        confirmed = ''
      if tm['date-inprogress']:
        inprogress = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
          time.strptime(tm['date-inprogress'], "%a, %d %b %Y %H:%M:%S -0000"))
      else:
        inprogress = ''
      if tm['date-fix-committed']:
        fixcommitted = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
          time.strptime(tm['date-fix-committed'], "%a, %d %b %Y %H:%M:%S -0000"))
      else:
        fixcommitted = ''
      if tm['date-fix-released']:
        fixreleased = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
          time.strptime(tm['date-fix-released'], "%a, %d %b %Y %H:%M:%S -0000"))
      else:
        fixreleased = ''
      if tm['date-left-new']:
        leftnew = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
          time.strptime(tm['date-left-new'], "%a, %d %b %Y %H:%M:%S -0000"))
      else:
        leftnew = ''
      if tm['date-triaged']:
        triaged = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
          time.strptime(tm['date-triaged'], "%a, %d %b %Y %H:%M:%S -0000"))
      else:
        triaged = ''
      if tm['date-left-closed']:
        leftclosed = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
          time.strptime(tm['date-left-closed'], "%a, %d %b %Y %H:%M:%S -0000"))
      else:
        leftclosed = ''
      # check for missing headers
      s = set(tm.keys()) - set(['task', 'reporter', 'assignee', 'status', 'date-created', 'importance', 'component', 'milestone', 'date-assigned', 'date-closed', 'date-incomplete', 'date-confirmed', 'date-inprogress', 'date-fix-committed', 'date-fix-released', 'watch', 'date-left-new', 'date-triaged', 'date-left-closed'])
      if len(s) > 0:
        print s
        print t
      c.execute('insert into ubuntu_bugs_tasks values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (bugno, pkg, distro,
        tm['status'], tm['importance'], tm['component'], tm['milestone'], created,
        assigned, closed, incomplete, confirmed, inprogress, fixcommitted, fixreleased, leftnew, triaged, leftclosed, tm['watch'],
        rep_login, rep_name, ass_login, ass_name))

