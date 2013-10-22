#!/bin/sh

# To avoid duplicate entries in new_packages and blends_prospectivepackages
# a defined sequence of imports has to be ensured.  So the following
# importers are called in a sequence rather than at random cron times.

UAR=/srv/udd.debian.org/udd/update-and-run.sh

$UAR ftpnew
$UAR blends-prospective
# $UAR blends-metadata
$UAR blends-all
