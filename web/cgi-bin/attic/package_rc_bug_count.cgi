#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd;port=5452;host=localhost", "guest") or die $!;
my $sth = $dbh->prepare(<<EOF
SELECT b.package, COUNT(b.id)
FROM bugs b
WHERE 
        b.severity >= 'serious'
    AND 
        b.affects_testing
    AND(
            NOT EXISTS (SELECT tag FROM bugs_tags t WHERE b.id=t.id AND t.tag IN ('sid', 'sarge', 'etch', 'lenny', 'experimental'))
        OR
                EXISTS (SELECT tag FROM bugs_tags t WHERE b.id=t.id AND t.tag = 'wheezy')
    )
    AND NOT EXISTS (SELECT tag FROM bugs_tags t WHERE b.id=t.id AND t.tag = 'wheezy-ignore')
    AND(
            EXISTS (SELECT package FROM packages p WHERE p.package = b.package AND p.distribution = 'debian' AND p.release = 'wheezy')
        OR
            EXISTS (SELECT source FROM sources s WHERE s.source = b.package AND s.distribution = 'debian' AND s.release = 'wheezy')
    )
GROUP BY b.package
EOF
	);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

