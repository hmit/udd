#!/usr/bin/ruby -w

# See #647258

require 'dbi'
require 'pp'
require 'cgi'
require 'time'
require 'yaml'
require 'json'
require 'net/http'
puts "Content-type: text/yaml\n\n"

rgs = Net::HTTP::get(URI("http://release.debian.org/testing/goals.yaml"))
rgs = YAML::load(rgs)
rgs = rgs['release-goals']
# only rgs that are not rejected or proposed
rgs = rgs.select { |rg| rg['state'] != 'rejected' }
rgs = rgs.select { |rg| rg['state'] != 'proposed' }
# only rgs that have associated usertags
rgs = rgs.select { |rg| rg['bugs'] != nil }
usertags = []
rgs.each do |rg|
  rg['bugs']['usertags'].each do |ut|
    usertags << [ rg['bugs']['user'], ut ]
  end
end
ut_text = usertags.map { |e| "('#{e[0]}', '#{e[1]}')"}.join(',')
dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
dbh.execute("SET statement_timeout TO 90000")
q = "select distinct bugs.id, bugs.source, bugs.package, bu.email, bu.tag from bugs, bugs_usertags bu where bugs.id = bu.id and status = 'pending' and (bu.email, bu.tag) in (#{ut_text})"
sth = dbh.prepare(q)
sth.execute
rows = sth.fetch_all
rows = rows.map { |r| r.to_h }
puts YAML::dump(rows)
