#!/bin/bash

grep -v -e ': unable to open /org/bugs.debian.org/versions/pkg/' -e 'Use of uninitialized value in hash slice at ' -e 'Could not read file for bug ' -e 'Unmatched () ' -e "Unmatched '<>' in " -e 'Use of uninitialized value in subroutine entry at' -e 'Mail::Address::_tokenise' -e 'Mail::Address::parse' -e "main::run('HASH" -e 'main::main() called at /org/udd.debian.org/udd/udd/bugs_gatherer.pl line 401' -e 'Wide character in print at /org/udd.debian.org/mirrors/bugs.debian.org/perl/Debbugs/Packages.pm line'
