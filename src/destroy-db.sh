#!/bin/sh

SUDO="sudo -u postgres"
$SUDO dropdb udd
$SUDO createdb -O christian udd
