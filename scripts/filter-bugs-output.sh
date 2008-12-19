#!/bin/sh

grep -v -e ': unable to open /org/bugs.debian.org/versions/pkg/' -e 'Use of uninitialized value in hash slice at '
