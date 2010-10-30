#/usr/bin/env python
# Last-Modified: <Sun Aug 17 12:07:25 2008>
# This file is a part of the Ultimate Debian Database project

import debian_bundle.deb822
import gzip
import os
import sys
import aux
import tempfile
from aux import ConfigException
from aux import null_or_quote, quote
from gatherer import gatherer
from time import time
import email.Utils
import re

def get_gatherer(connection, config, source):
  return sources_gatherer(connection, config, source)

class sources_gatherer(gatherer):
  "This class imports the data from Sources.gz files into the database"
  mandatory = {'Maintainer': 0, 'Package': 0, 'Version': 0, 'Files': 0}
  non_mandatory = {'Format':0, 'Uploaders': 0, 'Binary': 0, 'Architecture': 0,
      'Standards-Version': 0, 'Homepage': 0, 'Build-Depends': 0,
      'Build-Depends-Indep': 0, 'Build-Conflicts': 0, 'Build-Conflicts-Indep': 0,
      'Priority': 0, 'Section': 0, 'Python-Version': 0, 'Checksums-Sha1':0,
      'Checksums-Sha256':0, 'Original-Maintainer':0, 'Dm-Upload-Allowed':0} 
  ignorable = {'Vcs-Arch': 0, 'Vcs-Bzr': 0,
      'Vcs-Cvs': 0, 'Vcs-Darcs': 0, 'Vcs-Git': 0, 'Vcs-Hg': 0, 'Vcs-Svn': 0,
      'Vcs-Mtn':0,
      'X-Vcs-Browser': 0, 'Vcs-Browser': 0, 'X-Vcs-Bzr': 0, 'X-Vcs-Darcs': 0, 'X-Vcs-Svn': 0, 'X-Vcs-Hg':0, 'X-Vcs-Git':0, 'Vcs-Browse':0,
      'Directory':0, 'Comment':0, 'Origin':0, 'Url':0, 'X-Collab-Maint':0, 'Autobuild':0, 'Vcs-Cvs:':0, 'Python-Standards-Version':0, 'url':0, 'originalmaintainer':0, 'Originalmaintainer':0, 'Build-Recommends':0, 'Maintainer-Homepage': 0, 'Python3-Version': 0}
      #Vcs-Cvs: is caused by a bug in python-debian, apparently.
  ignorable_re = re.compile("^(Orig-|Original-|Origianl-|Orginal-|Orignal-|Orgiinal-|Orginial-|Debian-|X-Original-|Upstream-)")
  vcs = [ 'Svn', 'Git', 'Arch', 'Bzr', 'Cvs', 'Darcs', 'Hg', 'Mtn']

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self._distr = None
    self.assert_my_config('directory', 'components', 'distribution', 'release', 'sources-table', 'sources-schema')
    self.warned_about = {}

  def build_dict(self, control):
    """Build a dictionary from the control dictionary.

    Influenced by global variables mandatory, non_mandatory and ignorable"""
    d = {}

    for k in sources_gatherer.mandatory:
      if k not in control:
        raise "Mandatory field %s not specified" % k
      d[k] = control[k]
    for k in sources_gatherer.non_mandatory:
      if k in control:
        d[k] = control[k]
      else:
        d[k] = None
    
    d['Vcs-Type'] = None
    d['Vcs-Url'] = None
    for vcs in sources_gatherer.vcs:
      if control.has_key("Vcs-"+vcs):  
        d['Vcs-Type'] = vcs
        d['Vcs-Url'] = control["Vcs-"+vcs]
        break
      elif control.has_key("X-Vcs-"+vcs):  
        d['Vcs-Type'] = vcs
        d['Vcs-Url'] = control["X-Vcs-"+vcs]
        break
    if control.has_key("Vcs-Browser"):  
        d['Vcs-Browser'] = control["Vcs-Browser"]
    elif control.has_key("X-Vcs-Browser"):  
        d['Vcs-Browser'] = control["X-Vcs-Browser"]
    elif control.has_key("Vcs-Browse"):  # common typo
        d['Vcs-Browser'] = control["Vcs-Browse"]
    else:
        d['Vcs-Browser'] = None
    if control.has_key("Dm-Upload-Allowed"):
        d['Dm-Upload-Allowed'] = (d['Dm-Upload-Allowed'].lower() == 'yes')

    
    for k in control.iterkeys():
      if k not in sources_gatherer.mandatory and k not in sources_gatherer.non_mandatory and k not in sources_gatherer.ignorable and (not sources_gatherer.ignorable_re.match(k)):
        if k not in self.warned_about:
          self.warned_about[k] = 1
        else:
          self.warned_about[k] += 1
    return d

  def import_sources(self, file):
    """Import the sources from the file into the database-connection conn.

    Sequence has to have an iterator interface, that yields a line every time it
    is called.The Format of the file is expected to be that of a debian
    source file."""
    cur = self.cursor()
    pkgs = []
    query = """EXECUTE source_insert
      (%(Package)s, %(Version)s, %(Maintainer)s,
      %(maintainer_name)s, %(maintainer_email)s, %(Format)s, %(Files)s,
      %(Uploaders)s, %(Binary)s, %(Architecture)s, %(Standards-Version)s,
      %(Homepage)s, %(Build-Depends)s, %(Build-Depends-Indep)s,
      %(Build-Conflicts)s, %(Build-Conflicts-Indep)s, %(Priority)s,
      %(Section)s, %(Vcs-Type)s, %(Vcs-Url)s, %(Vcs-Browser)s,
      %(Python-Version)s, %(Checksums-Sha1)s, %(Checksums-Sha256)s,
      %(Original-Maintainer)s, %(Dm-Upload-Allowed)s)"""
    query_uploaders = """EXECUTE uploader_insert (%(Package)s, %(Version)s,
      %(Uploader)s, %(Name)s, %(Email)s)"""
    uploaders = []
    for control in debian_bundle.deb822.Packages.iter_paragraphs(file):
      d = self.build_dict(control)
      d['maintainer_name'], d['maintainer_email'] = email.Utils.parseaddr(d['Maintainer'])
      pkgs.append(d)

      if d['Uploaders']:
        for uploader in email.Utils.getaddresses([d['Uploaders']]):
          ud = {}
          ud['Package'] = d['Package']
          ud['Version'] = d['Version']
          ud['Uploader'] = email.Utils.formataddr(uploader)
          ud['Name'] = uploader[0]
          ud['Email'] = uploader[1]
          uploaders.append(ud)
    cur.executemany(query, pkgs)
    cur.executemany(query_uploaders, uploaders)

  def tables(self):
    return [self.my_config['sources-table']]

  def run(self):
    src_cfg = self.my_config

    table = src_cfg['sources-table']

    utable = src_cfg['uploaders-table']

    aux.debug = self.config['general']['debug']

    cur = self.cursor()

    for comp in src_cfg['components']:
      if re.search("debian-installer", comp):
        continue # debian-installer components don't have source
      path = os.path.join(src_cfg['directory'], comp, 'source', 'Sources.gz')
      cur.execute("DELETE from %s WHERE Distribution = '%s' AND\
        release = '%s' AND component = '%s'"\
        % (table, src_cfg['distribution'], src_cfg['release'], comp))
      cur.execute("DELETE from %s WHERE Distribution = '%s' AND\
        release = '%s' AND component = '%s'"\
        % (utable, src_cfg['distribution'], src_cfg['release'], comp))
      try:
        query = """PREPARE source_insert as INSERT INTO %s
          (Source, Version, Maintainer, Maintainer_name, Maintainer_email, Format, Files, Uploaders, Bin,
          Architecture, Standards_Version, Homepage, Build_Depends,
          Build_Depends_Indep, Build_Conflicts, Build_Conflicts_Indep, Priority,
          Section, Vcs_Type, Vcs_Url, Vcs_Browser, python_version, checksums_sha1,
          checksums_sha256, original_maintainer, dm_upload_allowed,
          Distribution, Release, Component)
        VALUES
          ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
          $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, '%s', '%s', '%s')"""\
          % (table, src_cfg['distribution'], src_cfg['release'], comp)
        cur.execute(query)
        query = """PREPARE uploader_insert as INSERT INTO %s
          (Source, Version, Distribution, Release, Component, Uploader, Name, Email) VALUES
          ($1, $2, '%s', '%s', '%s', $3, $4, $5) """ % \
        (utable, src_cfg['distribution'], src_cfg['release'], comp)
        cur.execute(query)

