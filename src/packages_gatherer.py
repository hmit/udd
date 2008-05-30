#/usr/bin/env python
# Last-Modified: <Fri May 30 15:03:14 2008>

import debian_bundle.deb822
import gzip
import os
import sys
import aux
import tempfile
from aux import ConfigException

# A mapping from the architecture names to architecture IDs
archs = {}
# A mapping from <package-name><version> to 1
# If <package-name><version> is included in this dictionary, this means,
# that we've already added this package with this version for architecture 'all'
# to the database. Needed because different architectures include packages
# for architecture 'all' with the same version, and we don't want these duplicate
# entries
imported_all_pkgs = {}
# The ID for the distribution we want to include
distr_id = None

def import_packages(conn, sequence):
  """Import the packages from the sequence into the database-connection conn.

  Sequence has to have an iterator interface, that yields a line every time it
  is called.The Format of the sequence is expected to be that of a debian
  packages file."""
  global imported_all_pkgs
  # The fields that are to be read. Other fields are ignored
  fields = ('Architecture', 'Package', 'Version')
  for control in debian_bundle.deb822.Packages.iter_paragraphs(sequence, fields):
    # Check whether packages with architectue 'all' have already been
    # imported
    if control['Architecture'] == 'all':
      t = control['Package'] + control['Version']
      if t in imported_all_pkgs:
	continue
      imported_all_pkgs[t] = 1

    cur = conn.cursor()
    query = "INSERT INTO pkgs (name, distr_id, arch_id, version, src_id)\
    VALUES ('%s', %d, %d, '%s', 0)" % (control["Package"], distr_id, archs[control["Architecture"]], control["Version"])
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

  if not 'archs' in src_cfg:
    raise ConfigException('archs not specified for source %s in file %s' %
	(src_name, cfg_path))

  if not 'parts' in src_cfg:
    raise ConfigException('parts not specified for source %s in file %s' %
	(src_name, cfg_path))

  if not 'distribution' in src_cfg:
    raise ConfigException('distribution not specified for source %s in file %s' %
	(src_name, cfg_path))

  #if not 'release' in src_cfg:
  #  raise ConfigException('release not specified for source %s in file %s' %
  #     (src_name, cfg_path))

  aux.debug = config['general']['debug']

  conn = aux.open_connection(config)

  # Get distribution ID. If it does not exist, create it
  distr_ids = aux.get_distrs(conn)
  if src_cfg['distribution'] not in distr_ids:
    aux.insert_distr(conn, src_cfg['distribution'])
    distr_ids = aux.get_distrs(conn)
  distr_id = distr_ids[src_cfg['distribution']]

  archs = aux.get_archs(conn)

  # For every part and every architecture, import the packages into the DB
  for part in src_cfg['parts']:
    for arch in src_cfg['archs']:
      path = os.path.join(src_cfg['directory'], part, 'binary-' + arch, 'Packages.gz')
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
	import_packages(conn, open(tmp.name))
	tmp.close()
      except IOError, (e, message):
	print "Could not read packages from %s: %s" % (path, message)

  conn.commit()

if __name__ == '__main__':
  main()
