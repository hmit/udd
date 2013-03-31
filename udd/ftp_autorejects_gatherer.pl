#!/usr/bin/perl -w

use strict;
use warnings;

use DBI;
use DBI qw{:sql_types};
use YAML::Syck;

$YAML::Syck::ImplicitTyping = 1;

sub run {
	my ($config, $source, $dbh) = @_;

	my %src_config = %{$config->{$source}};
	my $table = $src_config{table};

	my $data = LoadFile($src_config{path}) or die "Could not load data: $!";

	$dbh->do("DELETE FROM ${table}") or die;
	my $insert_handle = $dbh->prepare("INSERT INTO $table ( ".
		"tag, ".
		"autoreject_type, ".
		"autoreject_level ".
	") VALUES (".
		"\$1, ".
		"\$2, ".
		"\$3 ".
	")");

	foreach my $type (keys %$data) {
		foreach my $level (keys %{$data->{$type}}) {
			foreach my $tag (@{$data->{$type}->{$level}}) {
				$insert_handle->execute($tag,$type,$level);
			}
		}
	}
}

sub check_commit {
	my ($config, $source, $dbh) = @_;
	my %src_config = %{$config->{$source}};
	my $table = $src_config{table};

	# TODO no sanity checks implemented for ftp-autorejects

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
