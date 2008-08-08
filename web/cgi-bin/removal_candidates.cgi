#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

s = <<EOF
select sources.package, id, insts, arrival, last_modified, title
from sources, bugs_unarchived AS bugs, popcon_src_max
where sources.distribution = 'debian' and sources.release = 'lenny'
and bugs.source = sources.package
and bugs.affects_testing = true
and bugs.affects_unstable = true
and bugs.severity in ('serious', 'grave', 'critical')
and arrival < (NOW() - interval '14 DAYS')
and sources.package = popcon_src_max.source
and popcon_src_max.distribution = 'debian'
and popcon_src_max.insts < 2000
order by package;
EOF

my $dbh = DBI->connect("dbi:Pg:dbname=udd") or die $!;
my $sth = $dbh->prepare(s);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
print "$s\n\n";
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

