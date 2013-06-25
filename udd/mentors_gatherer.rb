#!/usr/bin/ruby -w
# encoding: utf-8
#
# FIXME add detection of unknown fields

$:.unshift  '/srv/udd.debian.org/udd/udd'

require 'yaml'
require 'pp'
require 'pg'
require 'deb822'
require 'zlib'
require 'digest'

DODESC=false

DEBUG = false
TESTMODE = false
VCS = [ 'Svn', 'Git', 'Arch', 'Bzr', 'Cvs', 'Darcs', 'Hg', 'Mtn']

# PG doc: http://deveiate.org/code/pg/

class MentorsGatherer
  def initialize
    config = YAML::load(IO::read(ARGV[0]))
    gconf = config['general']

    @db = PG.connect({ :dbname => gconf['dbname'], :port => (gconf['dbport'] || 5432)})
#    @db.trace(STDOUT)
#    @db.setnonblocking(true)
    @mdb = PG.connect({ :host => 'mentors.debian.net', :dbname => 'debexpo_live', :user => 'udd', :password => 'UInyXCjdKL9JY', :port => 5432})

    @db.prepare 'users_insert', <<-EOF
    INSERT INTO mentors_users (id, name, email, gpg_id) VALUES ($1, $2, $3, $4)
    EOF

    @db.prepare 'packages_insert', <<-EOF
    INSERT INTO mentors_packages (id, name, user_id, description, needs_sponsor) VALUES ($1, $2, $3, $4, $5)
    EOF

    @db.prepare 'package_versions_insert', <<-EOF
    INSERT INTO mentors_package_versions (id, package_id, version, maintainer, section, distribution, component, priority, uploaded, closes) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    EOF

    @db.prepare 'package_info_insert', <<-EOF
    INSERT INTO mentors_package_info (id, package_version_id, from_plugin, outcome, data, severity) VALUES ($1, $2, $3, $4, $5, $6)
    EOF
  end

  def run
    @db.exec("BEGIN")
    @db.exec("SET CONSTRAINTS ALL DEFERRED")

    @db.exec("DELETE FROM mentors_users")
    res = @mdb.exec("SELECT id, name, email, gpg_id from users_filtered").values
    res.each { |r| @db.exec_prepared('users_insert', r) }

    @db.exec("DELETE FROM mentors_packages")
    res = @mdb.exec("SELECT id, name, user_id, description, needs_sponsor from packages").values
    res.each { |r| @db.exec_prepared('packages_insert', r) }

    @db.exec("DELETE FROM mentors_package_versions")
    res = @mdb.exec("SELECT id, package_id, version, maintainer, section, distribution, component, priority, uploaded, closes from package_versions").values
    res.each { |r| @db.exec_prepared('package_versions_insert', r) }

    @db.exec("DELETE FROM mentors_package_info")
    res = @mdb.exec("SELECT id, package_version_id, from_plugin, outcome, data, severity from package_info").values
    res.each { |r| @db.exec_prepared('package_info_insert', r) }

    @db.exec("COMMIT")
    @db.exec("ANALYSE mentors_users")
    @db.exec("ANALYSE mentors_packages")
    @db.exec("ANALYSE mentors_package_versions")
    @db.exec("ANALYSE mentors_package_info")
  end
end


if(ARGV.length != 3)
  puts "Usage: #{$0} <config> <command> <source>"
  exit(1)
end
MentorsGatherer::new.run
