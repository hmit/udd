#!/usr/bin/env python

import yaml

sf = open("sections.yaml")
sections = yaml.safe_load(sf.read())
sf.close()
for section in sections:
	print section

