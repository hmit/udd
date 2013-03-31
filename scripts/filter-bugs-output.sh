#!/bin/bash

grep -v\
 -e ': unable to open /srv/bugs.debian.org/versions/pkg/'\
 -e 'Use of uninitialized value in hash slice at '\
 -e 'Could not read file for bug '\
 -e 'Unmatched () '\
 -e "Unmatched '<>' in "\
 -e 'Use of uninitialized value in subroutine entry at'\
 -e 'Mail::Address::_tokenise'\
 -e 'Mail::Address::parse'\
 -e "main::run('HASH"\
 -e "main::update_bugs('HASH"\
 -e "main::update_bug('HASH"\
 -e 'main::main() called at /srv/udd.debian.org/udd.*/udd/bugs_gatherer.pl line'\
 -e 'Wide character in print at /srv/bugs.debian.org/perl/Debbugs/Packages.pm line'\
 -e 'does not map to Unicode at'
