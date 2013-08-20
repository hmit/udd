#! /usr/bin/perl

# collect information on the status of architectures for the next release
# the output format is not stable (for the moment)
# TODO move to some standard output format
#
# TODO this script is quite slow, it should probably not run as a cgi

use DBI;
use strict;
use Data::Dumper;
use Time::Local;

my $dbname= "udd";
my $dbport = "5452";
my $dbh = DBI->connect("dbi:Pg:host=localhost;dbname=$dbname;port=$dbport;user=guest");
my $wbh = DBI->connect("dbi:Pg:host=buildd.debian.org;dbname=wanna-build;port=5433;user=guest");
my $testing = "jessie";
my $now = time;

my $arch_info = ();
my $info = ();

printf "Content-Type: text/plain\n\n";

sub yesno {
	my $val = shift;
	return "yes" if ($val);
	return "no";
}

# from bugs_gatherer.pl, this should be done in a better way...
sub time2stamp {
	if(shift =~ /(\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)/) {
		my ($year, $month, $day, $hour, $minute, $second) = ($1, $2, $3, $4, $5, $6);
		return timelocal($second, $minute, $hour, $day, $month-1, $year);
	}
}

my $query = "select count(*),release,architecture from packages where release in ('$testing','sid') group by release,architecture order by architecture,release;";
my $sthc = $dbh->prepare($query);
$sthc->execute();
while (my $rowsc = $sthc->fetchrow_hashref()) {
	$arch_info->{$rowsc->{"architecture"}}->{"packages"}->{$rowsc->{"release"}} = $rowsc->{"count"};
}

my $query = "select count(*),release from sources where release in ('$testing','sid') group by release order by release;";
$query = "select architecture,distribution,state,count(*) from wannabuild where distribution ='sid' and state='Installed' group by architecture,distribution,state order by count;";
$sthc = $dbh->prepare($query);
$sthc->execute();
while (my $rowsc = $sthc->fetchrow_hashref()) {
	$info->{"sources"}->{$rowsc->{"distribution"}} = $rowsc->{"count"};
}


$query = "select architecture,distribution,state,count(*) from wannabuild where distribution ='sid' and state='Installed' group by architecture,distribution,state order by count;";
$sthc = $dbh->prepare($query);
$sthc->execute();
while (my $rowsc = $sthc->fetchrow_hashref()) {
	$arch_info->{$rowsc->{"architecture"}}->{"installed"} = $rowsc->{"count"};
}

my $lastok = $now - 30*24*3600;
$query = "select architecture,builder,max(state_change) from packages_public where builder like 'buildd_%' group by architecture,builder order by max;";
$sthc = $wbh->prepare($query);
$sthc->execute();
while (my $rowsc = $sthc->fetchrow_hashref()) {
	my $stamp = time2stamp($rowsc->{"max"});
	if ($stamp < $lastok) {
		#print "$stamp $lastok\n";
	} else {
		$arch_info->{$rowsc->{"architecture"}}->{"builders"} ++;
	}
}

$query = "select architecture,state,min(state_change),count(*) from packages_public group by architecture,state;";
$sthc = $wbh->prepare($query);
$sthc->execute();
while (my $rowsc = $sthc->fetchrow_hashref()) {
	#print Dumper $rowsc;
	my $stamp = time2stamp($rowsc->{"min"});
	my $state = $rowsc->{"state"};
	$arch_info->{$rowsc->{"architecture"}}->{"buildstate_duration"}->{$state} = $now-$stamp;
	$arch_info->{$rowsc->{"architecture"}}->{"buildstate_count"}->{$state} = $rowsc->{"count"};
}

my $period = $now - 3*30*24*3600;
foreach my $arch (keys $arch_info) {
	next if ($arch eq "all");
	$query = "select max(build_time) from \"${arch}_public\".pkg_history where timestamp > to_timestamp($period) limit 1;";
	$sthc = $wbh->prepare($query);
	$sthc->execute();
	if (my $rowsc = $sthc->fetchrow_hashref()) {
		$arch_info->{$arch}->{"longest_build"} = $rowsc->{"max"};
	}
}

#print Dumper $info;
#print Dumper $arch_info;

foreach my $arch (sort keys $arch_info) {
	next if ($arch eq "all");
	print "$arch:\n";
	my $a_i = $arch_info->{$arch};
	print "  in sid: ".yesno($a_i->{"packages"}->{"sid"} > 0)."\n";
	print "  in $testing: ".yesno($a_i->{"packages"}->{$testing} > 0)."\n";
	print "  archive_coverage: ".int(100*$a_i->{"installed"}/$info->{"sources"}->{"sid"})."%\n";
	print "  active buildds: ".$a_i->{"builders"}."\n";
	print "  longest build: ".int($a_i->{"longest_build"}/3600)." hours\n";
	print "  longest time in needs-build: ".int($a_i->{"buildstate_duration"}->{"Needs-Build"}/3600)." hours\n";
	print "  number of packages in needs-build: ".int($a_i->{"buildstate_count"}->{"Needs-Build"})."\n";
}

