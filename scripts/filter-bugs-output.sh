#!/bin/sh

grep -v -e ': unable to open /org/bugs.debian.org/versions/pkg/' -e 'Use of uninitialized value in hash slice at ' -e 'Could not read file for bug ' -e 'Unmatched () ' -e "Unmatched '<>' in " -e 'Use of uninitialized value in subroutine entry at'
