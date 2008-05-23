#!/usr/bin/env python
# Last-Modified: <Fri 23 May 2008 19:31:29 CEST>

"""Dispatch udd gatherers

This script is used to dispatch the source gatherers of the UDD project."""

import syck
from psycopg2 import connect
import sys
from os import system

def print_help():
  print "Usage: " + sys.argv[0] + " <configuration> <source1> [source2 source3 ...]"

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print_help()
    sys.exit(1)

  # Check the configuration
  config = syck.load(open(sys.argv[1]))
  if not 'dbname' in config:
    print "dbname not specified in configuration file " + sys.argv[1]
    sys.exit(1)

  if not 'types' in config:
    print "types not specified in configuration file " + sys.argv[1]
    sys.exit(1)

  types = config['types']

  # Process the sources
  for src in sys.argv[2:]:
    if not src in config:
      print src + " is no data source according to " + sys.argv[1]
      sys.exit(1)

    src_config = config[src]
    if not 'type' in src_config:
      print "Type of " + src + " not specified in " + sys.argv[1]
      sys.exit(1)
    type = src_config['type']

    if not type in types:
      print "No script specified for type " + src['type']
      sys.exit(1)
    script = types[type]

    system(script + " " + sys.argv[1] + " " + src)
