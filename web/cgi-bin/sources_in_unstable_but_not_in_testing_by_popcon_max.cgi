#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd") or die $!;
my $sth = $dbh->prepare(<<EOF
SELECT DISTINCT unstable.package, insts
FROM (SELECT DISTINCT package FROM sources
WHERE distribution = 'debian' and release = 'sid')
AS unstable,
popcon_src
WHERE unstable.package NOT IN (SELECT package FROM sources WHERE distribution = 'debian'
AND release = 'lenny')
AND popcon_src.source = unstable.package ORDER BY insts DESC;
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

