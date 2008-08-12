#!/usr/bin/perl -w

use strict;
use warnings;

use YAML::Syck;

$YAML::Syck::ImplicitTyping = 1;

sub pyformat {
	my ($string, %dict) = @_;
	$string =~ s/%\(([^)]+)\)s/$dict{$1}/g;
	return $string;
}

if (@ARGV == 0) {
	print STDERR "Usage: $0 <config-file> [source 1 [source 2 ...]]\n";
	exit 1;
}

my $config = LoadFile($ARGV[0]) or die "Could not load configuration: $!";

my @sources = ();
if (@ARGV == 1) {
	@sources = grep { !($_ eq 'general') } keys %{$config};
} else {
	@sources = @ARGV[1, $#ARGV];
}

my $schema_dir = $config->{general}->{'schema-dir'} or die "schema-dir not specified";
my %schemata = ();

foreach my $source (@sources) {
	if(not exists $config->{$source}) {
		print STDERR "No such source: $source\n";
		exit 1;
	}
	my %src_config = %{$config->{$source}};
	foreach my $schema_tag (qw{schema packages-schema sources-schema}) {
		if(not exists $src_config{$schema_tag}) {
			next;
		}
		my $schema = "$schema_dir/$src_config{$schema_tag}";

		open SCHEMA, $schema or die "Couldn't read $schema: $!";
		$schemata{pyformat((join "", <SCHEMA>), %src_config)} = 1;
		close SCHEMA;
	}
}

print join "\n\n", keys %schemata;
print "\n";

