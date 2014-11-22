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
my $removaldelay = 15*24*3600;
my $removaldelay_rdeps = 30*24*3600;
my $debug = 0;
# set to 0 to disable autoremoval of rdeps
my $POPCON_PERCENT = 5; # x% of submissions must have the package installed

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

	if (defined $config->{general}->{debug}) {
		$debug = $config->{general}->{debug};
	}

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

	my $popcon = get_popcon($dbh);

	# if the total popcon of all rdeps is less than this value, remove them all
	my $rdeppopconlimit = get_popcon_limit($dbh);
	print "popcon limit rdeps: $rdeppopconlimit\n" if $debug;

	my $autoremoval_info = get_autoremoval_info($dbh,$table);

	do_query($dbh,"DELETE FROM ${table}") unless $debug;
	my $insert_autoremovals_handle = $dbh->prepare("INSERT INTO ${table} (
			source,
			version,
			bugs,
			first_seen,
			last_checked,
			removal_time,
			rdeps,
			rdeps_popcon,
			buggy_deps,
			bugs_deps
		) VALUES (
			\$1,
			\$2,
			\$3,
			\$4,
			\$5,
			\$6,
			\$7,
			\$8,
			\$9,
			\$10
		)");

	my $autoremovals = {};
	my $skipped = 0;
	foreach my $buggy_src (sort keys %$buggy) {
		# If it is not in testing, ignore it.
		unless ($needs->{$buggy_src}) {
			print "skip $buggy_src: not in testing" if $debug;
			next;
		}

		# all rdeps for $buggy_src, recursively
		my $my_rdeps = {};
		# rdeps added during at this level
		my $newrdeps = {};
		# start with only this package
		$newrdeps->{$buggy_src} = $buggy_src;
		my $level = 0;
		while (scalar keys %$newrdeps) {
			my $_found = {};
			foreach my $src (keys %$newrdeps) {
				unless ($my_rdeps->{$src}) {
					my $dep = $newrdeps->{$src};
					$my_rdeps->{$src}->{'level'} = $level;
					$my_rdeps->{$src}->{'dep'} = $dep;
					my $depchain = "";
					if ($src ne $dep) {
						$depchain = $my_rdeps->{$dep}->{'dep_chain'};
						$depchain = " ".$depchain if $depchain;
						$depchain = $dep.$depchain;
					}
					$my_rdeps->{$src}->{'dep_chain'} = $depchain;
					foreach my $rrdep (keys %{$rdeps->{$src}}) {
						unless ($my_rdeps->{$rrdep}) {
							$_found->{$rrdep} = $src;
						}
					}
				}
			}
			$newrdeps = $_found;
			$level++;
		}
		my $nonbuggy_rdeps;
		foreach my $src (keys %$my_rdeps) {
			if ($buggy->{$src}) {
				#print "skip buggy rdep $src of $buggy_src\n" if $debug;
				next;
			}
			$nonbuggy_rdeps->{$src} = $popcon->{$src};
		}

		my $rdepcount = (scalar keys %$my_rdeps);
		my $nbrdepcount = (scalar keys %$nonbuggy_rdeps);
		if ($nbrdepcount) {
			my $totalpopcon = 0;
			foreach my $nb ( keys %$nonbuggy_rdeps) {
				$totalpopcon += $nonbuggy_rdeps->{$nb}||0;
			}
			if ($totalpopcon < $rdeppopconlimit)  {
				foreach my $rdep (keys %$my_rdeps) {
					if ($rdep ne $buggy_src) {
						$autoremovals->{$buggy_src}->{"rdep"}->{$rdep} = 1;
						$autoremovals->{$rdep}->{"dep"}->{$buggy_src} = $buggy->{$buggy_src};
						foreach my $bugid (keys %{$buggy->{$buggy_src}}) {
							$autoremovals->{$rdep}->{"bugs_deps"}->{$bugid} =
								$buggy->{$buggy_src}->{$bugid};
						}
					}
				}
				if ($debug) {
					print "$buggy_src (".$popcon->{$buggy_src}."):  total popcon of non-buggy rdeps: $totalpopcon\n";
					print Dumper $my_rdeps;
					print "\n";
				}
				$autoremovals->{$buggy_src}->{"rdeps_popcon"} = $totalpopcon||0;
			} else {
				print "$buggy_src (".$popcon->{$buggy_src}."): skipped, total popcon of non-buggy rdeps: $totalpopcon\n\n" if $debug;
				print Dumper $my_rdeps;
				$skipped++;
				next;
			}
		}
		$autoremovals->{$buggy_src}->{"bugs"} = $buggy->{$buggy_src};
	}

	foreach my $buggy_src (sort keys %$autoremovals) {
		my @bugschecked = ();
		my @bugsmodified = ();
		foreach my $_bugdata (values %{ $buggy->{$buggy_src}}, values %{$autoremovals->{$buggy_src}->{"bugs_deps"}}) {
			push @bugschecked, $_bugdata->{"last_check"};
			push @bugsmodified, $_bugdata->{"last_modified"};
		}
		my $checked = min(@bugschecked);
		my $modified = min(@bugsmodified);
		my $first_seen = $autoremoval_info->{$buggy_src}->{"first_seen"};
		$first_seen = $now unless $first_seen;
		# TODO can there be more than 1 version?
		my $version =  join (' ', keys %{ $needs->{$buggy_src}->{'_version'}});
		my $buginfo = "";
		my $bugcount = 0;
		if (defined $buggy->{$buggy_src}) {
			$buginfo = join (',', keys %{ $buggy->{$buggy_src} });
			$bugcount = scalar keys %{ $buggy->{$buggy_src} };
		}
		if ($debug) {
			print Dumper $autoremovals->{$buggy_src};
		}

		my $rdeps = join(",",sort keys %{$autoremovals->{$buggy_src}->{"rdep"}});
		my $rdeps_popcon = $autoremovals->{$buggy_src}->{"rdeps_popcon"}||0;
		my $buggy_deps = join(",",sort keys %{$autoremovals->{$buggy_src}->{"dep"}});
		my $bugs_deps = join(",",sort keys %{$autoremovals->{$buggy_src}->{"bugs_deps"}});

		my $delay = $removaldelay;
		# use longer delay for packages with rdeps
		$delay = $removaldelay_rdeps if scalar keys %{$autoremovals->{$buggy_src}->{"rdep"}};
		# use longer delay for packages with don't have bugs themselves (these
		# are only listed because of buggy deps)
		$delay = $removaldelay_rdeps unless $bugcount;
		my $removal_time = $autoremoval_info->{$buggy_src}->{"removal_time"}||0;
		$removal_time = $first_seen + $delay unless ($removal_time > $first_seen + $delay);
		$removal_time = $modified + $delay unless ($removal_time > $modified + $delay);

		if ($debug) {
			print "Package: $buggy_src\n";
			print "Version: $version\n";
			print "Removal at: ".localtime($removal_time)."\n";
			print "Popcon: ".($popcon->{$buggy_src}||0)."\n";
			print "Bugs: $buginfo\n";
			print "rdeps: $rdeps\n";
			print "rdeps_popcon: $rdeps_popcon\n";
			print "buggy_deps: $buggy_deps\n";
			print "bugs_deps: $bugs_deps\n";
			print "\n";
		} else {
			$insert_autoremovals_handle->execute(
				$buggy_src,
				$version,
				$buginfo,
				$first_seen,
				$checked,
				$removal_time,
				$rdeps,
				$rdeps_popcon,
				$buggy_deps,
				$bugs_deps
			);
		}
	}
	do_query($dbh,"ANALYZE ".$table) unless $debug;
	$dbh->commit();
	print "total: ".(scalar keys $autoremovals)." autoremovals, $skipped skipped for rdeps\n" if $debug;
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
            # skip build-deps for now, because britney ignores them
            next if $el eq '_BD';
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
				if (my $prov = $providers->{'_main'}) {
					# when the package exists, only use that, not the packages
					# that provide it
					if ($prov ne $src) {
						$rdeps->{$prov}->{$src} = 1;
					}
					next;
				}
                foreach my $prov (keys %$providers) {
                    next if $prov eq '_main'; # fake entry
                    next if $src eq $prov;    # self depends does not count
                    #print STDERR "N: $src deps on $prov (via $el)\n";
                    $rdeps->{$prov}->{$src} = 1;
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

SELECT  b.source,
        b.id,
        b.affects_unstable,
        EXTRACT(epoch FROM b.arrival) AS arrival,
        EXTRACT(epoch FROM b.last_modified) AS last_modified,
        min(s.db_updated) AS last_check,
        b4.bugs_unstable,
        b5.id AS unblock_request,
        count(ub.source) as unblock_hints
FROM    bugs_stamps s,
        bugs b
        LEFT JOIN
        -- RC bugs in unstable (caused by OTHER rc bugs)
        ( 
            SELECT b3.source, array_agg(b3.id) AS bugs_unstable
            FROM bugs b3
            WHERE b3.severity >= 'serious'
                AND b3.affects_unstable = true
                AND b3.affects_testing = false
            GROUP BY b3.source
        ) b4
        ON b.source = b4.source
        LEFT JOIN
        -- unblock requests
        (
             SELECT array_to_string(regexp_matches(title,'unblock: ([^ /]*)/'),'') AS source,
             id FROM bugs b2
             WHERE b2.source = 'release.debian.org'
                 AND b2.done != 'done'
                 -- Find (?:pre-approve )?unblock: <src>/.*
                 AND b2.title LIKE ('%unblock: %/%')
        ) b5
        ON b.source = b5.source
        LEFT JOIN
        -- unblock hints
        (
            SELECT * FROM hints
            WHERE type = 'unblock'
        ) ub
        ON b.source = ub.source
WHERE   b.severity >= 'serious'
        AND b.affects_testing = true
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
                        t.tag = '$testing-ignore'
            )
        AND b.id NOT IN ( -- Not <release>-{is-blocker,will-remove...} ...
                 SELECT ut.id FROM bugs_usertags ut
                 WHERE ut.email = 'release.debian.org\@packages.debian.org'
                     AND ut.id = b.id AND
                         (   ut.tag = '$testing-can-defer'
                          OR ut.tag = '$testing-is-blocker'
                          OR ut.tag = '$testing-no-auto-remove'
                         )
            )
        AND b.arrival < CURRENT_TIMESTAMP - INTERVAL '14 days'
        AND b.id = s.id
