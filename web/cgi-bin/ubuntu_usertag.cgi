#!/usr/bin/ruby

require 'dbi'
require 'pp'

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
<title>Ubuntu usertags on the BTS</title>
</head>
<body>
EOF

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

sth = dbh.prepare("select email, tag, count(*) from bugs_usertags group by email, tag order by count desc limit 100")
sth.execute ; rows = sth.fetch_all

puts "<h2>Top 100 usertags in Debian</h2>"

puts "<table>"
puts "<tr><th>email</th><th>tag</th><th>count</th></tr>"
rows.each do |r|
  if r['email'] =~ /ubuntu/
    puts "<tr><td><b>#{r['email']}</b></td><td><b>#{r['tag']}</b></td><td><b>#{r['count']}</b></td></tr>"
  else
    puts "<tr><td>#{r['email']}</td><td>#{r['tag']}</td><td>#{r['count']}</td></tr>"
  end
end
puts "</table>"
sth.finish

puts "<h2>Ubuntu usertags</h2>"
sth = dbh.prepare("select email, tag, count(*) from bugs_usertags where email='ubuntu-devel@lists.ubuntu.com' group by email, tag order by count desc")
sth.execute ; rows = sth.fetch_all
puts "<table>"
puts "<tr><th>email</th><th>tag</th><th>count</th></tr>"
rows.each do |r|
  puts "<tr><td>#{r['email']}</td><td>#{r['tag']}</td><td>#{r['count']}</td></tr>"
end
puts "</table>"
sth.finish

puts "<h2>Submitters of origin-ubuntu bugs (with >5 bugs)</h2>"
puts "(The origin-ubuntu usertag might have been added when a patch was submitted to an existing bug. In that case the original submitter is listed.)"
sth = dbh.prepare("select (case when submitter_name = '' then submitter_email else submitter_name end) as name, count(*) from all_bugs, bugs_usertags where email='ubuntu-devel@lists.ubuntu.com' and all_bugs.id = bugs_usertags.id group by name having count(*) >5 order by count desc")
sth.execute ; rows = sth.fetch_all
puts "<table>"
puts "<tr><th>name</th><th>count</th></tr>"
rows.each do |r|
  puts "<tr><td>#{r['name']}</td><td>#{r['count']}</td></tr>"
end
puts "</table>"
sth.finish

