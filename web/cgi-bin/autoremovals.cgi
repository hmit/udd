#! /usr/bin/perl

use DBI;
use strict;
use Data::Dumper;
$Data::Dumper::Sortkeys = 1;
use Time::Local;

my $dbname= "udd";
my $dbport = "5452";
my $dbh = DBI->connect("dbi:Pg:host=localhost;dbname=$dbname;port=$dbport;user=guest");
my $testing = "jessie";
my $now = time;

my $info = ();

my $debug = 0;

my $cgi = defined($ENV{"REMOTE_ADDR"});

if ($cgi) {
	printf "Content-Type: text/plain; charset=utf-8 \n\n";
	$debug = 0;
}

sub show_secs {
	my $secs = shift||0;
	if ($secs < 10000) {
		return "$secs s";
	}
	my $hours = int($secs/3600);
	if ($hours < 50) {
		return "$hours hours";
	}
	return (int(10*$hours/24)/10)." days";
}

sub do_query {
	my $handle = shift;
	my $query = shift;

	print ((time-$now)." $query\n") if $debug;
	my $sthc = $handle->prepare($query);
	$sthc->execute();
	return $sthc;
}

my $maintainerlist = {};

my $query = "select 
		r.bugs,
		r.buggy_deps,
		r.first_seen,
		r.removal_time,
		r.source,
		s.maintainer,
		s.uploaders
	from
		testing_autoremovals r,
		sources s
	where
		s.release='sid' and
		-- get maintainer info only for newest version in sid
		s.version = (
			select
				max(version)
			from sources
			where release = 'sid'
			and sources.source = r.source
			group by source
		)  and
		s.source=r.source
	";
my $sthc = do_query($dbh,$query);
while (my $rowsc = $sthc->fetchrow_hashref()) {
	my $buginfo = "";
	$buginfo .= "bugs ".$rowsc->{"bugs"}.", " if ($rowsc->{"bugs"} ne "");
	$buginfo .= "buggy deps ".$rowsc->{"buggy_deps"}.", " if ($rowsc->{"buggy_deps"} ne "");
	my $sourceinfo = $rowsc->{"source"}.": ".$buginfo."flagged for removal";
	my $delay = $rowsc->{"removal_time"}-$now;
	if ($delay > 0) {
		$sourceinfo .= " in ".show_secs($delay);
	}
	my $maintainers = {};
	push @{$maintainerlist->{$rowsc->{"maintainer"}}}, $sourceinfo;
	foreach my $upl (split(/>,\s*/,$rowsc->{"uploaders"})) {
		$upl.=">" unless ($upl =~ m/>$/);
		push @{$maintainerlist->{$upl}}, $sourceinfo;
	}
}

print "http://udd.debian.org/cgi-bin/autoremovals.yaml.cgi\n\n";

print Dumper $maintainerlist if $debug;
foreach my $maint (sort keys %$maintainerlist) {
	print "$maint\n";
	my $sourcelist = $maintainerlist->{$maint};
	foreach my $source (sort @$sourcelist) {
		print "   $source\n";
	}
	print "\n";
}

