#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $s = <<EOF
select sources.source, id, insts, arrival, last_modified, title
from sources, bugs, popcon_src
where sources.distribution = 'debian' and sources.release = 'lenny'
and bugs.source = sources.source
and id in (select id from bugs_rt_affects_testing)
and id in (select id from bugs_rt_affects_unstable)
and bugs.severity in ('serious', 'grave', 'critical')
and arrival < (NOW() - interval '14 DAYS')
and sources.source = popcon_src.source
and popcon_src.insts < 2000
order by insts ASC
EOF
;

my $dbh = DBI->connect("dbi:Pg:dbname=udd") or die $!;
my $sth = $dbh->prepare($s);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
print "$s\n\n";
while(my @row = $sth->fetchrow_array) {
	$" = "\t";
	print "@row.\n";
}

