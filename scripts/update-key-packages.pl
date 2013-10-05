#!/usr/bin/perl -w

# calculate key packages
# based on ruby version by Lucas

use strict;
use warnings;

use DBI;
use Data::Dumper;
$Data::Dumper::Sortkeys = 1;

my $EXC_SRC = [
];
my $INC_SRC = [
	'debian-installer',
	'piuparts',
	'debian-cd',
	'debian-installer-netboot-images',
];
my $POPCON_PERCENT = 5; # x% of submissions must have the package installed
my $do_deps = 1;
my $TESTING='jessie';

my $debug = 0;
my $now = time;

sub debug {
	my $msg = shift;
	print $msg if ($debug);
}

sub do_query {
	my $handle = shift;
	my $query = shift;

	print ((time-$now)." $query\n") if $debug;
	my $sthc = $handle->prepare($query);
	$sthc->execute();
	return $sthc;
}

sub addsources {
	my $handle = shift;
	my $query = shift;
	my $srcs = shift;
	my $origin = shift;
	my $sthc = do_query($handle,$query);
	while (my $source = $sthc->fetchrow()) {
		if (!defined($srcs->{$source})) {
			$srcs->{$source} = $origin;
		}
	}
}

sub get_depends {
	my $handle = shift;
	my $query = shift;
	my $type = shift;
	my $pkgs = shift;
	my $sthc = do_query($handle,$query);
	while (my ($pkg,$deps) = $sthc->fetchrow_array()) {
		next unless $deps;
		foreach my $dep (split(/\s*[|,]\s*/,$deps)) {
			$dep =~ s/( |\(|\[).*//;
			my $info = "$pkg $type $dep";
			unless (defined $pkgs->{$dep}) {
				$pkgs->{$dep} = $info;
			}
		}
	}
}

sub add_pkg_sources {
	my $handle = shift;
	my $srcs = shift;
	my $pkgs = shift;

	my $newsrcs = {};
	my $query = "select source,package from packages where ".
		" release='$TESTING' and ".
		" package in ('".join("','",keys %$pkgs)."')";
	my $sthc = do_query($handle,$query);
	while (my ($source,$package) = $sthc->fetchrow_array()) {
		next if defined($srcs->{$source});
		$srcs->{$source} = $pkgs->{$package};
		$newsrcs->{$source} = $pkgs->{$package};
	}
	return $newsrcs;
}

my $dbh = DBI->connect("dbi:Pg:dbname=udd;port=5452;user=udd");

my $sthc = do_query($dbh,"select max(insts) from popcon");
my $pg = $sthc->fetchrow_hashref();
my $popcon_max = $pg->{"max"};
my $minpopcon = int($popcon_max * $POPCON_PERCENT/100);

debug "# Popcon submissions: $popcon_max -- $POPCON_PERCENT% = $minpopcon\n";

my $srcs = {map { $_ => "manual" } @$INC_SRC};
debug "# building initial list\n";

addsources($dbh,"select distinct source from sources where
	release='$TESTING' and
	( source in (select source from packages where release='$TESTING' and priority in ('standard', 'important', 'required')));
	",$srcs,"priority");

addsources($dbh,"select distinct source from sources where
	release='$TESTING' and
	( source in (select source from popcon_src where insts >= $minpopcon))
	",$srcs,"popcon");

addsources($dbh,"select distinct source from sources where
	release='$TESTING' and
    ( source in (select source from packages where section='debian-installer' and release='$TESTING'))
	",$srcs,"d-i");


foreach my $remove (@$EXC_SRC) {
	delete $srcs->{$remove};
}

debug "# Initial list: ".join(" ",sort keys %$srcs)."\n";
debug "# Now recursively getting build-depends...\n";
my $round = 1;
my $newsrcs = $srcs;

while (1) {
	debug "# Round $round, #srcs = ".(scalar keys %$srcs)."\n";
	my $pkgs = {};

	debug "# Getting build-depends for sources\n";
	get_depends($dbh,"select source,build_depends from sources
		where release='$TESTING' and source in ('".join("','",keys %$newsrcs)."')","build-depends",$pkgs);

	debug "# Getting sources for build-depends\n";
	my $newsrcs_a = add_pkg_sources($dbh,$srcs,$pkgs);

	my $newsrcs_b = {};
	if ($do_deps) {
		$pkgs = {};
		debug "# Getting depends for sources\n";
		get_depends($dbh,"select package,depends from packages
			where release='$TESTING' and source in ('".join("','",keys %$newsrcs)."')","depends",$pkgs);

		debug "# Getting sources for depends\n";
		$newsrcs_b = add_pkg_sources($dbh,$srcs,$pkgs);
	}

	$newsrcs = {%$newsrcs_a,%$newsrcs_b};

	debug "# Adding ".(scalar keys %$newsrcs)." source packages: ".join(" ",sort keys %$newsrcs)."\n";
	last unless scalar keys %$newsrcs;
	$round++;
	last if ($round > 20);
}

#print "sources:\n";
#print Dumper $srcs;

debug "# Final list of ".(scalar keys %$srcs)." key source packages:\n";
do_query($dbh,"DELETE FROM key_packages;");
my $insert_handle = $dbh->prepare("INSERT INTO key_packages ".
	"(source, reason) VALUES (\$1,\$2);");
foreach my $source (sort keys %$srcs) {
	my $reason = $srcs->{$source};
	debug "$source\t$reason\n";
	$insert_handle->execute($source,$reason);
}

do_query($dbh,"ANALYZE key_packages");


