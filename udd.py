#!/usr/bin/env python
# $Date$

"""Dispatch udd gatherers

This script is used to dispatch the source gatherers of the UDD project."""

import string
import sys
from os import system
from time import asctime
import udd.aux
import os.path

available_commands = [ 'run', 'update' ]
# available_commands = [ 'run', 'setup', 'drop', 'update', 'schema', 'tables' ]

def print_help():
  print "Usage: %s CONF_FILE COMMAND SOURCE [SOURCE ...]" % sys.argv[0]
  print "Available commands:"
  for cmd in available_commands:
    print '  %s' % cmd

if __name__ == '__main__':
  if len(sys.argv) < 4:
    print_help()
    sys.exit(1)

  command = sys.argv[2]
  if command not in available_commands:
    print >> sys.stderr, "command has to be one of: %s" % \
        string.join(available_commands, ', ')
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
      # If the command is update, we need a special case. Otherwise we
      # can just use the gatherer's methods
      if command == 'update':
	if "update-command" in src_config:
	  result = system(src_config['update-command']) 
	  if result != 0:
	    sys.exit(result)
	  if 'timestamp-dir' in config['general']:
	    f = open(os.path.join(config['general']['timestamp-dir'],
                                  src+".update"), "w")
	    f.write(asctime())
	    f.close()
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
	if 'timestamp-dir' in config['general']:
	  f = open(os.path.join(config['general']['timestamp-dir'],
                                src+".dispatch"), "w")
	  f.write(asctime())
	  f.close()
    except:
      udd.aux.unlock(config, src)
      raise
    udd.aux.unlock(config, src)
  connection.commit()
