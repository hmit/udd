#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd;port=5441;host=localhost", "guest") or die $!;
my $sth = $dbh->prepare(<<EOF
SELECT DISTINCT pkgs.package, insts
FROM packages_summary pkgs, popcon
WHERE pkgs.release = 'sid' AND pkgs.package NOT IN
(SELECT package FROM packages_summary WHERE release = 'lenny')
AND popcon.package = pkgs.package ORDER BY insts DESC;
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

