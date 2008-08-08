#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd") or die $!;
my $sth = $dbh->prepare(<<EOF
	SELECT DISTINCT intrepid.package, insts
        FROM (SELECT DISTINCT package FROM ubuntu_sources
                WHERE release = 'intrepid')
          AS intrepid,
             ubuntu_popcon_src
        WHERE NOT EXISTS (SELECT * FROM sources WHERE distribution = 'debian'
                          and package = intrepid.package)
              AND ubuntu_popcon_src.source = intrepid.package ORDER BY insts DESC;
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

