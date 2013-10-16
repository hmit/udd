#!/usr/bin/env python

"""
This script imports data about not yet uploaded packages prepared by Blends teams.
"""

#TODO remove sys import
import sys
import hashlib
from aux import quote
from gatherer import gatherer
from sys import stderr, exit
from os import listdir
from os.path import exists
from fnmatch import fnmatch
from psycopg2 import IntegrityError, InternalError, ProgrammingError, DataError
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

    self.meta  = {}
    self.tasks = []
    self.deps  = []


  def sethandler(self, blend="default"):
    logger_name = "{0}-{1}".format(self.__class__.__name__, blend)

    self.log = logging.getLogger(logger_name)
    if debug==1:
      self.log.setLevel(logging.DEBUG)
    else:
      self.log.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(filename=logger_name+'.log',mode='w')
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - (%(lineno)d): %(message)s")
    handler.setFormatter(formatter)
    self.log.addHandler(handler)

  def get_hash(self, task_content):
    md5 = hashlib.md5()
    md5.update(task_content)
    
    return md5.hexdigest()

  def inject_package(self, blend, task, strength, dist, component, dep, provides):
    if dep in self.list_of_deps_in_task:
      if strength in ('ignore', 'avoid'):
        self.log.info("Blend %s task %s: Package %s is mentioned more than once.  There is no point in adding an extra entry with strength '%s'." % (blend, task, dep, strength))
      else:
        self.log.error("Blend %s task %s: Package %s is mentioned more than once.  Make sure that the higher dependency strength will be used. Currently ignored is '%s'." % (blend, task, dep, strength))
      return
    query = "EXECUTE blend_inject_package (%s, %s, %s, %s, %s, %s, %s)" \
             % (quote(blend), quote(task), quote(dep), quote(strength[0]), quote(dist), quote(component), quote(provides))
    try:
      self.cur.execute(query)
      self.list_of_deps_in_task.append(dep)
    except IntegrityError, err:
      self.log.error("%s (%s)" % (query, err))
    except InternalError, err:
      self.log.error("INTEGRITY: %s (%s)" % (query, err))

  def inject_package_alternatives(self, blend, task, strength, dist, component, alternatives, contains_provides):
    if alternatives in self.list_of_package_alternatives:
      if alternatives in self.list_of_deps_in_task:
        self.log.debug("Blend %s task %s: The warning about duplicated package %s should have just happended'." % (blend, task, alternatives))
      else:
        self.log.error("Blend %s task %s: Alternative %s is mentioned more than once.  Make sure that the higher dependency strength will be used. Currently ignored is '%s'." % (blend, task, alternatives, strength))
      return
    query = "EXECUTE blend_inject_package_alternatives (%s, %s, %s, %s, %s, %s, %s)" \
              % (quote(blend), quote(task), quote(alternatives), quote(strength[0]), quote(dist), quote(component), quote(contains_provides))
    try:
      self.cur.execute(query)
      self.list_of_package_alternatives.append(alternatives)
    except IntegrityError, err:
      self.log.error("%s (%s)" % (query, err))
    except InternalError, err:
      self.log.error("INTEGRITY: %s (%s)" % (query, err))

  def handle_dep_line(self, blend, task, strength, dependencies, is_prospective):
    # Hack: Debian Edu tasks files are using '\' at EOL which is broken
    #       in RFC 822 files, but blend-gen-control from blends-dev relies
    #       on this.  So remove this stuff here for the Moment
    deps = re.sub('\\\\\n\s+', '', dependencies)

    # temporary strip spaces from alternatives ('|') to enable erroneous space handling as it was done before
    deps = re.sub('\s*\|\s*', '|', deps)

    # turn alternatives ('|') into real depends for this purpose
    # because we are finally interested in all alternatives
    depslist = deps.split(',')
    # Collect all dependencies in one line first,
    # create an object for each later
    alts_in_one_line = []
    for depl in depslist:
      dl = depl.strip()
      if dl != '': # avoid confusion when ',' is at end of line
        # warn/clean versioned dependencies
        match = re.search('\(\s*[><=]+.*\)', dl)
        if match:
          dl1 = re.sub('\s*\(\s*[><=]+[^)]+\)\s*', '', dl).strip()
          self.log.info("Blend %s, task %s: Ignore versioned depends for '%s' -> '%s'" % (blend, task, dl, dl1))
          dl  = dl1

        if re.search('\s', dl):
          self.log.error("Blend %s task %s: Syntax error '%s'" % (blend, task, dl))
          # trying to fix the syntax error after issuing error message
          dlspaces = re.sub('\s+', ',', dl).split(',')
          for dls in dlspaces:
            alts_in_one_line.append(dls.strip())
            self.log.info("Blend %s task %s: Found '%s' package inside broken syntax string - please fix task file anyway" % (blend, task, dls.strip()))
        else:
          # in case we have to deal with a set of alternatives
          if re.search('\|', dl):
            dl = re.sub('\|', ' | ', dl)
          alts_in_one_line.append(dl)

    for alt in alts_in_one_line:
      contains_provides = 'false'
      alt_in_udd = [1000, '', '']
      for dep in alt.split(' | '):
        query = "EXECUTE blend_check_existing_package ('%s')" % (dep)
        self.cur.execute(query)
        in_udd = self.cur.fetchone()
        if in_udd:
          self.inject_package(blend, task, strength, in_udd[1], in_udd[2], dep, contains_provides)
          alt_in_udd = [0, in_udd[1], in_udd[2]]
        else:
          # for package names like 'espresso++' we need to escape '+' sign in regexp search
          query = "EXECUTE blend_check_existing_package_provides ('%s')" % (dep.replace('+', '\+'))
          try:
            self.cur.execute(query)
          except DataError, err:
            print >>stderr, query
            print >>stderr, err
            exit(1)
          in_udd_provides = self.cur.fetchone()
          if in_udd_provides:
            contains_provides = 'true'
            self.inject_package(blend, task, strength, in_udd_provides[1], in_udd_provides[2], dep, contains_provides)
            alt_in_udd = [0, in_udd_provides[1], in_udd_provides[2]]
          else:
            query = "EXECUTE blend_check_package_in_new ('%s')" % (dep)
            self.cur.execute(query)
            in_udd = self.cur.fetchone()
            if in_udd:
              self.inject_package(blend, task, strength, 'new', in_udd[1], dep, contains_provides)
              if alt_in_udd[0] > 1:
                alt_in_udd = [1, 'new', in_udd[1]]
            else:
              query = "EXECUTE blend_check_package_in_new_provides ('%s')" % (dep.replace('+', '\+'))
              self.cur.execute(query)
              in_udd_provides = self.cur.fetchone()
              if in_udd_provides:
                contains_provides = 'true'
                self.inject_package(blend, task, strength, 'new', in_udd_provides[1], dep, contains_provides)
                if alt_in_udd[0] > 1:
                  alt_in_udd = [1, 'new', in_udd_provides[1]]
              else:
                query = "EXECUTE blend_check_package_in_prospective ('%s')" % (dep)
                self.cur.execute(query)
                in_udd = self.cur.fetchone()
                if in_udd:
                  self.inject_package(blend, task, strength, 'prospective', in_udd[1], dep, contains_provides)
                  if alt_in_udd[0] > 2:
                    alt_in_udd = [2, 'prospective', in_udd[1]]
                else:
                  query = "EXECUTE blend_check_ubuntu_package ('%s')" % (dep)
                  self.cur.execute(query)
                  in_udd = self.cur.fetchone()
                  if in_udd:
                    self.log.info("Blend %s task %s: Package %s is provided in Ubuntu" % (blend, task, dep))
                    self.inject_package(blend, task, strength, 'ubuntu', in_udd[1], dep, contains_provides)
                    if alt_in_udd[0] > 3:
                      alt_in_udd = [3, 'ubuntu', in_udd[1]]
                  else:
                    query = "EXECUTE blend_check_ubuntu_package_provides ('%s')" % (dep.replace('+', '\+'))
                    self.cur.execute(query)
                    in_udd_provides = self.cur.fetchone()
                    if in_udd_provides:
                      contains_provides = 'true'
                      self.log.info("Blend %s task %s: Package %s is a virtual package provided in Ubuntu" % (blend, task, dep))
                      self.inject_package(blend, task, strength, 'ubuntu', in_udd_provides[1], dep, contains_provides)
                      if alt_in_udd[0] > 3:
                        alt_in_udd = [3, 'ubuntu', in_udd_provides[1]]
                    else:
                      if is_prospective:
                        if debug != 0:
                          self.log.debug("Blend %s task %s: Prospective package %s" % (blend, task, dep))
                      else:
                          self.log.info("Blend %s task %s: Package %s not found" % (blend, task, dep))
      if alt_in_udd[0] < 1000:
        self.inject_package_alternatives(blend, task, strength, alt_in_udd[1], alt_in_udd[2], alt, contains_provides)

  def delete_all_tables(self, table):
    my_config = self.my_config
    self.cur = self.cursor()

    self.cur.execute("DELETE FROM %s" % (my_config['table-dependencies']))
    self.cur.execute("DELETE FROM %s" % (my_config['table-alternatives']))
    self.cur.execute("DELETE FROM %s" % (my_config['table-tasks']))
    self.cur.execute("DELETE FROM %s" % (my_config['table-metadata']))

  def prepare_statements(self):
    my_config = self.my_config
    self.cur = self.cursor()

    #self.delete_all_tables()

    query = """PREPARE blend_metadata_insert AS INSERT INTO %s (blend, blendname, projecturl, tasksprefix,
               homepage, aliothurl, projectlist, logourl, outputdir, datadir, vcsdir, css, advertising, pkglist, dehsmail, distribution)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)""" % (my_config['table-metadata'])
    self.cur.execute(query)
    #query = """PREPARE blend_tasks_insert AS INSERT INTO %s (blend, task, title, section, enhances, leaf, test_always_lang, metapackage, metapackage_name, description, long_description)
    #           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""" % (my_config['table-tasks'])
    query = """PREPARE blend_tasks_insert AS INSERT INTO %s (blend, task, title, section, enhances, leaf, test_always_lang, metapackage, description, long_description, hashkey)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""" % (my_config['table-tasks'])
    self.cur.execute(query)
    
    query = """PREPARE blend_check_existing_package AS
                 SELECT DISTINCT package, p.distribution, component, r.sort FROM packages p
                 JOIN releases r ON p.release = r.release
                 WHERE package = $1
                 ORDER BY r.sort DESC
                 LIMIT 1"""
    self.cur.execute(query)

    query = """PREPARE blend_check_existing_package_provides AS
                 SELECT DISTINCT provides, p.distribution, component, r.sort FROM packages p
                 JOIN releases r ON p.release = r.release
                 WHERE provides ~ ('((\s|,)'||$1||'(\s+|,|$)|^'||$1||'$)') -- This should be equivalent: ('\y'||$1||'\y'); remark: psql is using '\y' where otherwise '\b' is used for word boundaries
                 ORDER BY r.sort DESC
                 LIMIT 1"""
    self.cur.execute(query)

    query = """PREPARE blend_check_package_in_new AS
                 SELECT DISTINCT package, component FROM new_packages WHERE package = $1 LIMIT 1"""
    self.cur.execute(query)

    query = """PREPARE blend_check_package_in_new_provides AS
                 SELECT DISTINCT provides, component FROM new_packages WHERE provides ~ ('((\s|,)'||$1||'(\s+|,|$)|^'||$1||'$)') LIMIT 1"""
                                                                                        # This should be equivalent: ('\y'||$1||'\y'); remark: psql is using '\y' where otherwise '\b' is used for word boundaries
    self.cur.execute(query)

    query = """PREPARE blend_check_package_in_prospective AS
                 SELECT DISTINCT package, component FROM blends_prospectivepackages WHERE package = $1 LIMIT 1"""
    self.cur.execute(query)

    query = """PREPARE blend_inject_package AS
                 INSERT INTO %s (blend, task, package, dependency, distribution, component, provides)
                 VALUES ($1, $2, $3, $4, $5, $6, $7)""" % (my_config['table-dependencies'])
    self.cur.execute(query)

    query = """PREPARE blend_inject_package_alternatives AS
                 INSERT INTO %s  (blend, task, alternatives, dependency, distribution, component, contains_provides)
                 VALUES ($1, $2, $3, $4, $5, $6, $7)""" % (my_config['table-alternatives'])
    self.cur.execute(query)

    query = """PREPARE blend_check_ubuntu_package AS
                 SELECT DISTINCT package, component, regexp_replace(release, '-.*$', '') as release FROM ubuntu_packages
                 WHERE package = $1
                 ORDER BY release DESC
                 LIMIT 1"""
    self.cur.execute(query)

    query = """PREPARE blend_check_ubuntu_package_provides AS
                 SELECT DISTINCT provides, component, regexp_replace(release, '-.*$', '') as release FROM ubuntu_packages
                 WHERE provides ~ ('((\s|,)'||$1||'(\s+|,|$)|^'||$1||'$)') -- This should be equivalent: ('\y'||$1||'\y'); remark: psql is using '\y' where otherwise '\b' is used for word boundaries
                 ORDER BY release DESC
                 LIMIT 1"""
    self.cur.execute(query)

  def run(self):
    my_config = self.my_config

    self.prepare_statements()

    blendsdir = my_config['path']
    metadatadir = blendsdir+'/website/webtools/webconf'
    ctrlfiletemplate = blendsdir+'/blends/%s/debian/control.stub'
    tasksdirtemplate = blendsdir+'/blends/%s/tasks'


    all_blends_conf = listdir(metadatadir)
    selected_source = self.source

    blends_to_update = []

    if selected_source == 'blends-all':
      blends_to_update = all_blends_conf
    else:
      for md in all_blends_conf:
        md_cleaned = md.replace(".conf",'')
        source_cleaned = selected_source.split('-')[1]
        if '-' in md_cleaned:
          md_cleaned = md_cleaned.split('-')[1]

        if source_cleaned == md_cleaned:
          blends_to_update.append(md)
          break

    if not blends_to_update:
      #set default blends_metadata_handler
      self.sethandler()
      self.log.error("Can not find any conf in: {1} for {0} blend, aborting...".format(selected_source, metadatadir))

    for md in blends_to_update:
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
        if stanza.has_key('distribution'):
          meta['distribution']    = stanza['distribution']
        else:
          meta['distribution']    = ''

      f.close()

      #set the current blend's handler
      self.sethandler(meta['blend'])

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

      #TODO check again the blend metadata removal
      #try:
      #  self.cur.execute("DELETE FROM %s WHERE blend='%s'" % (my_config['table-metadata'], meta['blend'] ))
      #except IntegrityError, err:
      #  self.log.error("Delete from %s: error %s" % (my_config['table-metadata'], err))
      
        
      meta['tasksprefix'] = p
      #query = """EXECUTE blend_metadata_insert (%(blend)s, %(blendname)s, %(projecturl)s, %(tasksprefix)s,
      #           %(homepage)s, %(aliothurl)s, %(projectlist)s, %(logourl)s, %(outputdir)s, %(datadir)s, %(vcsdir)s, %(css)s, %(advertising)s, %(pkglist)s, %(dehsmail)s, %(distribution)s)"""
      #try:
      #  self.cur.execute(query, meta)
      #except IntegrityError, err:
      #  self.log.error("taskfile = %s: %s" % (taskfile, err))

      for t in listdir(tasksdirtemplate % meta['blend']):
        if t.startswith('.'):
          continue
        taskfile = tasksdirtemplate % meta['blend'] + '/' + t
        try:
          f = open(taskfile, 'r')
        except:
          self.log.error("error reading %s" % taskfile)
        self.list_of_deps_in_task = []
        self.list_of_package_alternatives = []
        
        #read task metadata
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

          task_is_uptodate = False
          with open(taskfile, 'r') as readforhash:
            taskhash = self.get_hash(readforhash.read())

          self.cur.execute("SELECT hashkey FROM %s WHERE task='%s' AND blend='%s'" % 
                                            (my_config['table-tasks'], t, meta['blend']) )
          hash_from_db = self.cur.fetchone()

          #check if the task exists and if it is up to date using the hash
          if hash_from_db and hash_from_db[0] == taskhash:
            task_is_uptodate = True

          if task_is_uptodate:
            self.log.info("Task %s is up date. Continue to next task." % ( taskmeta['task'] ) )
            continue
          else:
            self.log.info("Task %s has changed, proceed to update." % ( taskmeta['task'] ) )
            #clean up this task's data
            self.cur.execute("DELETE FROM ONLY %s WHERE blend='%s' AND task='%s'" % (my_config['table-dependencies'], meta['blend'], t ))
            self.cur.execute("DELETE FROM ONLY %s WHERE blend='%s' AND task='%s'" % (my_config['table-alternatives'], meta['blend'], t ))
            self.cur.execute("DELETE FROM ONLY %s WHERE blend='%s' AND task='%s'" % (my_config['table-tasks'], meta['blend'], t ))

          task = { 'blend'            : meta['blend'],
                   'task'             : t,
                   'title'            : taskmeta['task'],
                   'section'          : '',
                   'enhances'         : '',
                   'leaf'             : '',
                   'test_always_lang' : '',
                   'metapackage'      : True,
                   'metapackage_name' : None,
                   'description'      : '',
                   'long_description' : '',
                   'hashkey'          : taskhash,
                 }

          if taskmeta.has_key('section'):
            task['section'] = taskmeta['section']
          if taskmeta.has_key('enhances'):
            task['enhances'] = taskmeta['enhances']
          if taskmeta.has_key('leaf'):
            task['leaf'] = taskmeta['leaf']
          if taskmeta.has_key('test-always-lang'):
            task['test_always_lang'] = taskmeta['test-always-lang']
          if taskmeta.has_key('metapackage'):
            if taskmeta['metapackage'].lower() == 'false':
              task['metapackage'] = False
          if task['metapackage']:
              task['metapackage_name'] = meta['tasksprefix'] + '-' + t
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

        #query = "EXECUTE blend_tasks_insert (%(blend)s, %(task)s, %(title)s, %(section)s, %(enhances)s, %(leaf)s, %(test_always_lang)s, %(metapackage)s, %(metapackage_name)s, %(description)s, %(long_description)s, %(hashkey)s)"
        query = "EXECUTE blend_tasks_insert (%(blend)s, %(task)s, %(title)s, %(section)s, %(enhances)s, %(leaf)s, %(test_always_lang)s, %(metapackage)s, %(description)s, %(long_description)s, %(hashkey)s)"
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
          is_prospective = False
          if dep.has_key('Pkg-Description') and dep.has_key('Homepage'):
            is_prospective = True
          if dep.has_key('depends'):
            self.handle_dep_line(meta['blend'], t, 'depends', dep['depends'], is_prospective)
          if dep.has_key('recommends'):
            self.handle_dep_line(meta['blend'], t, 'recommends', dep['recommends'], is_prospective)
          if dep.has_key('suggests'):
            self.handle_dep_line(meta['blend'], t, 'suggests', dep['suggests'], is_prospective)
          if dep.has_key('ignore'):
            self.handle_dep_line(meta['blend'], t, 'ignore', dep['ignore'], is_prospective)
          if dep.has_key('avoid'):
            self.handle_dep_line(meta['blend'], t, 'avoid', dep['avoid'], is_prospective)
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
