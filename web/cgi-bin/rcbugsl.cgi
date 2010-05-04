#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
require 'net/http'

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
<title>Possibly easy targets for RC bug squashing</title>
</head>
<body>
<h1>Possibly easy targets for RC bug squashing</h1>
EOF

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')

pkgs = Net::HTTP.get(URI::parse('http://blop.info/pub/pkgs')).split(/\n/)
pkgss= pkgs.join("','")
sth = dbh.prepare("select source from packages where package in ('#{pkgss}')")
sth.execute ; rows = sth.fetch_all
spkgs = []
rows.each do |r|
  spkgs << r['source']
end
spkgss = spkgs.uniq.join("','")

# all RC

sth = dbh.prepare("select id, bugs.package, bugs.source, insts, title from bugs, popcon_src where bugs.source = popcon_src.source and id in (select id from bugs_rt_affects_testing_and_unstable) and severity >= 'serious' and bugs.source in ('#{spkgss}') order by id")
sth.execute ; rows = sth.fetch_all

puts "<h2>All RC bugs</h2>"
puts "<table>"
puts "<tr><th>bug</th><th>package</th><th>source</th><th>popcon</th><th>title</th></tr>"
rows.each do |r|
   puts "<tr><td><a href=\"http://bugs.debian.org/#{r['id']}\">#{r['id']}</a></td>"
   puts "<td>#{r['package']}</td>"
   puts "<td><a href=\"http://packages.qa.debian.org/#{r['source']}\">#{r['source']}</a></td>"
   puts "<td>#{r['insts']}</td>"
   puts "<td>#{r['title']}</td>"
end
puts "</table>"
sth.finish


sth = dbh.prepare("select id, bugs.package, bugs.source, insts, title from bugs, popcon_src where bugs.source = popcon_src.source and id in (select id from bugs_rt_affects_testing_and_unstable) and id in (select id from bugs_tags where tag='patch') and severity >= 'serious' and bugs.source in ('#{spkgss}') order by id")
sth.execute ; rows = sth.fetch_all

puts "<h2>RC bugs tagged patch</h2>"
puts "<table>"
puts "<tr><th>bug</th><th>package</th><th>source</th><th>popcon</th><th>title</th></tr>"
rows.each do |r|
   puts "<tr><td><a href=\"http://bugs.debian.org/#{r['id']}\">#{r['id']}</a></td>"
   puts "<td>#{r['package']}</td>"
   puts "<td><a href=\"http://packages.qa.debian.org/#{r['source']}\">#{r['source']}</a></td>"
   puts "<td>#{r['insts']}</td>"
   puts "<td>#{r['title']}</td>"
end
puts "</table>"
sth.finish

puts "<h2>RC bugs on packages with a newer version in Ubuntu, not tagged patch (possible patches)</h2>"
puts "<table>"
puts "<tr><th>bug</th><th>package</th><th>source</th><th>versions (D/U)</th><th>popcon</th><th>title</th></tr>"

sth = dbh.prepare("WITH ubudeb AS (select distinct on (d.source, u.source) d.source as dsource, u.source as usource, d.version as dversion, u.version as uversion from sources_uniq d, ubuntu_sources u where d.release = 'sid' and d.distribution = 'debian' and u.release = 'maverick' and u.distribution = 'ubuntu' and u.source = d.source and u.version > d.version order by d.source asc, u.source asc, d.version desc)
select id, bugs.package, bugs.source, title, dversion, uversion, insts from bugs, ubudeb, popcon_src where popcon_src.source = bugs.source and id in (select id from bugs_rt_affects_testing_and_unstable) and id in (select id from bugs_tags where tag='patch') and severity >= 'serious' and ubudeb.dsource = bugs.source and bugs.source in ('#{spkgss}') order by id")
sth.execute ; rows = sth.fetch_all
rows.each do |r|
   puts "<tr><td><a href=\"http://bugs.debian.org/#{r['id']}\">#{r['id']}</a></td>"
   puts "<td>#{r['package']}</td>"
   puts "<td><a href=\"http://packages.qa.debian.org/#{r['source']}\">#{r['source']}</a> <a href=\"https://launchpad.net/ubuntu/maverick/+source/#{r['source']}/+changelog\">UbCh</a></td>"
   puts "<td>#{r['dversion']} / #{r['uversion']}</td>"
   puts "<td>#{r['insts']}</td>"
   puts "<td>#{r['title']}</td>"
end
puts "</table>"
sth.finish
