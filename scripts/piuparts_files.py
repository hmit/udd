#!/usr/bin/env python

import yaml

sf = open("sections.yaml")
sections = yaml.load(sf.read())
sf.close()
for section in sections:
	print section

