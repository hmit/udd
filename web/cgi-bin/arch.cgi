#! /usr/bin/perl

# collect information on the status of architectures for the next release
# the output format is not stable (for the moment)
# TODO move to some standard output format
#
# TODO this script is quite slow, it should probably not run as a cgi

use DBI;
use strict;
use Data::Dumper;
$Data::Dumper::Sortkeys = 1;
use Time::Local;

my $dbname= "udd";
my $dbport = "5452";
my $dbh = DBI->connect("dbi:Pg:host=localhost;dbname=$dbname;port=$dbport;user=guest");
my $wbh = DBI->connect("dbi:Pg:host=buildd.debian.org;dbname=wanna-build;port=5433;user=guest");
my $testing = "jessie";
my $now = time;

my $arch_info = ();
my $info = ();

my $debug = 1;

my $cgi = defined($ENV{"REMOTE_ADDR"});

if ($cgi) {
	printf "Content-Type: text/plain\n\n";
	$debug = 0;
}

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

sub percentage {
	my $val = shift;
	return (int(1000*$val)/10);
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
	return int($hours/24)." days";
}

sub do_query {
	my $handle = shift;
	my $query = shift;

	print ((time-$now)." $query\n") if $debug;
	my $sthc = $handle->prepare($query);
	$sthc->execute();
	return $sthc;
}

my $query = "select count(*),release,architecture from packages where release in ('$testing','sid') group by release,architecture order by architecture,release;";
my $sthc = do_query($dbh,$query);
while (my $rowsc = $sthc->fetchrow_hashref()) {
	$arch_info->{$rowsc->{"architecture"}}->{"packages"}->{$rowsc->{"release"}} = $rowsc->{"count"};
}

# count source packages in sid
$query = "
select
	count(*)
from
	(
		select
			source,
			max(version) as version
		from
			sources
		where
			sources.extra_source_only is null and
			sources.release='sid' and
			sources.component='main' and
			sources.architecture!='all'
		group by source
	) as sources
;
";
$sthc = do_query($dbh,$query);
while (my $rowsc = $sthc->fetchrow_hashref()) {
	$info->{"sources"}->{"sid"} = $rowsc->{"count"};
}


#$query = "select architecture,distribution,state,count(*) from wannabuild where distribution ='sid' and state='Installed' group by architecture,distribution,state order by count;";
#$sthc = do_query($dbh,$query);
#while (my $rowsc = $sthc->fetchrow_hashref()) {
#	$arch_info->{$rowsc->{"architecture"}}->{"installed"} = $rowsc->{"count"};
#}

my $lastok = $now - 30*24*3600;
$query = "select architecture,builder,max(state_change) from packages_public where builder like 'buildd_%' group by architecture,builder order by max;";
$sthc = do_query($wbh,$query);
while (my $rowsc = $sthc->fetchrow_hashref()) {
	my $stamp = time2stamp($rowsc->{"max"});
	if ($stamp < $lastok) {
		#print "$stamp $lastok\n";
	} else {
		$arch_info->{$rowsc->{"architecture"}}->{"builders"} ++;
	}
}

$query = "select architecture,state,min(state_change),count(*) from packages_public group by architecture,state;";
$sthc = do_query($wbh,$query);
while (my $rowsc = $sthc->fetchrow_hashref()) {
	my $stamp = time2stamp($rowsc->{"min"});
	my $state = $rowsc->{"state"};
	$arch_info->{$rowsc->{"architecture"}}->{"buildstate_duration"}->{$state} = $now-$stamp;
	$arch_info->{$rowsc->{"architecture"}}->{"buildstate_count"}->{$state} = $rowsc->{"count"};
}

my $period = $now - 3*30*24*3600;
foreach my $arch (keys $arch_info) {
	next if ($arch eq "all");
	$query = "select * from \"${arch}_public\".pkg_history where timestamp > to_timestamp($period) and build_time > 0 order by build_time desc limit 1;";
	$sthc = do_query($wbh,$query);
	if (my $rowsc = $sthc->fetchrow_hashref()) {
		$arch_info->{$arch}->{"longest_build_time"} = $rowsc->{"build_time"};
		$arch_info->{$arch}->{"longest_build"} = $rowsc->{"package"}."/".$rowsc->{"distribution"};
	}

	$query = "select * from packages_public where architecture='$arch' and state='Needs-Build' order by state_change limit 1;";
	$sthc = do_query($wbh,$query);
	if (my $rowsc = $sthc->fetchrow_hashref()) {
		my $stamp = time2stamp($rowsc->{"state_change"});
		$arch_info->{$arch}->{"longest_needsbuild_time"} = $now - $stamp;
		$arch_info->{$arch}->{"longest_needsbuild"} = $rowsc->{"package"}."/".$rowsc->{"distribution"};
	}
}

# count source packages in sid/main which have binary packages per arch
$query = "
select
	architecture,
	count(*)
from
	(
		select
			source,
			version
		from
			sources
		where
			sources.extra_source_only is null and
			sources.release='sid'
	) as sources,
	(
		select
			source,
			architecture,
			max(source_version) as source_version,
			max(version) as version
		from
			packages
		where
			packages.release='sid' and
			component = 'main'
		group by
			source,
			architecture
	) as packages
where
	packages.source = sources.source and
	packages.source_version = sources.version
group by architecture
order by count
;
";
my $sthc = do_query($dbh,$query);
while (my $rowsc = $sthc->fetchrow_hashref()) {
	$arch_info->{$rowsc->{"architecture"}}->{"packagecount"} = $rowsc->{"count"};
}

# count source packages in sid/main which have a higher version than the highest
# binary version in sid per arch
$query = "
select
	architecture,
	count(*)
from
	(
		select
			source,
			max(version) as version
		from
			sources
		where
			sources.extra_source_only is null and
			sources.release='sid'
		group by source
	) as sources,
	(
		select
			source,
			architecture,
			max(source_version) as source_version,
			max(version) as version
		from
			packages
		where
			packages.release='sid' and
			component = 'main'
		group by
			source,
			architecture
	) as packages
where
	packages.source = sources.source and
	packages.source_version < sources.version
group by architecture
order by count
;
";
my $sthc = do_query($dbh,$query);
while (my $rowsc = $sthc->fetchrow_hashref()) {
	$arch_info->{$rowsc->{"architecture"}}->{"outofdate"} = $rowsc->{"count"};
}

print Dumper $info if $debug;
print Dumper $arch_info if $debug;

foreach my $arch (sort keys $arch_info) {
	next if ($arch eq "all");
	print "$arch:\n";
	my $a_i = $arch_info->{$arch};
	print "  in sid: ".yesno($a_i->{"packages"}->{"sid"} > 0)."\n";
	print "  in $testing: ".yesno($a_i->{"packages"}->{$testing} > 0)."\n";
	print "  archive_coverage: ".percentage($a_i->{"packagecount"}/$info->{"sources"}->{"sid"})."%\n";
	print "  archive_uptodate: ".percentage(($a_i->{"packagecount"}-$a_i->{outofdate})/$a_i->{"packagecount"})."%\n";
	print "  active buildds: ".$a_i->{"builders"}."\n";
	print "  longest build: ".show_secs($a_i->{"longest_build_time"}).": ".$a_i->{"longest_build"}."\n";
	print "  longest time in needs-build: ".show_secs($a_i->{"longest_needsbuild_time"}).": ".
		$a_i->{"longest_needsbuild"}."\n";
	print "  number of packages in needs-build: ".int($a_i->{"buildstate_count"}->{"Needs-Build"})."\n";
}

