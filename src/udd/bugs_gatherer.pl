#!/usr/bin/perl -w
# Last-Modified: <Mon Aug 11 13:55:12 2008>

use strict;
use warnings;

use FindBin '$Bin';

# We need our own copy of Debbugs::Status for now
use lib $Bin, qw{/org/udd.debian.net/mirrors/bugs.debian.org/perl};

use DBI;
use DBI qw{:sql_types};
use YAML::Syck;
use Time::Local;

use Debbugs::Bugs qw{get_bugs};
use Debbugs::Status qw{read_bug get_bug_status bug_presence};
use Debbugs::Packages qw{binarytosource};
use Debbugs::Config qw{:globals};
use Debbugs::User;
#use Debbugs::User qw{read_usertags};

$YAML::Syck::ImplicitTyping = 1;

#Used for measuring time
my $t;
my $timing = 1;

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

sub setup {
	my ($config, $source, $dbh) = @_;
	my $schema = $config->{general}->{'schema-dir'} . '/' . $config->{$source}->{schema};
	open SQL, "<",  $schema or die $!;
	my $command = join "", <SQL>;
	close SQL;
	$command =~ s/%\(([^)]+)\)s/$config->{$source}->{$1}/g;
	$dbh->prepare($command)->execute() or die $!;
}

sub drop {
	my ($config, $source, $dbh) = @_;
	map {
		$dbh->prepare("DROP VIEW $_")->execute() or die $!;
	}
	qw{bugs_rt_affects_stable bugs_rt_affects_testing_and_unstable bugs_rt_affects_unstable bugs_rt_affects_testing};

	foreach my $prefix ($config->{$source}->{table}, $config->{$source}->{'archived-table'}) {
		foreach my $postfix ('', qw{_merged_with _found_in _fixed_in _tags}) {
			$dbh->prepare("DROP TABLE $prefix$postfix")->execute() or die $!;
		}
	}
	$dbh->prepare("DROP TABLE " . $config->{$source}->{'usertags-table'})->execute() or die $!;
}

sub run_usertags {
	my ($config, $source, $dbh) = @_;
	my %src_config = %{$config->{$source}};
	my $table = $src_config{'usertags-table'} or die "usertags-table not specified for source $source";
	our $timing;
	our $t;


	$t = time();
	# Free usertags table
	$dbh->do("DELETE FROM $table") or die
		"Couldn't empty $table: $!";
	print "Deleting usertags: ",(time() - $t),"s\n" if $timing;
	$t = time();
	# read and insert user tags
	my @users = get_bugs_users();
	foreach my $user (@users) {
		#read_usertags(\%tags, $user);
		my $u = Debbugs::User->new($user);
		my %tags = %{$u->{tags}};
		$user = $dbh->quote($user);
		foreach my $tag (keys %tags) {
			my $qtag = $dbh->quote($tag);
			map { $dbh->do("INSERT INTO $table VALUES ($user, $qtag, $_)") or die $! } @{$tags{$tag}};
		}
	}
}

