#/usr/bin/env python
# Last-Modified: <Sun Jun 22 20:43:14 2008>

import debian_bundle.deb822
import gzip
import os
import sys
import aux
import tempfile
from aux import ConfigException

distr = None

mandatory = {'Format': 0, 'Maintainer': 0, 'Package': 0, 'Version': 0, 'Files': 0}
non_mandatory = {'Uploaders': 0, 'Binary': 0, 'Architecture': 0,
    'Standards-Version': 0, 'Homepage': 0, 'Build-Depends': 0,
    'Build-Depends-Indep': 0, 'Build-Conflicts': 0, 'Build-Conflicts-Indep': 0,
    'Priority': 0, 'Section': 0, 'Vcs-Arch': 0, 'Vcs-Browser': 0, 'Vcs-Bzr': 0,
    'Vcs-Cvs': 0, 'Vcs-Darcs': 0, 'Vcs-Git': 0, 'Vcs-Hg': 0, 'Vcs-Svn': 0,
    'X-Vcs-Browser': 0, 'X-Vcs-Bzr': 0, 'X-Vcs-Darcs': 0, 'X-Vcs-Svn': 0}

ignorable = {}

def null_or_quote(dict, key):
  if key in dict:
    return "'" + dict[key].replace("'", "\\'") + "'"
  else:
    return 'NULL'

warned_about = {}
def build_dict(control):
  """Build a dictionary from the control dictionary.

  Influenced by global variables mandatory, non_mandatory and ignorable"""
  global mandatory, non_mandatory
  d = {}
  for k in mandatory:
    if k not in control:
      raise "Mandatory field %s not specified" % k
    d[k] = "'" + control[k].replace("\\", "\\\\").replace("'", "\\'") + "'"
  for k in non_mandatory:
    d[k] = null_or_quote(control, k)
  for k in control.keys():
    if k not in mandatory and k not in non_mandatory and k not in ignorable:
      if k not in warned_about:
	warned_about[k] = 1
      else:
	warned_about[k] += 1
  return d

def import_sources(conn, file):
  """Import the sources from the file into the database-connection conn.

  Sequence has to have an iterator interface, that yields a line every time it
  is called.The Format of the file is expected to be that of a debian
  source file."""
  cur = conn.cursor()
  for control in debian_bundle.deb822.Packages.iter_paragraphs(file):
    d = build_dict(control)
    query = """EXECUTE source_insert
	(%(Package)s, %(Version)s, %(Maintainer)s, %(Format)s, %(Files)s,
	%(Uploaders)s, %(Binary)s, %(Architecture)s, %(Standards-Version)s,
	%(Homepage)s, %(Build-Depends)s, %(Build-Depends-Indep)s,
	%(Build-Conflicts)s, %(Build-Conflicts-Indep)s, %(Priority)s,
	%(Section)s, %(Vcs-Arch)s, %(Vcs-Browser)s, %(Vcs-Bzr)s, %(Vcs-Cvs)s,
	%(Vcs-Darcs)s, %(Vcs-Git)s, %(Vcs-Hg)s, %(Vcs-Svn)s, %(X-Vcs-Browser)s,
	%(X-Vcs-Bzr)s, %(X-Vcs-Darcs)s, %(X-Vcs-Svn)s)
	"""  % d
    cur.execute(query)

def main():
  global distr
  if len(sys.argv) != 3:
    print "Usage: %s <config> <source>" % sys.argv[0]
    sys.exit(1)

  src_name = sys.argv[2]
  cfg_path = sys.argv[1]
  config = None
  try:
    config = aux.load_config(open(cfg_path).read())
  except ConfigException, e:
    raise ConfigException, "Configuration error in " + cfg_path +": " + e.message

  if not src_name in config:
    raise ConfigException, "Source %s not specified in %s" %(src_name, cfg_path)
  src_cfg = config[src_name]

  if not 'directory' in src_cfg:
    raise ConfigException('directory not specified for source %s in file %s' %
	(src_name, cfg_path))

  if not 'components' in src_cfg:
    raise ConfigException('parts not specified for source %s in file %s' %
	(src_name, cfg_path))

  if not 'distribution' in src_cfg:
    raise ConfigException('distribution not specified for source %s in file %s' %
	(src_name, cfg_path))

  if not 'release' in src_cfg:
    raise ConfigException('release not specified for source %s in file %s' %
	(src_name, cfg_path))

  aux.debug = config['general']['debug']

  conn = aux.open_connection(config)

  cur = conn.cursor()

  for comp in src_cfg['components']:
    path = os.path.join(src_cfg['directory'], comp, 'source', 'Sources.gz')
    try:
      query = """PREPARE source_insert as INSERT INTO sources
	(Package, Version, Maintainer, Format, Files, Uploaders, Bin,
	Architecture, Standards_Version, Homepage, Build_Depends,
	Build_Depends_Indep, Build_Conflicts, Build_Conflicts_Indep, Priority,
	Section, Vcs_Arch, Vcs_Browser, Vcs_Bzr, Vcs_Cvs, Vcs_Darcs, Vcs_Git,
	Vcs_Hg, Vcs_Svn, X_Vcs_Browser, X_Vcs_Bzr, X_Vcs_Darcs, X_Vcs_Svn,
	Distribution, Release, Component)
      VALUES
	($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
	$17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, '%s', '%s',
	'%s')"""\
	% (src_cfg['distribution'], comp, src_cfg['release'])
      cur.execute(query)

      aux.print_debug("Reading file " + path)
      # Copy content from gzipped file to temporary file, so that apt_pkg is
      # used by debian_bundle
      tmp = tempfile.NamedTemporaryFile()
      file = gzip.open(path)
      tmp.write(file.read())
      file.close()
      tmp.seek(0)
      aux.print_debug("Importing from " + path)
      import_sources(conn, open(tmp.name))
      tmp.close()
      cur.execute("DEALLOCATE source_insert")
    except IOError, (e, message):
      print "Could not read packages from %s: %s" % (path, message)

  conn.commit()

  for key in warned_about:
    print "Unknowen key %s appeared %d times" % (key, warned_about[key])

if __name__ == '__main__':
  main()
