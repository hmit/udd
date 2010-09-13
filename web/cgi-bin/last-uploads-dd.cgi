#!/usr/bin/ruby -w

require 'dbi'
require 'pp'

puts "Content-type: text/html\n\n"

puts <<-EOF
<html>
<head>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8">
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
<title>Latest uploads for Debian Developers</title>
</head>
<body>
EOF

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')

q = "
select login, max(date) as date
from upload_history, carnivore_keys, carnivore_login
where upload_history.fingerprint = carnivore_keys.key
and carnivore_keys.id = carnivore_login.id
group by login
order by date desc;
"
sth = dbh.prepare(q)
sth.execute ; rows = sth.fetch_all
puts "<h2>Latest uploads for Debian Developers</h2>"
puts "(Looking at keys used by DDs to sign uploads)"

puts "<table>"
puts "<tr><th></th><th>date</th><th>login</th></tr>"
n = 1
rows.each do |r|
  puts "<tr><td>#{n}</td><td>#{r['date']}</td><td>#{r['login']}</td></tr>"
  n+=1
end
puts "</table>"
sth.finish
puts "Query:<br><pre>#{q}</pre>"
