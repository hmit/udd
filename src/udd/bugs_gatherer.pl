#!/usr/bin/perl
# Last-Modified: <Wed Jul 23 10:02:51 2008>

use strict;
use warnings;

use lib qw{/org/udd.debian.net/mirrors/bugs.debian.org/perl};

use DBI;
use YAML::Syck;

use Debbugs::Bugs qw{get_bugs};
use Debbugs::Status qw{readbug get_bug_status};

use POSIX qw{strftime};

$YAML::Syck::ImplicitTyping = 1;

sub main {
	if(@ARGV != 2) {
		print STDERR "Usage: $0 <config> <source>";
		exit 1;
	}

	my $config = LoadFile($ARGV[0]) or die "Could not load configuration: $!";
	my $source = $ARGV[1];

	my $dbname = $config->{general}->{dbname};
	# Connection to DB
	my $dbh = DBI->connect("dbi:Pg:dbname=$dbname");
	# We want to commit the transaction as a hole at the end
	$dbh->{AutoCommit} = 0;

	$dbh->prepare("DELETE FROM bugs")->execute();
	$dbh->prepare("DELETE from bug_found_in")->execute();
	$dbh->prepare("DELETE from bug_fixed_in")->execute();

	# Read all bugs
	foreach my $bug_nr (get_bugs()) {
		my %bug = %{readbug($bug_nr)};
		# Construct insertion query
		my $date = strftime("%Y-%m-%d %T", localtime($bug{date}));
		my $log_modified = strftime("%Y-%m-%d %T", localtime($bug{log_modified}));
		map { $bug{$_} = $dbh->quote($bug{$_}) } qw(subject originator owner);
		my @found_versions = map { $dbh->quote($_) } @{$bug{found_versions}};
		my @fixed_versions = map { $dbh->quote($_) } @{$bug{fixed_versions}};

		# Insert data into bugs table
		my $query = "INSERT INTO bugs VALUES ($bug_nr, '$bug{package}', '$date', \
		             NULL, '$bug{severity}', '$bug{keywords}', $bug{originator}, $bug{owner}, \
					 $bug{subject}, '$log_modified')";
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
	}

	$dbh->commit();
}

main();
