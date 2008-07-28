#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd") or die $!;
my $sth = $dbh->prepare(<<EOF
	SELECT DISTINCT unstable.package, (vote + olde + recent + nofiles) as pvote
        FROM (SELECT DISTINCT package FROM packages
                WHERE distribution = 'debian' and release = 'sid')
          AS unstable,
             popcon
        WHERE NOT EXISTS (SELECT * FROM packages where distribution = 'debian'
                          AND release = 'lenny' and package = unstable.package)
              AND popcon.name = unstable.package AND popcon.distribution = 'debian' ORDER BY pvote DESC;
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

