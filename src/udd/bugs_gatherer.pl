#!/usr/bin/perl
# Last-Modified: <Sun Aug  3 13:11:34 2008>

use strict;
use warnings;

use FindBin '$Bin';

# We need our own copy of Debbugs::Status for now
use lib $Bin, qw{/org/udd.debian.net/mirrors/bugs.debian.org/perl};

use DBI;
use YAML::Syck;
use Time::Local;

use Debbugs::Bugs qw{get_bugs};
use Debbugs::Status qw{read_bug get_bug_status bug_presence};
use Debbugs::Packages qw{binarytosource};
use Debbugs::Config qw{:globals};
use Debbugs::User qw{read_usertags};

$YAML::Syck::ImplicitTyping = 1;

# Return the list of usernames
sub get_bugs_users {
	my $topdir = "$gSpoolDir/user";
	my @ret = ();
	# see Debbugs::User::filefromemail for why 0...6
	for(my $i = 0; $i < 7; $i++) {
		my $dir = "$topdir/$i";
		opendir DIR, $dir or die "Can't open dir $dir: $!";
		# Replace all occurences of %dd with the corresponding
		# character represented by dd, where dd is a hexadecimal
		# number
		push @ret, map { s/%(..)/chr(hex($1))/ge; $_ } readdir DIR;
	}
	return @ret;
}

sub parse_time {
	if(shift =~ /(\d\d\d\d)-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)/) {
		return ($1, $2, $3, $4, $5, $6);
	}
	return undef;
}


sub get_db_max_last_modified {
	my $dbh = shift or die "Argument required";
	my $sth = $dbh->prepare("SELECT MAX (last_modified) FROM bugs");
	$sth->execute() or die $!;
	my $date = $sth->fetchrow_array();
	if(defined $date) {
		my ($year, $month, $day, $hour, $minute, $second) = parse_time($date);
		return timelocal($second, $minute, $hour, $day, $month-1, $year);
	} else {
		return 0;
	}
}

sub get_mtime {
	return ((stat(shift))[9]);
}

sub get_modified_bugs {
	my $prune_stamp = shift;
	die "Argument required" unless defined $prune_stamp;
	my $top_dir = $gSpoolDir;
	my @result = ();
	foreach my $sub (qw(archive db-h)) {
		my $spool = "$top_dir/$sub";
		foreach my $subsub (glob "$spool/*") {
			if( -d $subsub and get_mtime($subsub) > $prune_stamp ) {
				push @result, 
					map { s{.*/(.*)\.log}{$1}; $_ } 
						grep { get_mtime("$_") > $prune_stamp }
							glob "$subsub/*.log";
			}
		}
	}
	return \@result;
}

sub without_duplicates {
	my %h = ();
	return (grep { ($h{$_}++ == 0) || 0 } @_);
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



	# Free usertags table
	$dbh->prepare("DELETE FROM bug_user_tags")->execute() or die
		"Couldn't empty bug_user_tags: $!";

	# read and insert user tags
	my @users = get_bugs_users();
	foreach my $user (@users) {
		my %tags = ();
		read_usertags(\%tags, $user);
		$user = $dbh->quote($user);
		foreach my $tag (keys %tags) {
			my $qtag = $dbh->quote($tag);
			map { $dbh->prepare("INSERT INTO bug_user_tags VALUES ($user, $qtag, $_)")->execute() or die $! } @{$tags{$tag}};
		}
	}

	####### XXX EXPERIMENT
	####### XXX What to do with bugs both archived and unarchived
	#my $max_last_modified = get_db_max_last_modified($dbh);
	#my @modified_bugs;
	#if($max_last_modified) {
	#	@modified_bugs = @{get_modified_bugs($max_last_modified)};
		# Delete modified bugs
		#	for my $bug (@modified_bugs) {
		#		map {
		#			$dbh->prepare("DELETE FROM $_ WHERE id = $bug")->execute()
		#		} qw{bugs bug_merged_with bug_found_in bug_fixed_in};
		#	}
		#} else {
		#	@modified_bugs = get_bugs(archive => 'both');
		#}
		#@modified_bugs = without_duplicates(@modified_bugs);
	my @modified_bugs;
	if($src_config{archived}) {
		@modified_bugs = get_bugs(archive => 1);
	} else {
		@modified_bugs = get_bugs();
	}

	print scalar(@modified_bugs), " modified bugs\n";
	####### XXX EXPERIMENT

	# Get the bugs we want to import
	# my @bugs = $src_config{archived} ? get_bugs(archive => 1) : get_bugs();

	# Delete all bugs we are going to import
	for my $bug (@modified_bugs) {
		map {
			$dbh->prepare("DELETE FROM $_ WHERE id = $bug")->execute()
		} qw{bugs bug_merged_with bug_found_in bug_fixed_in};
	}
	print "Bugs deleted\n";

	# Used to chache binary to source mappings
	my %binarytosource = ();

	# XXX What if a bug is in location 'db' (which currently doesn't exist)
	my $location = $src_config{archived} ? 'archive' : 'db_h';
	# Read all bugs
	foreach my $bug_nr (@modified_bugs) {
		#next unless $bug_nr =~ /00$/;
		# Fetch bug using Debbugs
		# Bugs which were once archived and have been unarchived again will appear in get_bugs(archive => 1).
		# However, those bugs are not to be found in location 'archive', so we detect them, and skip them
		my $bug_ref = read_bug(bug => $bug_nr, location => $location) or (print STDERR "Could not read file for bug $bug_nr; skipping\n" and next);
		# Yeah, great, why does get_bug_status not accept a location?
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
			$binarytosource{$bug{package}} = (binarytosource($bug{package}))[0];
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
		foreach my $version (without_duplicates(@found_versions)) {
			$query = "INSERT INTO bug_found_in VALUES ($bug_nr, $version)";
			$dbh->prepare($query)->execute() or die $!;
		}
		foreach my $version (without_duplicates(@fixed_versions)) {
			$query = "INSERT INTO bug_fixed_in VALUES ($bug_nr, $version)";
			$dbh->prepare($query)->execute() or die $!;
		}
		foreach my $mergee (without_duplicates(split / /, $bug{mergedwith})) {
			$query = "INSERT INTO bug_merged_with VALUES ($bug_nr, $mergee)";
			$dbh->prepare($query)->execute() or die $!;
		}
	}

	$dbh->commit();
}

main();
