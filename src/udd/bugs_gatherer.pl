#!/usr/bin/perl
# Last-Modified: <Sun Jul 27 12:50:43 2008>

use strict;
use warnings;

use lib qw{./ /org/udd.debian.net/mirrors/bugs.debian.org/perl};

use DBI;
use YAML::Syck;

use Debbugs::Bugs qw{get_bugs};
use Debbugs::Status qw{read_bug get_bug_status bug_presence};
use Debbugs::Packages qw{binarytosource getpkgsrc};

use POSIX qw{strftime};
use Time::Local qw{timelocal};

$YAML::Syck::ImplicitTyping = 1;

sub parse_time {
	if(shift =~ /(\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)/) {
		return ($1, $2, $3, $4, $5, $6);
	}
	return undef;
}

sub is_bug_in_db {
	my ($dbh, $bug_nr) = @_;
	return $dbh->execute("SELECT * FROM bugs WHERE id = $bug_nr")->fetchrow_array();
}

sub main {
	if(@ARGV != 2) {
		print STDERR "Usage: $0 <config> <source>";
		exit 1;
	}

	my $config = LoadFile($ARGV[0]) or die "Could not load configuration: $!";
	my $source = $ARGV[1];
	my %src_config = %{$config->{$source}};

	my $dbname = $config->{general}->{dbname};
	# Connection to DB
	my $dbh = DBI->connect("dbi:Pg:dbname=$dbname");
	# We want to commit the transaction as a hole at the end
	$dbh->{AutoCommit} = 0;

	#delete the bug, if it exists
	$dbh->prepare("DELETE FROM bugs")->execute();
	$dbh->prepare("DELETE FROM bug_found_in")->execute();
	$dbh->prepare("DELETE FROM bug_fixed_in")->execute();
	$dbh->prepare("DELETE FROM bug_merged_with")->execute();

	my %binarytosource = ();

	my $location = $src_config{archived} ? 'archive' : 'db_h';
	# Read all bugs
	foreach my $bug_nr ($src_config{archived} ? get_bugs(archive => 1) : get_bugs()) {
		next unless $bug_nr =~ /00$/;
		# Fetch bug using Debbugs
		# Yeah, great, why does get_bug_status not accept a location?
		my $bug_ref = read_bug(bug => $bug_nr, location => $location) or (print STDERR "Could not read file for bug $bug_nr in $location; skipping\n" and next);
		my %bug = %{get_bug_status(bug => $bug_nr, status => $bug_ref)};
		
		# Convert data where necessary
		map { $bug{$_} = $dbh->quote($bug{$_}) } qw(subject originator owner pending);
		my @found_versions = map { $dbh->quote($_) } @{$bug{found_versions}};
		my @fixed_versions = map { $dbh->quote($_) } @{$bug{fixed_versions}};

		# log_modified and date are not necessarily set. If they are not available, they
		# are assumed to be epoch (i.e. bug #4170)
		map {
			if($bug{$_}) {
				$bug{$_} = "$bug{$_}::abstime";
			} else {
				$bug{$_} = '0::abstime';
			}
		} qw{date log_modified};


		if(not exists $binarytosource{$bug{package}}) {
			$binarytosource{$bug{package}} = binarytosource($bug{package});
		}
		my $source = $binarytosource{$bug{package}};

		if(not defined $source) {
			$source = 'NULL';
		} else {
			$source = $dbh->quote($source);
		}

		#Calculate bug presence in distributions
		my $present_in_stable =
			bug_presence(bug => $bug_nr, status => \%bug,
				         dist => 'stable');
		my $present_in_testing =
			bug_presence(bug => $bug_nr, status => \%bug,
				         dist => 'testing');
		my $present_in_unstable =
			bug_presence(bug => $bug_nr, status => \%bug,
				         dist => 'unstable');
		if(!defined($present_in_stable) or !defined($present_in_unstable) or !defined($present_in_testing)) {
			print "NUMBER: $bug_nr\n";
		}
		if(defined($present_in_stable) and ($present_in_stable eq 'absent' or $present_in_stable eq 'fixed')) {
			$present_in_stable = 'FALSE';
		} else {
			$present_in_stable = 'TRUE';
		}
		if(defined($present_in_testing) and ($present_in_testing eq 'absent' or $present_in_testing eq 'fixed')) {
			$present_in_testing = 'FALSE';
		} else {
			$present_in_testing = 'TRUE';
		}
		if(defined($present_in_unstable) and ($present_in_unstable eq 'absent' or $present_in_unstable eq 'fixed')) {
			$present_in_unstable = 'FALSE';
		} else {
			$present_in_unstable = 'TRUE';
		}


		# Insert data into bugs table
		my $query = "INSERT INTO bugs VALUES ($bug_nr, '$bug{package}', $source, $bug{date}, \
		             E$bug{pending}, '$bug{severity}', '$bug{keywords}', E$bug{originator}, E$bug{owner}, \
					 E$bug{subject}, $bug{log_modified}, $present_in_stable,
					 $present_in_testing, $present_in_unstable, " . ($src_config{archived} ? 'True' : 'False') . ")";
		# Execute insertion
		my $sth = $dbh->prepare($query);
		$sth->execute() or die $!;

		# insert data into bug_fixed_in and bug_found_in tables
		foreach my $version (@found_versions) {
			$query = "INSERT INTO bug_found_in VALUES ($bug_nr, $version)";
			$dbh->prepare($query)->execute() or die $!;
		}
		foreach my $version (@fixed_versions) {
			$query = "INSERT INTO bug_fixed_in VALUES ($bug_nr, $version)";
			$dbh->prepare($query)->execute() or die $!;
		}
		foreach my $mergee (split / /, $bug{mergedwith}) {
			$query = "INSERT INTO bug_merged_with VALUES ($bug_nr, $mergee)";
			$dbh->prepare($query)->execute() or die $!;
		}
	}

	$dbh->commit();
}

main();
