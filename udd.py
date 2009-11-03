#!/usr/bin/env python
# $Date$

"""Dispatch udd gatherers

This script is used to dispatch the source gatherers of the UDD project."""

import string
import sys
from os import system
import time
import udd.aux
import os.path

available_commands = [ 'run', 'setup', 'drop', 'update', 'schema', 'tables' ]

def print_help():
  print "Usage: %s CONF_FILE COMMAND SOURCE [SOURCE ...]" % sys.argv[0]
  print "Available commands:"
  for cmd in available_commands:
    print '  %s' % cmd

def insert_timestamps(config, source, command, start_time, end_time):
  connection = udd.aux.open_connection(config)
  cur = connection.cursor()
  values = { 'source' : source,
             'command' : command,
             'start_time' : start_time,
             'end_time' : end_time }
  cur.execute("""INSERT INTO timestamps
                 (source, command, start_time, end_time)
                 VALUES (%(source)s, %(command)s, %(start_time)s,
                 %(end_time)s)""",
              values)
  connection.commit()

def get_timestamp():
  return time.strftime('%Y-%m-%d %H:%M:%S')

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

  schemata = {}
  # Process the sources
  for src in sys.argv[3:]:
    src_config = config[src]
    type = src_config['type']
    udd.aux.lock(config, src)
    try:
      # If the command is update, we need a special case. Otherwise we
      # can just use the gatherer's methods
      start_time = get_timestamp()
      if command == 'update':
        if "update-command" in src_config:
          result = system(src_config['update-command']) 
          if result != 0:
            sys.exit(result)
        end_time = get_timestamp()
      else:
        (src_command,rest) = types[type].split(None, 1)
        if src_command == "exec":
          system(rest + " " + sys.argv[1] + " " + sys.argv[2] + " " + src)
        elif src_command == "module":
          connection = udd.aux.open_connection(config)
          # TODO XXX: using exec is hackish and prone to failures due
          # to what is being written in the conffile. We should get
          # rid of these lines and use the "imp" module, which is
          # meant for these tasks:
          # http://docs.python.org/lib/module-imp.html
          exec("import " + rest)
          exec "gatherer = " + rest + ".get_gatherer(connection, config, src)"
          if command == 'tables':
            exec "tables = gatherer.%s()" % command
            print "\n".join(tables)
          else:
            exec "gatherer.%s()" % command
          connection.commit()
        end_time = get_timestamp()
      insert_timestamps(config, src, command, start_time, end_time)
    except:
      udd.aux.unlock(config, src)
      raise
    udd.aux.unlock(config, src)

# vim:set et tabstop=2:
