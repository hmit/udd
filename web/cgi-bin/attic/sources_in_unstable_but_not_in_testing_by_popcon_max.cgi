#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd;port=5441;host=localhost", "guest") or die $!;
my $sth = $dbh->prepare(<<EOF
SELECT DISTINCT unstable.source, insts
FROM (SELECT DISTINCT source FROM sources
WHERE distribution = 'debian' and release = 'sid')
AS unstable,
popcon_src
WHERE unstable.source NOT IN (SELECT source FROM sources WHERE distribution = 'debian'
AND release = 'wheezy')
AND popcon_src.source = unstable.source ORDER BY insts DESC;
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

