#!/usr/bin/env python
# Last-Modified: <Tue Aug 19 13:55:40 2008>

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
  if command not in ('run', 'setup', 'drop', 'tables', 'update', 'schema'):
    sys.stderr.write("command has to be one of 'run', 'setup', 'drop', 'update', 'schema' and 'tables'\n")
    sys.exit(1)

  config = udd.aux.load_config(open(sys.argv[1]).read())

  types = config['general']['types']

  connection = udd.aux.open_connection(config)

  schemata = {}
  # Process the sources
  for src in sys.argv[3:]:
    src_config = config[src]
    type = src_config['type']
    udd.aux.lock(config, src)
    try:
      # If the command is update, we need a special case. Otherwise we can just use the gatherer's methods
      if command == 'update':
	if "update-command" in src_config:
	  result = system(src_config['update-command']) 
	  if result != 0:
	    sys.exit(result)
	  if 'timestamp-folder' in config['general']:
	    f = open(os.path.join(config['general']['timestamp-folder'], src+".update"), "w")
	    f.write(asctime())
	    f.close()
      elif command == 'schema':
	for tag in ('schema', 'packages-schema', 'sources-schema'):
	  if not tag in src_config:
	    continue
	  schema = config['general']['schema-dir'] + '/' + src_config[tag]
	  print (open(schema).read() % src_config)
      else:
	(src_command,rest) = types[type].split(None, 1)
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

