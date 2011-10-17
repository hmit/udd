#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
require 'uri'
require 'net/http'
require 'json/pure'

URELEASE='precise'

puts "Content-type: application/json\n\n"

DREL='sid'
UREL='precise'

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

sth = dbh.prepare("select ubu.component, deb.source, deb.version as dversion, ubu.version as uversion
from sources_uniq deb, ubuntu_sources ubu
where deb.distribution='debian' and deb.release='#{DREL}'
and ubu.distribution='ubuntu' and ubu.release='#{UREL}'
and deb.source = ubu.source and deb.version > ubu.version
and deb.source not in (#{sbpkgs})
and ubu.version !~ '[0-9]build[0-9]'
and ubu.version ~ 'ubuntu'
order by component, source")
sth.execute ; rows = sth.fetch_all

sth2 = dbh.prepare("select distinct package, b.bug, title, status
from ubuntu_bugs b, ubuntu_bugs_tasks bt
where b.bug = bt.bug
and title ~ '^((P|p)lease )?((M|m)erge|(S|s)ync) .* from Debian'
and status not in ('Invalid', 'Fix Released', 'Won''t Fix', 'Opinion')
and distro != 'Debian'")
sth2.execute ; rowsb = sth2.fetch_all

bugs = {}
rowsb.each do |r|
  src = r['package']
  bugs[src] = [] if bugs[src].nil?
  bugs[src] << {'bug' => r['bug'], 'status' => r['status'], 'title' => r['title']}
end

merges = {}
merges['main'] = {}
merges['restricted'] = {}
merges['universe'] = {}
merges['multiverse'] = {}

rows.each do |r|
  merges[r['component']][r['source']] = { 'debian_version' => r['dversion'], 'ubuntu_version' => r['uversion'], 'bugs' => (bugs[r['source']] or []) }
end
puts merges.to_json
sth.finish
