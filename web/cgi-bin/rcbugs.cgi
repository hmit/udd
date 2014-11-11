#!/usr/bin/ruby

require 'dbi'
require 'pp'
require 'yaml'
require 'cgi'

csvflag = false

cgi = CGI::new

if cgi.has_key?('out') and cgi.params['out'][0] == 'csv'
  csvflag = true
end

URELEASE=YAML::load(IO::read('../ubuntu-releases.yaml'))['devel']

puts "Content-type: text/html\n\n"

unless csvflag
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
end

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

sth = dbh.prepare("select id, bugs.package, bugs.source, insts, title from bugs, popcon_src where bugs.source = popcon_src.source and id in (select id from bugs_rt_affects_testing_and_unstable) and id in (select id from bugs_tags where tag='patch') and id not in (select id from bugs_tags where tag='pending') and severity >= 'serious' order by id")
sth.execute ; rows = sth.fetch_all

unless csvflag
  puts "<h2>RC bugs tagged patch (and not pending)</h2>"
  puts "<table>"
  puts "<tr><th>bug</th><th>package</th><th>source</th><th>popcon</th><th>title</th></tr>"
else
  puts "#RC bugs tagged patch (and not pending)"
end

rows.each do |r|
  unless csvflag
    puts "<tr><td><a href=\"http://bugs.debian.org/#{r['id']}\">#{r['id']}</a></td>"
    puts "<td>#{r['package']}</td>"
    puts "<td><a href=\"http://tracker.debian.org/#{r['source']}\">#{r['source']}</a></td>"
    puts "<td>#{r['insts']}</td>"
    puts "<td>#{r['title']}</td>"
  else
    puts "#{r['id']},#{r['source']},#{r['insts']},#{r['title']}"
    #puts "bug, source, popcorn, title"
  end

end

puts "</table>" unless csvflag

sth.finish

unless csvflag
  puts "<h2>RC bugs on packages with a newer version in Ubuntu (possible patches), not tagged patch nor pending</h2>"
  puts "<table>"
  puts "<tr><th>bug</th><th>package</th><th>source</th><th>versions (D/U)</th><th>popcon</th><th>title</th></tr>"
else
  puts "#RC bugs on packages with a newer version in Ubuntu (possible patches), not tagged patch nor pending"
  #puts "bug, source, versions, popcon, title"
end

sth = dbh.prepare("WITH ubudeb AS (select distinct on (d.source, u.source) d.source as dsource, u.source as usource, d.version as dversion, u.version as uversion from sources_uniq d, ubuntu_sources u where d.release = 'sid' and d.distribution = 'debian' and u.release = '#{URELEASE}' and u.distribution = 'ubuntu' and u.source = d.source and u.version > d.version order by d.source asc, u.source asc, d.version desc)
select id, bugs.package, bugs.source, title, dversion, uversion, insts from bugs, ubudeb, popcon_src where popcon_src.source = bugs.source and id in (select id from bugs_rt_affects_testing_and_unstable) and id not in (select id from bugs_tags where tag='patch') and id not in (select id from bugs_tags where tag='pending') and severity >= 'serious' and ubudeb.dsource = bugs.source order by id")
sth.execute ; rows = sth.fetch_all
rows.each do |r|
  unless csvflag
    puts "<tr><td><a href=\"http://bugs.debian.org/#{r['id']}\">#{r['id']}</a></td>"
    puts "<td>#{r['package']}</td>"
    puts "<td><a href=\"http://tracker.debian.org/#{r['source']}\">#{r['source']}</a> <a href=\"https://launchpad.net/ubuntu/#{URELEASE}/+source/#{r['source']}/+changelog\">UbCh</a></td>"
    puts "<td>#{r['dversion']} / #{r['uversion']}</td>"
    puts "<td>#{r['insts']}</td>"
    puts "<td>#{r['title']}</td>"
  else
    puts "#{r['id']},#{r['source']},#{r['dversion']} / #{r['uversion']},#{r['insts']},#{r['title']}"
  end

end

puts "</table>" unless csvflag

sth.finish

sth = dbh.prepare("select id, bugs.package, bugs.source, insts, title from bugs, popcon_src where bugs.source = popcon_src.source and id in (select id from bugs_rt_affects_testing) and id not in (select id from bugs_rt_affects_unstable) and severity >= 'serious' order by package")
sth.execute ; rows = sth.fetch_all

unless csvflag
  puts "<h2>RC bugs affecting only testing (not unstable, and not pending)</h2>"
  puts "<table>"
  puts "<tr><th>bug</th><th>package</th><th>source</th><th>popcon</th><th>title</th></tr>"
else
  puts "#RC bugs affecting only testing (not unstable, and not pending)"
  #puts "bug,source, popcon, title"
end
rows.each do |r|
  unless csvflag
    puts "<tr><td><a href=\"http://bugs.debian.org/#{r['id']}\">#{r['id']}</a></td>"
    puts "<td>#{r['package']}</td>"
    puts "<td><a href=\"http://tracker.debian.org/#{r['source']}\">#{r['source']}</a></td>"
    puts "<td>#{r['insts']}</td>"
    puts "<td>#{r['title']}</td>"
  else
    puts "#{r['id']},#{r['source']},#{r['insts']},#{r['title']}"
  end

end

puts "</table>" unless csvflag

sth.finish