#        aux.print_debug("Reading file " + path)
        # Copy content from gzipped file to temporary file, so that apt_pkg is
        # used by debian_bundle
        tmp = tempfile.NamedTemporaryFile()
        file = gzip.open(path)
        tmp.write(file.read())
        file.close()
        tmp.seek(0)
#        aux.print_debug("Importing from " + path)
        self.import_sources(open(tmp.name))
        tmp.close()
      except IOError, (e, message):
        print "Could not read packages from %s: %s" % (path, message)
        sys.exit(1)
      cur.execute("DEALLOCATE source_insert")
      cur.execute("DEALLOCATE uploader_insert")

    cur.execute('ANALYZE %s' % table)
    cur.execute('ANALYZE %s' % utable)

    self.print_warnings()

  def setup(self):
    if 'schema-dir' in self.config['general']:
      schema_dir = self.config['general']['schema-dir']
      if 'sources-schema' in self.my_config:
        schema = schema_dir + '/' + self.my_config['sources-schema']
        self.eval_sql_file(schema, self.my_config)
      else:
        raise Exception("'packages-schema' not specified for source " + self.source)
    else:
      raise Exception("'schema-dir' not specified")

  def print_warnings(self):
    for key in self.warned_about:
      print "[Sources] Unknown key %s appeared %d times" % (key, self.warned_about[key])
