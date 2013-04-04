#!/usr/bin/ruby

require 'dbi'
require 'pp'
require 'uri'
require 'net/http'
require 'yaml'

URELEASE=YAML::load(IO::read('../ubuntu-releases.yaml'))['devel']

puts "Content-type: text/html\n\n"

puts <<-EOF
<html>
<head>
<style type="text/css">
  td, th {
    border: 1px solid gray;
    padding-left: 3px;
    padding-right: 3px;
  }
  tr:hover  {
    background-color: #ccc;
  }
  table {
    border-collapse: collapse;
  }
</style>
<title>Ubuntu: outstanding merges</title>
</head>
<body>
<h1>Outstanding merges</h1>
EOF

DREL='sid'
UREL=URELEASE
puts "Debian release: #{DREL}<br>"
puts "Ubuntu release: #{UREL}<br>"
puts "Bugs data refreshed once a day. Packages data refreshed twice a day.<br>"
puts "<a href=\"http://svn.debian.org/wsvn/collab-qa/udd/web/cgi-bin/merges.cgi\">Source code</a>"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

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
  bugs[src] << [r['bug'], r['status']]
end

puts "<table>"
puts "<tr><th>Component</th><th>Source</th><th>Debian</th><th>Ubuntu</th><th>Bugs</th></tr>"
rows.each do |r|
   puts "<tr>"
   puts "<td>#{r['component']}</td>"
   puts "<td>#{r['source']} "
   puts "<a href=\"https://launchpad.net/ubuntu/+source/#{r['source']}\">LP</a> "
   puts "<a href=\"http://packages.qa.debian.org/#{r['source']}\">PTS</a> "
   puts "<a href=\"http://bugs.debian.org/src:#{r['source']}\">BTS</a> "
   puts "</td>"
   puts "<td>#{r['dversion']}</td>"
   puts "<td>#{r['uversion']}</td>"
   puts "<td>"
   if bugs[r['source']] != nil
      puts bugs[r['source']].map { |b| "<a href=\"https://launchpad.net/bugs/#{b[0]}\">#{b[0]}</a> (#{b[1]})" }.join('<br>')
   end
   puts "</tr>"
end
puts "</table>"
puts "#{rows.length} packages listed<br>"
['main', 'restricted', 'universe', 'multiverse'].each do |comp|
   n = rows.select { |r| r['component'] == comp }.length
   puts "#{comp}: #{n}<br>"
end
puts "#{bpkgs.length} packages in the <a href=\"http://people.canonical.com/~ubuntu-archive/sync-blacklist.txt\">blacklist</a>"
sth.finish
puts "</body></html>"
