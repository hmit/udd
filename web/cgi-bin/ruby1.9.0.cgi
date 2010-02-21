#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
require 'uri'
require 'net/http'

puts "Content-type: text/plain\n\n"

pkgs = `zgrep usr/lib/ruby/1.9.0 /org/mirrors/ftp.debian.org/ftp/dists/sid/Contents-i386.gz`.split(/\n/).map do |line|
  line.chomp!
  path, pkg = line.split(/\s+/)
  sect, pkg = pkg.split('/')
  pkg
end
pkgs.uniq!

pp pkgs

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')

spkgs = pkgs.join('\',\'')
sth = dbh.prepare("select distinct source, package, version from packages
where architecture in ('i386','all') and package in ('#{spkgs}') and release='sid' and distribution='debian' and source != 'ruby1.9'")
sth.execute ; rows = sth.fetch_all
pp rows
exit(0)
