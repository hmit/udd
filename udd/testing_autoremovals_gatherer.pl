#!/usr/bin/perl
#
# based on rt-find-rc-buggy-leaf-packages
# Copyright 2011 Niels Thykier <niels@thykier.net>
# Copyright 2013 Ivo De Decker
# License: GPL-2 (or at your option any later)
#

use DBI;
use Data::Dumper;
$Data::Dumper::Sortkeys=1;
use YAML::Syck;
use List::Util qw(min max);

my $testing = "jessie";
my $debug = 0;
my $now = time;
print "start: ".$now."\n" if ($debug);

use strict;
use warnings;

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
	my $dbconnect ="dbi:Pg:dbname=$dbname";
	if ($config->{general}->{dbport} ne '') {
	  $dbconnect .= ";port=".$config->{general}->{dbport};
	}
	if (defined $config->{general}->{dbuser}) {
	  $dbconnect .= ";host=localhost;user=".$config->{general}->{dbuser};
	}
	# Connection to DB
	my $dbh = DBI->connect($dbconnect);
	# We want to commit the transaction as a hole at the end
	$dbh->{AutoCommit} = 0;
	$dbh->do('SET CONSTRAINTS ALL DEFERRED');

	if($command eq 'run') {
		update_autoremovals($config,$source,$dbh)
		#check_commit($config, $source, $dbh);
	} else {
		print STDERR "<command> has to be one of run, drop and setup\n";
		exit(1)
	}

}

main();
print "end: ".(time-$now)."\n" if ($debug);
exit 0;


sub update_autoremovals {
	my $config = shift;
	my $source = shift;
	my $dbh = shift;

	my %src_config = %{$config->{$source}};
	my $table = $src_config{table};

	# $needs->{src}->{bin}->{$dep} = 1
	# $needs->{src}->{_BD}->{$dep} = 1
	# $needs->{src}->{_verison}->{$version} = 1
	my $needs = {};
	# $buggy->{src}->{bug1} = last_checked_bug1
	# $buggy->{src}->{bug2} = last_checked_bug2
	my $buggy;

	# $rdep->{srcX} > 0 (if something depends on something from srcX)
	my $rdeps;

	# $bin2src->{bin}->{_main} = $src
	# - _main is the "main" provider of $src (if any)
	# $bin2src->{bin}->{src} = 1
	# - bin may map to multiple sources (hi Provides)
	my $bin2src = {};

	read_source_depends($dbh,$needs);
	read_package_data($dbh,$needs,$bin2src);

	$rdeps = _calculate_rdeps ($needs, $bin2src);

	$buggy = get_bugs ($dbh, $bin2src);

	my $first_seen = get_first_seen($dbh,$table);

	do_query($dbh,"DELETE FROM ${table}") unless $debug;
	my $insert_autoremovals_handle = $dbh->prepare("INSERT INTO ${table} (source, version, bugs, first_seen, last_checked) VALUES (\$1, \$2, \$3, \$4, \$5)");

	foreach my $buggy_src (sort keys %$buggy) {
		# If it is not in testing, ignore it.
		next unless $needs->{$buggy_src};
		next if $rdeps->{$buggy_src};
		# TODO can there be more than 1 version?
		my $version =  join (' ', keys %{ $needs->{$buggy_src}->{'_version'}});
		my $bugs = join (',', keys %{ $buggy->{$buggy_src} });
		my $updated = min(values %{ $buggy->{$buggy_src}});
		my $first_seen = $first_seen->{$buggy_src};
		$first_seen = $now unless $first_seen;
		if ($debug) {
			print "Package: $buggy_src\n";
			print "Version: $version\n";
			print "Bugs: $bugs\n";
			print "\n";
		} else {
			$insert_autoremovals_handle->execute($buggy_src,$version,$bugs,$first_seen,$updated);
		}
	}
	do_query($dbh,"ANALYZE ".$table) unless $debug;
	$dbh->commit();
}

sub do_query {
	my $handle = shift;
	my $query = shift;

	print ((time-$now)." $query\n") if $debug;
	my $sthc = $handle->prepare($query);
	$sthc->execute();
	return $sthc;
}

