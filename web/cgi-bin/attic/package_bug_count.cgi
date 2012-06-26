#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd;port=5452;host=localhost", "guest") or die $!;
my $sth = $dbh->prepare(<<EOF
	SELECT package, COUNT(id) AS nr FROM bugs
	WHERE
		NOT (affects_stable OR affects_testing OR affects_unstable)
		AND NOT EXISTS (SELECT 1 FROM bugs_tags WHERE bugs_tags.id = bugs.id AND bugs_tags.tag = 'fixed')
	GROUP BY package ORDER BY nr DESC
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

