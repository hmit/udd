#/usr/bin/env python
# Last-Modified: <Fri Jun  6 12:31:10 2008>

import debian_bundle.deb822
import gzip
import os
import sys
import aux
import tempfile
from aux import ConfigException

# A mapping from the architecture names to architecture IDs
archs = {}
# The ID for the distribution we want to include
distr_id = None

def import_sources(conn, file):
  """Import the sources from the file into the database-connection conn.

  Sequence has to have an iterator interface, that yields a line every time it
  is called.The Format of the file is expected to be that of a debian
  source file."""
  # The fields that are to be read. Other fields are ignored
  fields = ('Package', 'Version', 'Architecture', 'Maintainer', 'Uploaders', 'Binary')
  cur = conn.cursor()
  for control in debian_bundle.deb822.Packages.iter_paragraphs(file, fields):
    # Put the source package into the DB
    query = "EXECUTE source_insert('%s', '%s', '%s', %d)" % (control["Package"], control['Maintainer'].replace("'", "\\'"), control["Version"],
	distr_id)
    cur.execute(query)
    # Get the src_id of the source
    #cur.execute("SELECT src_id FROM sources WHERE name = '%(Package)s' AND version = '%(Version)s'" % control)
    cur.execute("EXECUTE select_src_id('%(Package)s', '%(Version)s')" % control)
    src_id = int(cur.fetchone()[0])
    # Fill the build_archs table for this source package
    if control['Architecture'] == 'all' or control['Architecture'] == 'any':
      query = "EXECUTE build_archs_insert(%d, %d)" % (src_id, archs[control['Architecture']])
      cur.execute(query)
    else:
      for arch in control['Architecture'].split():
	query = "EXECUTE build_archs_insert(%d, %d)" % (src_id, archs[arch])
	cur.execute(query)

def main():
  global distr_id
  global archs
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

  if not 'parts' in src_cfg:
    raise ConfigException('parts not specified for source %s in file %s' %
	(src_name, cfg_path))

  if not 'distribution' in src_cfg:
    raise ConfigException('distribution not specified for source %s in file %s' %
	(src_name, cfg_path))

  aux.debug = config['general']['debug']

  conn = aux.open_connection(config)

  # Get distribution ID. If it does not exist, create it
  distr_ids = aux.get_distrs(conn)
  if src_cfg['distribution'] not in distr_ids:
    aux.insert_distr(conn, src_cfg['distribution'])
    distr_ids = aux.get_distrs(conn)
  distr_id = distr_ids[src_cfg['distribution']]

  archs = aux.get_archs(conn)

  cur = conn.cursor()
  cur.execute("PREPARE source_insert AS INSERT INTO sources (name, maintainer, version, distr_id) VALUES ($1,$2,$3,$4)")
  cur.execute("PREPARE build_archs_insert AS INSERT INTO build_archs (src_id, arch_id) VALUES ($1,$2)")
  cur.execute("PREPARE select_src_id AS SELECT src_id FROM sources WHERE name = $1 AND version = $2")

  for part in src_cfg['parts']:
    path = os.path.join(src_cfg['directory'], part, 'source', 'Sources.gz')
    try:
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
    except IOError, (e, message):
      print "Could not read packages from %s: %s" % (path, message)

  cur.execute("DEALLOCATE source_insert")
  cur.execute("DEALLOCATE build_archs_insert")
  cur.execute("DEALLOCATE select_src_id")
  conn.commit()

if __name__ == '__main__':
  main()