sub _calculate_rdeps {
    my ($needs, $bin2src) = @_;
    my $rdeps = {};
    my %once = ();

    foreach my $src (keys %$needs) {
        foreach my $el (keys %{$needs->{$src}}) {
            next if $el eq '_version';
            foreach my $dep (keys %{$needs->{$src}->{$el}}) {
                my $providers = $bin2src->{$dep};
                #print STDERR "N: $src ($el) -> $prov_src ($dep)\n" if $prov_src;
                unless ($providers) {
                    if ($debug) {
                        #print STDERR "warning: cannot determine the provider of $dep ($src via $el)\n"
                        #    unless $once{$dep}++;
                    }
                    next;
                }
                foreach my $prov (keys %$providers) {
                    next if $prov eq '_main'; # fake entry
                    next if $src eq $prov;    # self depends does not count
                    #print STDERR "N: $src deps on $prov (via $el)\n";
                    $rdeps->{$prov}++;
                }
            }
        }
    }

    return $rdeps;
}

sub get_bugs {
    my ($dbh, $bin2src) = @_;
    my $buggy = {};
    my $fd;

	my $query = "
--
-- Copyright (c) 2011 Alexander Reichle-Schmehl <tolimar\@debian.org>
-- Copyright (c) 2012 Niels Thykier <niels\@thykier.net>
-- 
-- Permission is hereby granted, free of charge, to any person obtaining a
-- copy of this software and associated documentation files (the
-- 'Software'),
-- to deal in the Software without restriction, including without limitation
-- the rights to use, copy, modify, merge, publish, distribute, sublicense,
-- and/or sell copies of the Software, and to permit persons to whom the
-- Software is furnished to do so, subject to the following conditions:
-- 
-- The above copyright notice and this permission notice shall be included
-- in
-- all copies or substantial portions of the Software.
-- 
-- THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS
-- OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
-- FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
-- THE
-- AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
-- FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
-- DEALINGS IN THE SOFTWARE.
--

SELECT	b.source, b.id, min(s.db_updated) as db_updated
FROM	bugs b, bugs_stamps s 
WHERE	b.severity >= 'serious'
        AND b.affects_testing = true AND b.affects_unstable = true
        AND b.source IN ( -- in testing
                 SELECT s.source FROM sources s WHERE
                    release = '$testing' AND
                    extra_source_only is null
            )
        AND b.source NOT IN ( -- Not in key packages
                 SELECT kp.source FROM key_packages kp
            )
        AND b.id NOT IN ( -- Not <release>-ignore
                 SELECT t.id FROM bugs_tags t WHERE t.id = b.id AND
                        t.tag = 'jessie-ignore'
            )
        AND b.id NOT IN ( -- Not <release>-{is-blocker,will-remove...} ...
                 SELECT ut.id FROM bugs_usertags ut
                 WHERE ut.email = 'release.debian.org\@packages.debian.org'
                     AND ut.id = b.id AND
                         (   ut.tag = 'jessie-can-defer'
                          OR ut.tag = 'jessie-is-blocker'
                          OR ut.tag = 'jessie-no-auto-remove'
                         )
            )
        AND 0 = ( -- No open unblock bugs 
                 SELECT COUNT(1) FROM bugs b2
                 WHERE b2.source = 'release.debian.org'
                     AND b2.done != 'done'
                     -- Find (?:pre-approve )?unblock: <src>/.*
                     AND b2.title LIKE ('%unblock: ' || b.source || '/%')
                 LIMIT 1
            )
        AND b.id NOT IN ( -- Bug not fixed in new
                 SELECT pbc.id FROM potential_bug_closures pbc
                 WHERE origin = 'ftpnew'
            )
        -- shoud be only 5 days, because there is a 10 day waiting period afterward
        AND b.last_modified < CURRENT_TIMESTAMP - INTERVAL '14 days'
        AND b.id = s.id
GROUP BY b.source, b.id

";

    my $sthc = do_query($dbh,$query);
    while (my $pg = $sthc->fetchrow_hashref()) {
        my $pkgsource = $pg->{'source'};
        my $bug = $pg->{'id'};

        foreach my $pkg (split m/\s*,\s*/, $pkgsource) {
			$buggy->{$pkg}->{$bug} = $pg->{"db_updated"};
        }
    }

    return $buggy;
}

