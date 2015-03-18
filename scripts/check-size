#!/usr/bin/perl
# Last-Modified: <Sat Jul 26 12:46:51 2008>

# This script is part of the Debian Ultimate Database Project
# It's used to check the size of the postgres database in use
# synopsis: check-size.pl <configuration file>

use strict;
use warnings;

use DBI;
use YAML::Syck;

$YAML::Syck::ImplicitTyping = 1;

defined $ARGV[0] or die "Usage: $0 <config-file>";

my $config = LoadFile($ARGV[0]);

my $dbname = $config->{general}->{dbname};
my $dbh = DBI->connect("dbi:Pg:dbname=$dbname") or die "Couldn't connect to database: $!";

my $sth = $dbh->prepare("SELECT pg_database.datname,\
	pg_size_pretty(pg_database_size(pg_database.datname)) AS size\
	FROM pg_database;");
$sth->execute() or die $!;

while(my ($dbname, $dbsize) = $sth->fetchrow_array()) {
	if($dbname eq $config->{general}->{dbname}) {
		print "$dbsize\n";
		exit 0;
	}
}

print STDERR "Couldn't find database in response\n";
exit 1;
