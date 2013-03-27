#!/usr/bin/env python

"""
This script imports data about not yet uploaded packages prepared by Blends teams.
"""

from gatherer import gatherer
from sys import stderr, exit
from os import listdir
from os.path import exists
from fnmatch import fnmatch
from psycopg2 import IntegrityError, InternalError, ProgrammingError
import re
import logging
import logging.handlers
from subprocess import Popen, PIPE
from debian import deb822

debug=1

def get_gatherer(connection, config, source):
  return blends_metadata_gatherer(connection, config, source)

class blends_metadata_gatherer(gatherer):
  """
  Metadata about Blends
   1. Metadata: general metadata
   2. Tasks: tasks belonging to Blends
   3. Dependencies: packages in tasks dependency relations
  """

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('table-metadata')
    self.assert_my_config('table-tasks')
    self.assert_my_config('table-dependencies')

    self.log = logging.getLogger(self.__class__.__name__)
    if debug==1:
        self.log.setLevel(logging.DEBUG)
    else:
        self.log.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(filename=self.__class__.__name__+'.log',mode='w')
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - (%(lineno)d): %(message)s")
    handler.setFormatter(formatter)
    self.log.addHandler(handler)

    self.meta  = {}
    self.tasks = []
    self.deps  = []

  def run(self):
    my_config = self.my_config
    cur = self.cursor()

    cur.execute("DELETE FROM %s" % (my_config['table-tasks']))
    cur.execute("DELETE FROM %s" % (my_config['table-metadata']))
    query = """PREPARE blend_metadata_insert AS INSERT INTO %s (blend, blendname, projecturl, tasksprefix)
               VALUES ($1, $2, $3, $4)""" % (my_config['table-metadata'])
    cur.execute(query)
    query = """PREPARE blend_tasks_insert AS INSERT INTO %s (blend, task, metapackage)
               VALUES ($1, $2, $3)""" % (my_config['table-tasks'])
    cur.execute(query)

    blendsdir = my_config['path']
    metadatadir = blendsdir+'/website/webtools/webconf'
    ctrlfiletemplate = blendsdir+'/blends/%s/debian/control.stub'
    tasksdirtemplate = blendsdir+'/blends/%s/tasks'
    for md in listdir(metadatadir):
      f = open(metadatadir+'/'+md, 'r')
      meta = { 'blend'       : '',
               'blendname'   : '',
               'projecturl'  : '',
             }
      for stanza in deb822.Sources.iter_paragraphs(f, shared_storage=False):
        meta['blend']      = stanza['blend']        # short name of the project
        meta['blendname']  = stanza['projectname']  # Printed name of the project
        meta['projecturl'] = stanza['projecturl']   # Link to the developer page with dynamic content
                                                    # like for instance these tasks pages
      f.close()
      ctrlfile = ctrlfiletemplate % meta['blend']
      p = ''
      try:
        f = open(ctrlfile, 'r')
        for stanza in deb822.Sources.iter_paragraphs(f, shared_storage=False):
          if stanza.has_key('source'):
            s = stanza['source']
          if stanza.has_key('package'):
            p = stanza['package']
            break
      except:
        if debug != 0:
          print "Unable to read", ctrlfile
        s = meta['blend']
      f.close()
      if p != '':
        p = p[0:p.find('-')]
      else:
        p = s.replace('debian-', '')
      # print p + ' (' + s + ')'
      meta['tasksprefix'] = p
      query = "EXECUTE blend_metadata_insert (%(blend)s, %(blendname)s, %(projecturl)s, %(tasksprefix)s)"
      try:
        cur.execute(query, meta)
      except IntegrityError, err:
        print >>stderr, err

      for t in listdir(tasksdirtemplate % meta['blend']):
        if t.startswith('.'):
          continue
        taskfile = tasksdirtemplate % meta['blend'] + '/' + t
        try:
          f = open(taskfile, 'r')
        except:
          print >>stderr, "error reading %s" % taskfile
        if f:
          ictrl = deb822.Deb822.iter_paragraphs(f)
          taskmeta = ictrl.next()
          if not taskmeta.has_key('task'):
            if debug != 0:
	      print "%s has no key 'Task'" % taskfile
          task = { 'blend'       : meta['blend'],
                   'task'        : t,
                   'metapackage' : True,
                 }
          if taskmeta.has_key('metapackage'):
            if taskmeta['metapackage'].lower() == 'false':
              task['metapackage'] = False
        query = "EXECUTE blend_tasks_insert (%(blend)s, %(task)s, %(metapackage)s)"
        try:
          cur.execute(query, task)
        except IntegrityError, err:
          print >>stderr, err

      self.meta[meta['blend']] = meta

    cur.execute("DEALLOCATE  blend_metadata_insert")
    cur.execute("ANALYZE %s" % my_config['table-metadata'])

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