sub get_first_seen {
    my ($dbh,$table) = @_;

	my $first_seen = {};
	my $query = "select source, min(first_seen) as first_seen from ${table} group by source;";
	my $sthc = do_query($dbh,$query);
	while (my $pg = $sthc->fetchrow_hashref()) {
		my $src = $pg->{'source'};
		my $seen = $pg->{'first_seen'};
		$first_seen->{$src} = $seen;
	}
	return $first_seen;
}

sub read_source_depends {
    my ($dbh,$needs) = @_;

	my $query = "select source, version, build_depends, build_depends_indep from sources where release = '$testing';";
	my $sthc = do_query($dbh,$query);
	while (my $pg = $sthc->fetchrow_hashref()) {
		my $src = $pg->{'source'};
		my $version = $pg->{'version'};

		my $depstr = '';
		die "Sources has paragraph without Source and Version field\n"
			unless defined $src && defined $version;
		foreach my $f (qw(build_depends build_depends_indep)) {
			my $val = $pg->{$f};
			next unless $val;
			$depstr .= ', ' if $depstr;
			$depstr .= $val;
		}
		foreach my $dep (_split_dep ($depstr)) {
			$needs->{$src}->{'_BD'}->{$dep} = 1;
		}
		$needs->{$src}->{'_version'}->{$version} = 1;
	}
}

sub read_package_data {
    my ($dbh,$needs, $bin2src) = @_;

	my $query = "select source, package, version, source_version, depends, pre_depends, provides from packages where release = '$testing';";
	my $sthc = do_query($dbh,$query);
	while (my $pg = $sthc->fetchrow_hashref()) {

		my $src = $pg->{'source'};
		my $src_version;
		my $pkg = $pg->{'package'};
		my $depstr = '';

		if ($src) {
			# strip src version (if any)
			if ($src =~ s/\s*\((.*)\)$//) {
				$src_version = $1;
			}
		} else {
			$src = $pkg;
		}
		$src_version = $pg->{'source_version'} unless defined $src_version;

		die "Packages_X has paragraph without Package or Version field\n"
			unless $pkg && defined $src_version;

		unless ($needs->{$src}->{'_version'}->{$src_version}) {
			#print "$src $src_version not found\n" if $debug;
			next;
		}

		$bin2src->{$pkg}->{'_main'} = $src;
		$bin2src->{$pkg}->{$src} = 1;
		if ($pg->{'provides'}) {
			my $prov = $pg->{'provides'};
			$prov =~ s/^\s*+//o;
			$prov =~ s/\s*+$//o;
			foreach my $p (split m/\s*+,\s*+/o, $prov) {
				$bin2src->{$p}->{$src} = 1;
				#print STDERR "N: $src (via $pkg) provides $p\n";
			}
		}

		foreach my $f (qw(pre_depends depends)) {
			my $val = $pg->{$f};
			next unless $val;
			$depstr .= ', ' if $depstr;
			$depstr .= $val;
		}

		foreach my $dep (_split_dep ($depstr)) {
			$needs->{$src}->{$pkg}->{$dep} = 1;
			#print STDERR "N: $src depends on $dep (via $pkg)\n";
		}
	}
}

sub _split_dep {
    my ($dep) = @_;
    # Remove version and architecture
    $dep =~ s/\[[^\]]*\]//og;
    $dep =~ s/\([^\)]*\)//og;
    $dep =~ s/^\s*+//o;
    $dep =~ s/\s*+$//o;
    my @deps = split m/\s*+[,]\s*+/o, $dep;
	my @deps_first = ();
	foreach my $dep (@deps) {
    	my ($dep1, undef) = split m/\s*+[,|]\s*+/o, $dep;
		push @deps_first, $dep1;
	}
    return @deps_first;
}

