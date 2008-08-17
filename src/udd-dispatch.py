#!/usr/bin/env python
# Last-Modified: <Sun Aug 17 12:03:34 2008>

"""Dispatch udd gatherers

This script is used to dispatch the source gatherers of the UDD project."""

import sys
from os import system
from time import asctime
import udd.aux
import os.path

def print_help():
  print "Usage: " + sys.argv[0] + " <configuration> <command> <source1> [source2 source3 ...]"

if __name__ == '__main__':
  if len(sys.argv) < 4:
    print_help()
    sys.exit(1)

  command = sys.argv[2]
  if command not in ('run', 'setup', 'drop', 'tables'):
    sys.stderr.write("command has to be one of 'run', 'setup', 'drop' and 'tables'\n")
    sys.exit(1)

  # Check the configuration
  config = udd.aux.load_config(open(sys.argv[1]).read())

  types = config['general']['types']

  for src in sys.argv[3:]:
    if not src in config:
      raise udd.aux.ConfigException("%s is not specified in %s" % (src, sys.argv[1]))

  connection = udd.aux.open_connection(config)

  # Process the sources
  for src in sys.argv[3:]:
    src_config = config[src]
    type = src_config['type']
    if not type in types:
      print "No script specified for type " + src['type']
      sys.exit(1)


    (src_command,rest) = types[type].split(None, 1)
    
    udd.aux.lock(config, src)
    try:
      if src_command == "exec":
	system(rest + " " + sys.argv[1] + " " + sys.argv[2] + " " + src)
      elif src_command == "module":
	exec("import " + rest)
	exec "gatherer = " + rest + ".get_gatherer(connection, config, src)"
	if command == 'tables':
	  exec "tables = gatherer.%s()" % command
	  print "\n".join(tables)
	else:
	  exec "gatherer.%s()" % command
      if 'timestamp-folder' in config['general']:
	f = open(os.path.join(config['general']['timestamp-folder'], src+".dispatch"), "w")
	f.write(asctime())
	f.close()
    except:
      udd.aux.unlock(config, src)
      raise
    udd.aux.unlock(config, src)
  connection.commit()

