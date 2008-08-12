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

if (@ARGV != 1) {
	print STDERR "Usage: $0 <config-file>\n";
	exit 1;
}

my $config = LoadFile($ARGV[0]) or die "Could not load configuration: $!";

my @sources = grep { !($_ eq 'general') } keys %{$config};
my $schema_dir = $config->{general}->{'schema-dir'} or die "schema-dir not specified";
my %schemata = ();

foreach my $source (@sources) {
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

