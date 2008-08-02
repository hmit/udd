#!/usr/bin/env python
# Last-Modified: <Sat Aug  2 18:46:52 2008>

"""
This script executes the update statements for selected sources
"""

import sys
from os import system
from time import asctime
import os.path
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
      if system(src_cfg['update-command']) == 0 and 'update-timestamp-folder' in config['general']:
	f = open(os.path.join(config['general']['update-timestamp-folder'], src), "w")
	f.write(asctime())
	f.close()

