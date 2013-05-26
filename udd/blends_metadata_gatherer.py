#!/usr/bin/env python

"""
This script imports data about not yet uploaded packages prepared by Blends teams.
"""

from aux import quote
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


  def inject_package(self, blend, task, strength, dist, component, dep):
    if dep in self.list_of_deps_in_task:
      self.log.info("Blend %s task %s: Packages %s is mentioned more than once" % (blend, task, dep))
    else:
      query = "EXECUTE blend_inject_package (%s, %s, %s, %s, %s, %s)" \
               % (quote(blend), quote(task), quote(dep), quote(strength[0]), quote(dist), quote(component))
      try:
        self.cur.execute(query)
        self.list_of_deps_in_task.append(dep)
      except IntegrityError, err:
        self.log.error("%s (%s)" % (query, err))
      except InternalError, err:
        self.log.error("INTEGRITY: %s (%s)" % (query, err))


  def handle_dep_line(self, blend, task, strength, dependencies):
    # Hack: Debian Edu tasks files are using '\' at EOL which is broken
    #       in RFC 822 files, but blend-gen-control from blends-dev relies
    #       on this.  So remove this stuff here for the Moment
    deps = re.sub('\\\\\n\s+', '', dependencies)

    # Remove versions from versioned depends
    deps = re.sub(' *\([ ><=\.0-9]+\) *', '', deps)

    # turn alternatives ('|') into real depends for this purpose
    # because we are finally interested in all alternatives
    depslist = deps.replace('|',',').split(',')
    # Collect all dependencies in one line first,
    # create an object for each later
    deps_in_one_line = []
    for depl in depslist:
      if depl.strip() != '': # avoid confusion when ',' is at end of line
        deps_in_one_line.append(depl.strip())

    for dep in deps_in_one_line:
      query = "EXECUTE blend_check_existing_package ('%s')" % (dep)
      self.cur.execute(query)
      in_udd = self.cur.fetchone()
      if in_udd:
        self.inject_package(blend, task, strength, in_udd[1], in_udd[2], dep)
      else:
        query = "EXECUTE blend_check_package_in_new ('%s')" % (dep)
        self.cur.execute(query)
        in_udd = self.cur.fetchone()
        if in_udd:
          self.inject_package(blend, task, strength, 'new', in_udd[1], dep)
        else:
          query = "EXECUTE blend_check_package_in_prospective ('%s')" % (dep)
          self.cur.execute(query)
          in_udd = self.cur.fetchone()
          if in_udd:
            self.inject_package(blend, task, strength, 'prospective', in_udd[1], dep)
          else:
            query = "EXECUTE blend_check_ubuntu_package ('%s')" % (dep)
            self.cur.execute(query)
            in_udd = self.cur.fetchone()
            if in_udd:
              self.log.info("UBUNTU: %s" % dep)
              self.inject_package(blend, task, strength, 'ubuntu', in_udd[1], dep)
            else:
              if debug != 0:
                self.log.info("Blend %s task %s: Package %s not found" % (blend, task, dep))

  def run(self):
    my_config = self.my_config
    self.cur = self.cursor()

    self.cur.execute("DELETE FROM %s" % (my_config['table-dependencies']))
    self.cur.execute("DELETE FROM %s" % (my_config['table-tasks']))
    self.cur.execute("DELETE FROM %s" % (my_config['table-metadata']))
    query = """PREPARE blend_metadata_insert AS INSERT INTO %s (blend, blendname, projecturl, tasksprefix,
               homepage, aliothurl, projectlist, logourl, outputdir, datadir, vcsdir, css, advertising, pkglist, dehsmail)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)""" % (my_config['table-metadata'])
    self.cur.execute(query)
    query = """PREPARE blend_tasks_insert AS INSERT INTO %s (blend, task, title, metapackage, description, long_description)
               VALUES ($1, $2, $3, $4, $5, $6)""" % (my_config['table-tasks'])
    self.cur.execute(query)
    
    query = """PREPARE blend_check_existing_package AS
                 SELECT DISTINCT package, distribution, component, r.sort FROM packages p
                 JOIN releases r ON p.release = r.release
                 WHERE package = $1
                 ORDER BY r.sort DESC
                 LIMIT 1"""
    self.cur.execute(query)

    query = """PREPARE blend_check_package_in_new AS
                 SELECT DISTINCT package, component FROM new_packages WHERE package = $1 LIMIT 1"""
    self.cur.execute(query)

    query = """PREPARE blend_check_package_in_prospective AS
                 SELECT DISTINCT package, component FROM blends_prospectivepackages WHERE package = $1 LIMIT 1"""
    self.cur.execute(query)

    query = """PREPARE blend_inject_package AS
                 INSERT INTO %s (blend, task, package, dependency, distribution, component)
                 VALUES ($1, $2, $3, $4, $5, $6)""" % (my_config['table-dependencies'])
    self.cur.execute(query)

    query = """PREPARE blend_check_ubuntu_package AS
                 SELECT DISTINCT package, component, regexp_replace(release, '-.*$', '') as release FROM ubuntu_packages
                 WHERE package = $1
                 ORDER BY release DESC
                 LIMIT 1"""
    self.cur.execute(query)

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
        meta['homepage']   = stanza['homepage']
        meta['aliothurl']  = stanza['aliothurl']
        meta['projectlist']= stanza['projectlist']
        if stanza.has_key('logourl'):
          meta['logourl']     = stanza['logourl']
        else:
          meta['logourl']     = ''
        meta['outputdir']  = stanza['outputdir']
        meta['datadir']    = stanza['datadir']
        meta['vcsdir']     = stanza['vcsdir']
        meta['css']        = stanza['css']
        if stanza.has_key('advertising'):
          meta['advertising'] = stanza['advertising']
        else:
          meta['advertising'] = ''
        meta['pkglist']    = stanza['pkglist']
        if stanza.has_key('dehsmail'):
          meta['dehsmail']    = stanza['dehsmail']
        else:
          meta['dehsmail']    = ''

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
          self.log.error("Unable to read %s" % ctrlfile)
        s = meta['blend']
      f.close()
      if p != '':
        p = p[0:p.find('-')]
      else:
        p = s.replace('debian-', '')
      meta['tasksprefix'] = p
      query = """EXECUTE blend_metadata_insert (%(blend)s, %(blendname)s, %(projecturl)s, %(tasksprefix)s,
                 %(homepage)s, %(aliothurl)s, %(projectlist)s, %(logourl)s, %(outputdir)s, %(datadir)s, %(vcsdir)s, %(css)s, %(advertising)s, %(pkglist)s, %(dehsmail)s)"""
      try:
        self.cur.execute(query, meta)
      except IntegrityError, err:
        self.log.error("taskfile = %s: %s" % (taskfile, err))

      for t in listdir(tasksdirtemplate % meta['blend']):
        if t.startswith('.'):
          continue
        taskfile = tasksdirtemplate % meta['blend'] + '/' + t
        try:
          f = open(taskfile, 'r')
        except:
          self.log.error("error reading %s" % taskfile)
        self.list_of_deps_in_task = []
        # read task metadata
        if f:
          ictrl = deb822.Deb822.iter_paragraphs(f)
          try:
            taskmeta = ictrl.next()
          except :
            self.log.error("The file %s does not seem to be a taskfile because it is not dep822 compatible." % taskfile)
            continue
          if not taskmeta.has_key('task'):
            if debug != 0:
	      self.log.debug("%s has no key 'Task'" % taskfile)
            continue
          task = { 'blend'            : meta['blend'],
                   'task'             : t,
                   'title'            : taskmeta['task'],
                   'metapackage'      : True,
                   'description'      : '',
                   'long_description' : '',
                 }
          if taskmeta.has_key('metapackage'):
            if taskmeta['metapackage'].lower() == 'false':
              task['metapackage'] = False
          try:
            desc               = taskmeta['description']
          except KeyError, err:
            self.log.error("taskfile=%s is lacking description (%s)" % (taskfile, err))
            continue
          lines                = desc.splitlines()
          try:
            task['description'] = lines[0]
          except IndexError, err:
            self.log.exception("Did not found first line in description: taskfile=%s" % (taskfile))
            continue
          for line in lines[1:]:
            task['long_description'] += line + "\n"

        query = "EXECUTE blend_tasks_insert (%(blend)s, %(task)s, %(title)s, %(metapackage)s, %(description)s, %(long_description)s)"
        try:
          self.cur.execute(query, task)
        except IntegrityError, err:
          self.log.error("taskfile = %s: %s" % (taskfile, err))

        # now read single dependencies
        try:
          dep = ictrl.next()
        except:
          dep = None
        while dep:
          if dep.has_key('depends'):
            self.handle_dep_line(meta['blend'], t, 'depends', dep['depends'])
          if dep.has_key('recommends'):
            self.handle_dep_line(meta['blend'], t, 'recommends', dep['recommends'])
          if dep.has_key('suggests'):
            self.handle_dep_line(meta['blend'], t, 'suggests', dep['suggests'])
          if dep.has_key('ignore'):
            self.handle_dep_line(meta['blend'], t, 'ignore', dep['ignore'])
          try:
            dep = ictrl.next()
          except:
            break


      self.meta[meta['blend']] = meta

    self.cur.execute("DEALLOCATE  blend_metadata_insert")
    self.cur.execute("ANALYZE %s" % my_config['table-metadata'])

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
