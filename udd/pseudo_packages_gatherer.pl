#!/usr/bin/perl -w

use strict;
use warnings;

use DBI;
use DBI qw{:sql_types};
use YAML::Syck;
use Mail::Address;

use Data::Dumper;

$YAML::Syck::ImplicitTyping = 1;

sub add_file {
	my $filename = shift;
	my $hashref = shift;
	my $key = shift;

	open(my $fh, '<', $filename) or die "cannot open file $filename";

	while (my $line = <$fh>) {
		if ($line =~ m/^\s*(\S+)\s+(\S+.*)\s*$/) {
			my $pkg = $1;
			my $val = $2;
			$hashref->{$pkg}->{$key} = $val;
		}
	}
	close($fh);
}

sub run {
	my ($config, $source, $dbh) = @_;

	my %src_config = %{$config->{$source}};
	my $table = $src_config{table};

	my %pseudopackages = ();

	add_file($src_config{"description-path"},\%pseudopackages,"description");
	add_file($src_config{"maintainers-path"},\%pseudopackages,"maintainer");

	$dbh->do("DELETE FROM ${table}") or die;
	my $insert_handle = $dbh->prepare("INSERT INTO $table ( ".
		"package, ".
		"maintainer, ".
		"maintainer_name, ".
		"maintainer_email, ".
		"description ".
	") VALUES (".
		"\$1, ".
		"\$2, ".
		"\$3, ".
		"\$4, ".
		"\$5 ".
	")");


	foreach my $pkg (keys %pseudopackages) {
		my $maintainer = $pseudopackages{$pkg}{"maintainer"}||"";
		my $description = $pseudopackages{$pkg}{"description"}||"";

		my (@addr);
		my $maintainer_name;
		my $maintainer_email;
		if ($maintainer) {
			@addr = Mail::Address->parse($maintainer);
			$maintainer_name = $addr[0]->phrase;
			$maintainer_email = $addr[0]->address;
		} else {
			$maintainer_name = '';
			$maintainer_email = '';
		}
		$insert_handle->execute(
			$pkg,
			$maintainer,
			$maintainer_name,
			$maintainer_email,
			$description
		);
	}
}

sub check_commit {
	my ($config, $source, $dbh) = @_;
	my %src_config = %{$config->{$source}};
	my $table = $src_config{table};

	# TODO no sanity checks implemented

	my $sth = $dbh->prepare("ANALYZE $table");
	$sth->execute() or die $!;

	$dbh->commit();
}

sub main {
	if(@ARGV != 3) {
		print STDERR "Usage: $0 <config> <command> <source>\n";
		exit 1;
	}

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
		run($config, $source, $dbh);
		check_commit($config, $source, $dbh);
	} else {
		print STDERR "<command> has to be one of run, drop and setup\n";
		exit(1)
	}

}

main();