sub run {
	my ($config, $source, $dbh) = @_;

	our $t;
	our $timing;
	print "Inserting usertags: ",(time() - $t),"s\n" if $timing;
	$t = time();
	run_usertags($config, $source, $dbh);

	my %src_config = %{$config->{$source}};
	my $table = $src_config{table};
	my $archived_table = $src_config{'archived-table'};

	my @modified_bugs;
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
	if($src_config{archived}) {
		@modified_bugs = get_bugs(archive => 1);
	} else {
		@modified_bugs = get_bugs();
	}

	my @modified_bugs2;
	if ($src_config{debug}) {
		foreach $b (@modified_bugs) {
			push(@modified_bugs2, $b) if ($b =~ /0$/);
		}
		@modified_bugs = @modified_bugs2;
	}

	print "Fetching list of ",scalar(@modified_bugs), " bugs to insert: ",(time() - $t),"s\n" if $timing;
	$t = time();

	foreach my $prefix ($table, $archived_table) {
		foreach my $postfix ('', qw{_merged_with _found_in _fixed_in _tags}) {
			my $sth = $dbh->prepare("DELETE FROM $prefix$postfix WHERE id = \$1");
			map {
				$sth->execute($_) or die $!;
			} @modified_bugs;
		}
	}
	print "Deleting bugs: ",(time() - $t),"s\n" if $timing;
	$t = time();

	# Used to chache binary to source mappings
	my %binarytosource = ();
	# XXX What if a bug is in location 'db' (which currently doesn't exist)
	my $location = $src_config{archived} ? 'archive' : 'db_h';
	#my $table = $src_config{archived} ? 'bugs_archived' : 'bugs';
	$table = $src_config{archived} ? $archived_table : $table;
	# Read all bugs
	my $insert_bugs_handle = $dbh->prepare("INSERT INTO $table VALUES (\$1, \$2, \$3, \$4::abstime, \$5, \$6, \$7, \$8, \$9, \$10::abstime, \$11, \$12, \$13)");
	my $insert_bugs_found_handle = $dbh->prepare("INSERT INTO ${table}_found_in VALUES (\$1, \$2)");
	my $insert_bugs_fixed_handle = $dbh->prepare("INSERT INTO ${table}_fixed_in VALUES (\$1, \$2)");
	my $insert_bugs_merged_handle = $dbh->prepare("INSERT INTO ${table}_merged_with VALUES (\$1, \$2)");
	my $insert_bugs_tags_handle = $dbh->prepare("INSERT INTO ${table}_tags VALUES (\$1, \$2)");
	$insert_bugs_handle->bind_param(4, undef, SQL_INTEGER);
	$insert_bugs_handle->bind_param(10, undef, SQL_INTEGER);

	print "Inserting bugs: ",(time() - $t),"s\n" if $timing;
	$t = time();
	foreach my $bug_nr (@modified_bugs) {
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
		my @tags = map {$dbh->quote($_) } split / /, $bug{keywords};

		# log_modified and date are not necessarily set. If they are not available, they
		# are assumed to be epoch (i.e. bug #4170)
		map {
			if($bug{$_}) {
				#$bug{$_} = "$bug{$_}::abstime";
				$bug{$_} = int($bug{$_});
			} else {
				$bug{$_} = 0;
			}
		} qw{date log_modified};


		if(not exists $binarytosource{$bug{package}}) {
			$binarytosource{$bug{package}} = (binarytosource($bug{package}))[0];
		}
		my $source = $binarytosource{$bug{package}};

		if(not defined $source) {
		# if source is not defined, then we $bug{package} is likely to
		# be a source package name (or the source package has the same
		# name as the binary package). See #480818 for ex.
			$source = $dbh->quote($bug{package});
		} else {
			$source = $dbh->quote($source);
		}

		#Calculate bug presence in distributions
		my ($present_in_stable, $present_in_testing, $present_in_unstable);
		if($src_config{archived}) {
			$present_in_stable = $present_in_testing = $present_in_unstable = 'FALSE';
		} else {
			$present_in_stable =
				bug_presence(bug => $bug_nr, status => \%bug,
							 dist => 'stable');
			$present_in_testing =
				bug_presence(bug => $bug_nr, status => \%bug,
							 dist => 'testing');
			$present_in_unstable =
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
		}

		# Insert data into bugs table
		$insert_bugs_handle->execute($bug_nr, $bug{package}, $source, $bug{date}, $bug{pending},
			$bug{severity}, $bug{originator}, $bug{owner}, $bug{subject}, $bug{log_modified},
			$present_in_stable, $present_in_testing, $present_in_unstable) or die $!;

		# insert data into bug_fixed_in and bug_found_in tables
		foreach my $version (without_duplicates(@found_versions)) {
			$insert_bugs_found_handle->execute($bug_nr, $version) or die $!;
		}
		foreach my $version (without_duplicates(@fixed_versions)) {
			$insert_bugs_fixed_handle->execute($bug_nr, $version) or die $!;
		}
		foreach my $mergee (without_duplicates(split / /, $bug{mergedwith})) {
			$insert_bugs_merged_handle->execute($bug_nr, $mergee) or die $!;
		}
		foreach my $tag (without_duplicates(@tags)) {
			$insert_bugs_tags_handle->execute($bug_nr, $tag) or die $!;
		}
	}
}

sub main {
	if(@ARGV != 3) {
		print STDERR "Usage: $0 <config> <command> <source>\n";
		exit 1;
	}

	our $t;
	our $timing;

	my $config = LoadFile($ARGV[0]) or die "Could not load configuration: $!";
	my $command = $ARGV[1];
	my $source = $ARGV[2];

	my $dbname = $config->{general}->{dbname};
	# Connection to DB
	my $dbh = DBI->connect("dbi:Pg:dbname=$dbname");
	# We want to commit the transaction as a hole at the end
	$dbh->{AutoCommit} = 0;

	if($command eq 'run') {
		run($config, $source, $dbh);
	} elsif ($command eq 'setup') {
		setup($config, $source, $dbh);
	} elsif ($command eq 'drop') {
		drop($config, $source, $dbh);
	} else {
		print STDERR "<command> has to be one of run, drop and setup\n";
		exit(1)
	}

	$dbh->commit();
	print "Committing bugs: ",(time() - $t),"s\n" if $timing;
}

main();
