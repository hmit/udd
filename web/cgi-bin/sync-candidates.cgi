#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
require 'uri'
require 'net/http'
require 'json/pure'

URELEASE='oneiric'

puts "Content-type: application/json\n\n"

DREL='sid'
UREL='oneiric'

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')

# Fetching blacklist
blacklist = Net::HTTP.get(URI::parse('http://people.canonical.com/~ubuntu-archive/sync-blacklist.txt')).split(/\n/)
bpkgs = []
blacklist.each do |l|
   l.gsub!(/#.*/, '')
   l.strip!
   next if l == ''
   bpkgs << l
end
sbpkgs = "'" + bpkgs.uniq.join("','") + "'"

# Fetching binary packages
sth2 = dbh.prepare("select distinct source, package, depends, recommends from packages where distribution='debian' and release='#{DREL}' and architecture in ('i386','all')")
sources = {}
sth2.execute
sth2.fetch_all.each do |r|
  sources[r['source']] ||= []
  h = r.to_h
  h.delete('source')
  sources[r['source']] << h
end

# Fetching sync req
sth3 = dbh.prepare("select * from ubuntu_bugs, ubuntu_bugs_tasks where ubuntu_bugs.bug = ubuntu_bugs_tasks.bug and title ~* 'sync.*from.*debian'")
sth3.execute
syncs = {}
sth3.fetch_all.each do |r|
  next if r['status'] == 'Invalid' or r['status'] == 'Incomplete'
  syncs[r['package']] = { 'bug'=>r['bug'], 'title' => r['title'], 'status' => r['status'], 'date' => r['date_created'] }
end

sth = dbh.prepare("select ubu.component, deb.source, deb.version as dversion, ubu.version as uversion, deb.maintainer, deb.uploaders, deb.build_depends
from sources_uniq deb, ubuntu_sources ubu
where deb.distribution='debian' and deb.release='#{DREL}'
and ubu.distribution='ubuntu' and ubu.release='#{UREL}'
and deb.source = ubu.source and deb.version > ubu.version
and deb.source not in (#{sbpkgs})
order by component, source")
sth.execute ; rows = sth.fetch_all

merges = []
rows.each do |r|
  h = r.to_h
  h['binaries'] = sources[h['source']]
  h['sync'] = syncs[h['source']]
  merges << h
end
puts merges.to_json
sth.finish
