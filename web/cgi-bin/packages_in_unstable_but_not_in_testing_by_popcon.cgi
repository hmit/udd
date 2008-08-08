#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd") or die $!;
my $sth = $dbh->prepare(<<EOF
	SELECT DISTINCT unstable.package, insts
        FROM (SELECT DISTINCT package FROM packages
                WHERE release = 'sid')
          AS unstable,
             popcon
        WHERE NOT EXISTS (SELECT 1 FROM packages WHERE
                          release = 'lenny' and package = unstable.package)
              AND popcon.package = unstable.package ORDER BY insts DESC;
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

