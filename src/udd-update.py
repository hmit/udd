#!/usr/bin/env python
# Last-Modified: <Sat Jul 12 16:44:23 2008>

"""
This script executes the update statements for selected sources
"""

import sys
from os import system
import udd.aux

def print_help():
  print 'Usage: ' + sys.argv[0] + " <configuration> <source1> [source2 source3 ...]"

if __name__ == '__main__':
  if len(sys.argv) < 3:
    print_help()
    sys.exit(1)

  config = udd.aux.load_config(open(sys.argv[1]).read())

  for src in sys.argv[2:]:
    if not src in config:
      raise udd.aux.ConfigException("%s is not specified in %s" % (src, sys.argv[1]))

  for src in sys.argv[2:]:
    src_cfg = config[src]
    if "update-command" in src_cfg:
      system(src_cfg['update-command'])

