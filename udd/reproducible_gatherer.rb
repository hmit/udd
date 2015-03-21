#!/usr/bin/ruby -w
# encoding: utf-8
#
# FIXME add detection of unknown fields

$:.unshift  '/srv/udd.debian.org/udd/udd'

require 'yaml'
require 'pp'
require 'pg'
require 'deb822'
require 'json'
require 'zlib'
require 'digest'
require 'open-uri'
require 'net/https'
require 'openssl'

module Kernel
  def suppress_warnings
    original_verbosity = $VERBOSE
    $VERBOSE = nil
    result = yield
    $VERBOSE = original_verbosity
    return result
  end
end

suppress_warnings do
  OpenSSL::SSL::VERIFY_PEER = OpenSSL::SSL::VERIFY_NONE
end
URL='https://jenkins.debian.net/userContent/reproducible.json'

DEBUG = false

# PG doc: http://deveiate.org/code/pg/

class ReproducibleGatherer
  def initialize
    config = YAML::load(IO::read(ARGV[0]))
    gconf = config['general']

    @db = PG.connect({ :dbname => gconf['dbname'], :port => (gconf['dbport'] || 5432)})
    #    @db.trace(STDOUT)
#    @db.setnonblocking(true)

    @db.prepare 'users_insert', <<-EOF
    INSERT INTO reproducible(source, version, release, architecture, status) VALUES ($1, $2, $3, $4, $5)
    EOF
  end

  def run
    @db.exec("BEGIN")
    @db.exec("SET CONSTRAINTS ALL DEFERRED")

    @db.exec("DELETE FROM reproducible")
    res = JSON::parse(open(URL, 'rb').read)
    res.each { |r| @db.exec_prepared('users_insert', [r['package'], r['version'], r['suite'], r['architecture'], r['status']]) }

    @db.exec("COMMIT")
    @db.exec("ANALYSE reproducible")
  end
end


if(ARGV.length != 3)
  puts "Usage: #{$0} <config> <command> <source>"
  exit(1)
end
ReproducibleGatherer::new.run