GROUP BY
        b.source,
        b.id,
        b4.source,
        b4.bugs_unstable,
        b5.source,
        b5.id

";

    my $sthc = do_query($dbh,$query);
    while (my $pg = $sthc->fetchrow_hashref()) {
        my $pkgsource = $pg->{'source'};
        my $bug = $pg->{'id'};

        foreach my $pkg (split m/\s*,\s*/, $pkgsource) {
			$buggy->{$pkg}->{$bug} = $pg;

			if ($buggy->{$pkg}->{$bug}->{"last_modified"} <
				$buggy->{$pkg}->{$bug}->{"arrival"} + 14*24*3600) {
				# we only start counting from 14 days after the bug was filed
				$buggy->{$pkg}->{$bug}->{"last_modified"} =
					$buggy->{$pkg}->{$bug}->{"arrival"} + 14*24*3600;
			}

			# during the freeze, we only whitelist bugs fixed in unstable if
			# there is an unblock request or an unblock hint
			if (!$pg->{"affects_unstable"} && (
					$pg->{"unblock_request"} ||
					$pg->{"unblock_hints"}
				)) {
				unless ($pg->{"bugs_unstable"}) {
					# if the bug is fixed in unstable, but not (yet) in
					# testing and there are no other bugs affecting the
					# package in unstable, we reset the counter on every run,
					# so the package doesn't get autoremoved, but it stays on
					# the list
					# if the package has other bugs in unstable (which prevent
					# migration of the fix to testing), the counter is NOT
					# reset, and the package can still be autoremoved
					$buggy->{$pkg}->{$bug}->{"last_modified"} = $now;
					print "reset counter for $pkg\n" if $debug;
				}
			}
        }
    }

    return $buggy;
}

