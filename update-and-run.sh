#!/bin/sh
DIR=/srv/udd.debian.org/udd/
CONFIG=$DIR/config-ullmann.yaml

$DIR/udd.py $CONFIG update "$@" && \
  $DIR/udd.py $CONFIG run "$@"
