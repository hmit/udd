#!/usr/bin/perl -w
# Last-Modified: <Mon Aug 18 14:29:47 2008>

use strict;
use warnings;

use FindBin '$Bin';

# We need our own copy of Debbugs::Status for now
use lib $Bin, qw{/srv/bugs.debian.org/perl /org/udd.debian.org/mirrors/bugs.debian.org/perl};

use DBI;
use DBI qw{:sql_types};
use YAML::Syck;
use Time::Local;

use Debbugs::Bugs qw{get_bugs};
use Debbugs::Status qw{read_bug get_bug_status bug_presence};
use Debbugs::Packages qw{getpkgsrc};
use Debbugs::Config qw{:globals %config};
use Debbugs::User;
use Mail::Address;
#use Debbugs::User qw{read_usertags};
use File::stat;
use Time::localtime;

$YAML::Syck::ImplicitTyping = 1;

#Used for measuring time
our $t;
our $timing = 0;
my %pkgsrc = %{getpkgsrc()};
our @archs = grep {  !/(^m68k$|^sparc|^hurd)/ } @{$config{default_architectures}};

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
	return ((stat(shift))->mtime);
}

sub get_modified_bugs {
	my $prune_stamp = shift;
	die "Argument required" unless defined $prune_stamp;
	my $top_dir = $gSpoolDir;
	my @result = ();
	foreach my $sub (qw(db-h)) {
		my $spool = "$top_dir/$sub";
		foreach my $subsub (glob "$spool/*") {
			print "looking for modified bugs in $subsub\n" if $timing;
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

sub get_bugs_modified {
	my $subdir = shift;
	my $top_dir = $gSpoolDir;
	my $result = ();
	my $spool = "$top_dir/$subdir";
	foreach my $subsub (glob "$spool/*") {
		if( -d $subsub ) {
			print "looking for modified bugs in $subsub\n" if $timing;
			foreach my $log (glob "$subsub/*.log") {
				if ($log =~ m;^(.*)/([^/]*)\.log;) {
					my $path = $1;
					my $id = $2;
					# skip bugs with only log file
					# TODO should this be .status of .summary?
					if (-e "$path/$id.status") {
						$result->{$id} = get_mtime($log);
					}
				}
			}
		}
	}
	return $result;
}

sub without_duplicates {
	my %h = ();
	return (grep { ($h{$_}++ == 0) || 0 } @_);
}

sub get_source {
	my $pkg = shift;

	if ($pkg =~ m/,/) {
		my @pkgs = split(/\s*[, ]\s*/, $pkg);
		my %srcs = ();
		foreach my $p (@pkgs) {
			my $src = get_source($p);
			$srcs{$src} = 1;
		}
		return join(",",sort keys %srcs);

	} else {
		my $srcpkg;
		if ($pkg =~ /^src:(.*)/)
		{
			$srcpkg = $1;
		} else {
			$srcpkg = exists($pkgsrc{$pkg}) ? $pkgsrc{$pkg} : $pkg;
		}
		return $srcpkg;
	}
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
			map { $dbh->do("INSERT INTO $table (email, tag, id) VALUES ($user, $qtag, $_)") or die $! } @{$tags{$tag}};
		}
	}
	# importing usertags for merged bugs
	$dbh->do("insert into bugs_usertags (email, tag, id) select email, tag, merged_with from bugs_usertags bu, bugs_merged_with bmw where bu.id = bmw.id and (email, tag, merged_with) not in (select email, tag, id from bugs_usertags)") or die $!;
	print "Inserting usertags: ",(time() - $t),"s\n" if $timing;
}

sub update_bug {
	my $config = shift;
	my $source = shift;
	my $dbh = shift;
	my $bug_nr = shift;

	my %src_config = %{$config->{$source}};
	my $unarchived_table = $src_config{table};
	my $archived_table = $src_config{'archived-table'};

	my $location = $src_config{archived} ? 'archive' : 'db_h';
	my $table = $src_config{archived} ? $archived_table : $unarchived_table;
	my $other_table = $src_config{archived} ? $unarchived_table : $archived_table;

	my $start = time();

	foreach my $prefix ($unarchived_table, $archived_table) {
		foreach my $postfix (qw{_packages _merged_with _found_in _fixed_in _tags _blocks _blockedby}, '') {
			$dbh->do("DELETE FROM $prefix$postfix where id in ($bug_nr)") or die;
		}
	}
	$dbh->do("DELETE FROM ${other_table}_stamps where id in ($bug_nr)") or die;

	# Read all bugs
	my $insert_bugs_handle = $dbh->prepare("INSERT INTO $table ( ".
		"id, ".
		"package, ".
		"source, ".
		"arrival, ".
		"status, ".
		"severity, ".
		"submitter, ".
		"submitter_name, ".
		"submitter_email, ".
		"owner, ".
		"owner_name, ".
		"owner_email, ".
		"done, ".
		"done_name, ".
		"done_email, ".
		"done_date, ".
		"title, ".
		"forwarded, ".
		"last_modified, ".
		"affects_oldstable, ".
		"affects_stable, ".
		"affects_testing, ".
		"affects_unstable, ".
		"affects_experimental, ".
		"affected_packages, ".
		"affected_sources ".
	") VALUES (".
		"\$1, ".
		"\$2, ".
		"\$3, ".
		"\$4::abstime, ".
		"\$5, ".
		"\$6, ".
		"\$7, ".
		"\$8, ".
		"\$9, ".
		"\$10, ".
		"\$11, ".
		"\$12, ".
		"\$13, ".
		"\$14, ".
		"\$15, ".
		"\$16::abstime, ".
		"\$17, ".
		"\$18, ".
		"\$19::abstime, ".
		"\$20, ".
		"\$21, ".
		"\$22, ".
		"\$23, ".
		"\$24, ".
		"\$25, ".
		"\$26 ".
	")");
	my $insert_bugs_packages_handle = $dbh->prepare("INSERT INTO ${table}_packages (id, package, source) VALUES (\$1, \$2, \$3)");
	my $insert_bugs_found_handle = $dbh->prepare("INSERT INTO ${table}_found_in (id, version) VALUES (\$1, \$2)");
	my $insert_bugs_fixed_handle = $dbh->prepare("INSERT INTO ${table}_fixed_in (id, version) VALUES (\$1, \$2)");
	my $insert_bugs_merged_handle = $dbh->prepare("INSERT INTO ${table}_merged_with (id, merged_with) VALUES (\$1, \$2)");
	my $insert_bugs_tags_handle = $dbh->prepare("INSERT INTO ${table}_tags (id, tag) VALUES (\$1, \$2)");
	my $insert_bugs_blocks_handle = $dbh->prepare("INSERT INTO ${table}_blocks (id, blocked) VALUES (\$1, \$2)");
	my $insert_bugs_blockedby_handle = $dbh->prepare("INSERT INTO ${table}_blockedby (id, blocker) VALUES (\$1, \$2)");
	$insert_bugs_handle->bind_param(4, undef, SQL_INTEGER);
	$insert_bugs_handle->bind_param(16, undef, SQL_INTEGER);
	$insert_bugs_handle->bind_param(19, undef, SQL_INTEGER);

	# Fetch bug using Debbugs
	# Bugs which were once archived and have been unarchived again will appear in get_bugs(archive => 1).
	# However, those bugs are not to be found in location 'archive', so we detect them, and skip them
	my $bug_ref = read_bug(bug => $bug_nr, location => $location) or (print STDERR "Could not read file for bug $bug_nr; skipping\n" and return);
	# Yeah, great, why does get_bug_status not accept a location?
	my %bug = %{get_bug_status(bug => $bug_nr, status => $bug_ref)};
	
	# Convert data where necessary
	my @found_versions = @{$bug{found_versions}};
	my @fixed_versions = @{$bug{fixed_versions}};
	my @tags = split / /, $bug{keywords};

	# log_modified and date are not necessarily set. If they are not available, they
	# are assumed to be epoch (i.e. bug #4170)
	map {
		if($bug{$_}) {
			$bug{$_} = int($bug{$_});
		} else {
			$bug{$_} = 0;
		}
	} qw{date log_modified done_date};

	my $srcpkg = get_source($bug{package});
	my $affected_packages = $bug{affects};
	my $affected_sources = get_source($bug{affects});

	# split emails
	my (@addr, $submitter_name, $submitter_email, $owner_name, $owner_email, $done_name, $done_email);
	if ($bug{originator}) {
		@addr = Mail::Address->parse($bug{originator});
		$submitter_name = $addr[0]->phrase;
		$submitter_email = $addr[0]->address;
	} else {
		$submitter_name = '';
		$submitter_email = '';
	}

	if ($bug{owner}) {
		@addr = Mail::Address->parse($bug{owner});
		$owner_name = $addr[0]->phrase;
		$owner_email = $addr[0]->address;
	} else {
		$owner_name = '';
		$owner_email = '';
	}

	if ($bug{done}) {
		@addr = Mail::Address->parse($bug{done});
		$done_name = $addr[0]->phrase;
		$done_email = $addr[0]->address;
	} else {
		$done_name = '';
		$done_email = '';
	}

	#Calculate bug presence in distributions
	my ($present_in_oldstable, $present_in_stable, $present_in_testing, $present_in_unstable, $present_in_experimental);
	if($src_config{archived}) {
		$present_in_oldstable = $present_in_stable = $present_in_testing = $present_in_unstable = $present_in_experimental = 'FALSE';
	} else {
		$present_in_oldstable =
			bug_presence(bug => $bug_nr, status => \%bug,
						 dist => 'oldstable',
						 arch => \@archs);
		$present_in_stable =
			bug_presence(bug => $bug_nr, status => \%bug,
						 dist => 'stable',
						 arch => \@archs);
		$present_in_testing =
			bug_presence(bug => $bug_nr, status => \%bug,
						 dist => 'testing',
						 arch => \@archs);
		$present_in_unstable =
			bug_presence(bug => $bug_nr, status => \%bug,
						 dist => 'unstable',
						 arch => \@archs);
		$present_in_experimental =
			bug_presence(bug => $bug_nr, status => \%bug,
						 dist => 'experimental',
						 arch => \@archs);

		if(!defined($present_in_oldstable) or !defined($present_in_stable) or !defined($present_in_unstable) or !defined($present_in_testing) or !defined($present_in_experimental)) {
			print "NUMBER: $bug_nr\n";
		}
	
		if(defined($present_in_oldstable) and ($present_in_oldstable eq 'absent' or $present_in_oldstable eq 'fixed')) {
			$present_in_oldstable = 'FALSE';
		} else {
			$present_in_oldstable = 'TRUE';
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
		if(defined($present_in_experimental) and ($present_in_experimental eq 'absent' or $present_in_experimental eq 'fixed')) {
			$present_in_experimental = 'FALSE';
		} else {
			$present_in_experimental = 'TRUE';
		}
	}

	# Insert data into bugs table
	$insert_bugs_handle->execute(
		$bug_nr,
		$bug{package},
		$srcpkg,
		$bug{date},
		$bug{pending},
		$bug{severity},
		$bug{originator},
		$submitter_name,
		$submitter_email,
		$bug{owner},
		$owner_name,
		$owner_email,
		$bug{done},
		$done_name,
		$done_email,
		$bug{done_date},
		$bug{subject},
		$bug{forwarded},
		$bug{log_modified},
		$present_in_oldstable,
		$present_in_stable,
		$present_in_testing,
		$present_in_unstable,
		$present_in_experimental,
		$affected_packages,
		$affected_sources
	) or die $!;

	my $src;
	foreach my $pkg (keys %{{ map { $_ => 1 } split(/\s*[, ]\s*/, $bug{package})}}) {
		$src = get_source($pkg);
		$insert_bugs_packages_handle->execute($bug_nr, $pkg, $src) or die $!;
	}

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
	foreach my $blocked (without_duplicates(split / /, $bug{blocks})) {
		$insert_bugs_blocks_handle->execute($bug_nr, $blocked) or die $!;
	}
	foreach my $blocker (without_duplicates(split / /, $bug{blockedby})) {
		$insert_bugs_blockedby_handle->execute($bug_nr, $blocker) or die $!;
	}
	foreach my $tag (without_duplicates(@tags)) {
		$insert_bugs_tags_handle->execute($bug_nr, $tag) or die $!;
	}

	my $update_stamp_handle = $dbh->prepare("UPDATE ${table}_stamps SET db_updated = \$1 WHERE id = \$2");
	my $update_res = $update_stamp_handle->execute($start,$bug_nr) or die $!;
	if ($update_res < 1) {
		my $insert_stamp_handle = $dbh->prepare("INSERT INTO ${table}_stamps (id, db_updated) VALUES (\$1, \$2)");
		$insert_stamp_handle->execute($bug_nr,$start) or die $!;
	}
}

sub update_bugs {

	my $config = shift;
	my $source = shift;
	my $dbh = shift;
	my $bugs = shift;
	my $limit = shift||1000;

	print "Fetching list of ",scalar(@$bugs), " bugs to insert: ",(time() - $t),"s\n" if $timing;
	$t = time();
	my $counter = 0;
	foreach my $bug_nr (@$bugs) {
		$counter++;
		update_bug($config,$source,$dbh,$bug_nr);
		if ($timing) {
			print "$bug_nr $counter/".(scalar @$bugs)."\n";
		}
		last if ($counter >= $limit);
	}
	print "Inserting bugs: ",(time() - $t),"s\n" if $timing;

	return $counter;
}

sub run {
	my ($config, $source, $dbh) = @_;

	our $t;
	our $timing;
	my %src_config = %{$config->{$source}};
	my $unarchived_table = $src_config{table};
	my $archived_table = $src_config{'archived-table'};
	my $table = $src_config{archived} ? $archived_table : $unarchived_table;

	my $limit = $src_config{'limit'} || 1000;

	my @modified_bugs;

	my $sth = $dbh->prepare("SELECT id,db_updated FROM ${table}_stamps");
	$sth->execute;
	my $bugs_db_updated = $sth->fetchall_hashref('id');

	if($src_config{archived}) {
		# some bugs (the unarchived ones) are in both list. exclude them.
		my %unarchived;
		foreach my $b (get_bugs()) {
			$unarchived{$b} = 1;
		}
		foreach my $b (get_bugs(archive => 1)) {
			push(@modified_bugs, $b) if not $unarchived{$b};
		}
	} else {
		@modified_bugs = get_bugs();
	}
	my @modified_bugs2;
	if ($src_config{debug}) {
		print "Running in debug mode with restricted bug list!!\n";
		foreach my $b (@modified_bugs) {
			push(@modified_bugs2, $b) if ($b =~ /58$/);
			push(@modified_bugs2, $b) if ($b == '624507' or $b == '694352' or $b == '692948' or $b == '692979' or $b == '654491' or $b == '696552' or $b == '694748' or $b == '667995' or $b == '661018');
		}
		@modified_bugs = @modified_bugs2;
	}

	# import new bugs
	@modified_bugs = grep { ! defined $bugs_db_updated->{$_} } @modified_bugs;
	my $counter = update_bugs($config,$source,$dbh,\@modified_bugs,$limit);
	$limit -= $counter;

	if ($limit > 0) {
		# we updated less bugs than the limit in the config file
		# update some of the olders bugs
		$sth = $dbh->prepare("SELECT id FROM ${table}_stamps ORDER BY db_updated LIMIT $limit");
		$sth->execute;
		my $oldest_bugs = $sth->fetchall_hashref('id');

		my @bug_ids = keys %$oldest_bugs;
		$counter = update_bugs($config,$source,$dbh,\@bug_ids,$limit);
		$limit -= $counter;
	}
}

sub run_modified {
	my ($config, $source, $dbh) = @_;

	our $t;
	our $timing;
	my %src_config = %{$config->{$source}};
	my $unarchived_table = $src_config{table};
	my $archived_table = $src_config{'archived-table'};
	my $table = $src_config{archived} ? $archived_table : $unarchived_table;

	my @modified_bugs;

	print "start looking for modified bugs\n" if $timing;
	my $sth = $dbh->prepare("SELECT id,db_updated FROM ${table}_stamps");
	$sth->execute;
	my $bugs_db_updated = $sth->fetchall_hashref('id');

	my $location = $src_config{archived} ? "archive" : "db-h";
	my $bugs_modified = get_bugs_modified($location);

	foreach my $bugid (keys %$bugs_modified) {
		if (
			# no stamp for this bug: new bug
			(!defined($bugs_db_updated->{$bugid})) ||
			# log file was modified after last db update
			($bugs_modified->{$bugid} > $bugs_db_updated->{$bugid}->{"db_updated"})
		) {
			push @modified_bugs,$bugid;
		}
	}
	my $counter = update_bugs($config,$source,$dbh,\@modified_bugs);
}

sub check_commit {
	my ($config, $source, $dbh) = @_;
	my %src_config = %{$config->{$source}};
	my $table = $src_config{table};

	# Check for broken imports
	if (!$src_config{debug}) {
		my $sthc = $dbh->prepare("select count(*) from bugs where id in (select id from bugs_rt_affects_unstable) and id > 500000");
		$sthc->execute();
		my $rowsc = $sthc->fetchrow_array();
		if ($rowsc < 1000) {
			die("Broken bugs import: not enough bugs affecting unstable\n");
		}
	}

#	if (stat($gSpoolDir."/../versions/indices/binsrc.idx")->mtime > $t) {
#		die("Broken bugs import: binsrc.idx changed during import\n");
#	}
#	if (stat($gSpoolDir."/../versions/indices/srcbin.idx")->mtime > $t) {
#		die("Broken bugs import: srcbin.idx changed during import\n");
#	}
#	if (stat($gSpoolDir."/../versions/indices/versions.idx")->mtime > $t) {
#		die("Broken bugs import: versions.idx changed during import\n");
#	}

	if (defined $table) {
		foreach my $postfix (qw{_packages _merged_with _found_in _fixed_in _tags}, '') {
			my $sth = $dbh->prepare("ANALYZE $table$postfix");
			$sth->execute() or die $!;
		}
	}

	if ($source eq "bugs-usertags") {
		my $sth = $dbh->prepare("ANALYZE ".$src_config{'usertags-table'});
		$sth->execute() or die $!;
	}

	print "Analyzing bugs: ",(time() - $t),"s\n" if $timing;

	$dbh->commit();
	print "Committing bugs: ",(time() - $t),"s\n" if $timing;
}

sub main {
	if(@ARGV != 3) {
		print STDERR "Usage: $0 <config> <command> <source>\n";
		exit 1;
	}

	our $t = time();
	our $timing;

	my $config = LoadFile($ARGV[0]) or die "Could not load configuration: $!";
	my $command = $ARGV[1];
	my $source = $ARGV[2];

	my $dbname = $config->{general}->{dbname};
	my $dbport;
	if ($config->{general}->{dbport} ne '') {
	  $dbport = ";port=".$config->{general}->{dbport};
	} else {
	  $dbport = "";
	}
	# Connection to DB
	my $dbh = DBI->connect("dbi:Pg:dbname=$dbname".$dbport);
	# We want to commit the transaction as a hole at the end
	$dbh->{AutoCommit} = 0;
	$dbh->do('SET CONSTRAINTS ALL DEFERRED');

	if($command eq 'run') {
		if ($source eq "bugs-usertags") {
			run_usertags($config, $source, $dbh);
		} elsif ($source eq "bugs-modified") {
			run_modified($config, $source, $dbh);
		} elsif ($source eq "bugs") {
			#run_modified($config, $source, $dbh);
			run($config, $source, $dbh);
		} else {
			run($config, $source, $dbh);
		}
		check_commit($config, $source, $dbh);
	} else {
		print STDERR "<command> has to be one of run, drop and setup\n";
		exit(1)
	}

}

main();