sub get_popcon {
    my ($dbh) = @_;

	my $popcon = {};
	my $query = "select source, insts from popcon_src;";
	my $sthc = do_query($dbh,$query);
	while (my $pg = $sthc->fetchrow_hashref()) {
		my $src = $pg->{'source'};
		my $insts = $pg->{'insts'};
		$popcon->{$src} = $insts;
	}
	return $popcon;
}

sub get_popcon_limit {
    my ($dbh) = @_;

	my $sthc = do_query($dbh,"select max(insts) from popcon");
	my $pg = $sthc->fetchrow_hashref();
	my $popcon_max = $pg->{"max"};
	my $minpopcon = int($popcon_max * $POPCON_PERCENT/100);

	return $minpopcon;
}

sub get_autoremoval_info {
    my ($dbh,$table) = @_;

	my $autoremoval_info = {};
	my $query = "select source, min(first_seen) as first_seen, min(removal_time) as removal_time from ${table} group by source;";
	my $sthc = do_query($dbh,$query);
	while (my $pg = $sthc->fetchrow_hashref()) {
		my $src = $pg->{'source'};
		my $info = {};
		$info->{"first_seen"} = $pg->{'first_seen'};
		$info->{"removal_time"} = $pg->{'removal_time'};
		$autoremoval_info->{$src} = $info;
	}
	return $autoremoval_info;
}

sub read_source_depends {
    my ($dbh,$needs) = @_;

	my $query = "select source, version, build_depends, build_depends_indep from sources ".
		" where release = '$testing' and extra_source_only is null;";
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

