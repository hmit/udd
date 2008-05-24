#!/usr/bin/env python
# Last-Modified: <Sat May 24 11:57:17 2008>

"""Dispatch udd gatherers

This script is used to dispatch the source gatherers of the UDD project."""

import sys
from os import system
import aux

def print_help():
  print "Usage: " + sys.argv[0] + " <configuration> <source1> [source2 source3 ...]"

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print_help()
    sys.exit(1)

  # Check the configuration
  config = aux.load_config(open(sys.argv[1]).read())

  types = config['types']

  for src in sys.argv[2:]:
    if not src in config:
      raise aux.ConfigException("%s is not specified in %s" % (src, sys.argv[1]))

  # Process the sources
  for src in sys.argv[2:]:
    src_config = config[src]
    type = src_config['type']
    if not type in types:
      print "No script specified for type " + src['type']
      sys.exit(1)
    script = types[type]

    system(script + " " + sys.argv[1] + " " + src)
