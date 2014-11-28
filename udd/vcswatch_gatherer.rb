#!/usr/bin/ruby -w
# encoding: utf-8
#

$:.unshift  '/srv/udd.debian.org/udd/udd'

require 'json'
require 'yaml'
require 'pp'
require 'pg'
require 'zlib'
require 'digest'

DEBUG = false

# PG doc: http://deveiate.org/code/pg/

class VcswatchGatherer
  def initialize
    config = YAML::load(IO::read(ARGV[0]))
    gconf = config['general']

    @db = PG.connect({ :dbname => gconf['dbname'], :port => (gconf['dbport'] || 5432)})
    @conf = config[ARGV[2]] 

    @db.prepare 'vcswatch_insert', <<-EOF
      INSERT INTO vcswatch
        (source, version, vcs, url, branch, browser, last_scan, next_scan, status, debian_dir, changelog_version, changelog_distribution, changelog, error) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    EOF
  end

  def run
    @db.exec("BEGIN")
    @db.exec("SET CONSTRAINTS ALL DEFERRED")
    @db.exec("DELETE FROM vcswatch")
    fd = Zlib::GzipReader::open('/srv/udd.debian.org/mirrors/qa.debian.org-vcswatch')
    s = fd.read
    s.force_encoding('utf-8')
    d = JSON::parse(s)
    fd.close
    d.each do |pkg|
      @db.exec_prepared('vcswatch_insert', ['package', 'package_version', 'vcs', 'url', 'branch', 'browser', 'last_scan', 'next_scan', 'status', 'debian_dir', 'changelog_version', 'changelog_distribution', 'changelog', 'error'].map { |e| pkg[e] } )

=begin
{"changelog"=>
  "pd-cyclone (0.1~alpha55-7) unstable; urgency=low\n\n  [ Hans-Christoph Steiner ]\n  * Bumped Standards-Version to 3.9.4\n  * Updated to copyright-format/1.0\n  * Removed 'DM-Upload-Allowed: yes', its deprecated\n\n  [ IOhannes m zmÃ¶lnig ]\n  * Fixed out-of-bound array access (Closes: #715772)\n  * Removed unneeded patches\n  * Exported CFLAGS and LDFLAGS\n    * Added patch to allow passing of extra FLAGS\n    * Enabled hardening-flags\n  * Dropped Build-Depends on \"puredata\" (keep only \"puredata-dev\")\n  * Used more CDBS features for packaging\n    * Unconditionally included cdbs/utils.mk\n    * Used cdbs/pd.mk snippet\n    * Switched to debian/control.in\n    * Added README.source to emphasize control.in file as *not* a show-stopper\n      for contributions.\n  * Added lintian-override: upstream comes without Changelog\n  * Used canonical Vcs-* stanzas\n  * Added myself to uploaders\n  * Updated debian/watch\n  * Updated debian/copyright\n  * Regenerated debian/copyright_hints\n  * Bumped Standards-Version to 3.9.5\n\n -- Felipe Sateler <fsateler@debian.org>  Fri, 21 Mar 2014 11:21:10 -0300",
 "last_scan"=>"2014-08-31 05:25:03.120777+00",
 "status"=>"OK",
 "next_scan"=>"2014-09-01 03:30:06+00",
 "browser"=>
  "http://anonscm.debian.org/gitweb/?p=pkg-multimedia/pd-cyclone.git",
 "branch"=>"master",
 "changelog_distribution"=>"unstable",
 "package"=>"pd-cyclone",
 "changelog_version"=>"0.1~alpha55-7",
 "debian_dir"=>1,
 "error"=>nil,
 "vcs"=>"Git",
 "url"=>"git://anonscm.debian.org/pkg-multimedia/pd-cyclone.git",
 "package_version"=>"0.1~alpha55-7"}
=end                                             
    end
    @db.exec("COMMIT")
  end
end


if(ARGV.length != 3)
  puts "Usage: #{$0} <config> <command> <source>"
  exit(1)
end
VcswatchGatherer::new.run
