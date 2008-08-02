#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd") or die $!;
my $sth = $dbh->prepare(<<EOF
	SELECT package, COUNT(id) as nr FROM bugs WHERE severity in ('critical', 'grave', 'serious') AND affects_testing AND NOT tags LIKE '%fixed%' AND NOT tags LIKE '%lenny-ignore%' AND NOT is_archived AND EXISTS (SELECT * FROM packages WHERE packages.package = package AND packages.release = 'etch') GROUP BY package ORDER BY nr DESC;
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

