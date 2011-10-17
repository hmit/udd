#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd;port=5441;host=localhost", "guest") or die $!;
my $sth = $dbh->prepare(<<EOF
	SELECT DISTINCT ubu.source, insts
        FROM (SELECT DISTINCT source FROM ubuntu_sources
                WHERE release = 'precise')
          AS ubu,
             ubuntu_popcon_src
        WHERE NOT EXISTS (SELECT * FROM sources WHERE distribution = 'debian'
                          and source = ubu.source)
              AND ubuntu_popcon_src.source = ubu.source
              AND ubu.source !~ '^language-(support|pack)-.*'
              AND ubu.source !~ '^kde-l10n-.*'
              AND ubu.source !~ 'ubuntu'
              AND ubu.source !~ 'launchpad'
         ORDER BY insts DESC;
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();
my $n = 0;
print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
	$n++;
}
print "\n\n# Packages: $n\n";

