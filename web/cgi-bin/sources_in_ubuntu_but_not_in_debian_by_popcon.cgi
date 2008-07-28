#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd") or die $!;
my $sth = $dbh->prepare(<<EOF
	SELECT DISTINCT intrepid.package, (vote + popcon_src_max.old + recent + nofiles) as pvote
        FROM (SELECT DISTINCT package FROM sources
                WHERE distribution = 'ubuntu' and release = 'intrepid')
          AS intrepid,
             popcon_src_max
        WHERE NOT EXISTS (SELECT * FROM sources WHERE distribution = 'debian'
                          and package = intrepid.package)
              AND popcon_src_max.package = intrepid.package AND popcon_src_max.distribution = 'ubuntu' ORDER BY pvote DESC;
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

