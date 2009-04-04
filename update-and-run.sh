#!/bin/sh
DIR=/org/udd.debian.org/udd/
CONFIG=$DIR/config-org.yaml

$DIR/udd.py $CONFIG update "$@" && \
  $DIR/udd.py $CONFIG run "$@"
