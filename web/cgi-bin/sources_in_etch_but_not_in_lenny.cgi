#!/usr/bin/perl -T

use strict;
use warnings;

use DBI;
use CGI;

my $dbh = DBI->connect("dbi:Pg:dbname=udd;port=5441;host=localhost", "guest") or die $!;
my $sth = $dbh->prepare(<<EOF
	select insts, sources.source
	from sources, popcon_src
	where release='etch'
	and sources.source not in
	   (select source from sources where release='lenny')
	   and sources.source = popcon_src.source
	   order by insts desc;
EOF
);

$sth->execute() or die $!;

my $q = CGI->new();

print $q->header(-type => 'text/plain');
while(my @row = $sth->fetchrow_array) {
	my ($package, $score) = @row;
	print "$package\t$score\n";
}

