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
<title>New debian maintainers</title>
</head>
<body>
EOF

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

q = "
select changed_by_email, changed_by_name, date, source, version, login from
(select changed_by_email, changed_by_name, date, source, version, fingerprint from upload_history
where (changed_by_name, changed_by_email, date) in (
select changed_by_name, changed_by_email, min(date)
from upload_history
group by changed_by_name, changed_by_email)
) uploads
LEFT JOIN (select distinct key, login from carnivore_keys, carnivore_login where carnivore_keys.id = carnivore_login.id) carn ON uploads.fingerprint = carn.key
where (changed_by_email, login) not in (select email, login from carnivore_emails, carnivore_login where carnivore_emails.id = carnivore_login.id)
order by date desc;
"
sth = dbh.prepare(q)
sth.execute ; rows = sth.fetch_all
puts "<h2>New Debian maintainers</h2>"
puts "This page lists the first upload of each maintainer (identified by his name and email), together with its sponsor."


puts "<table>"
puts "<tr><th>date</th><th>maintainer</th><th>package</th><th>sponsor</th></tr>"
rows.each do |r|
  puts "<tr><td>#{r['date'].to_s.split(' ')[0]}</td><td>#{r['changed_by_name']} &lt;#{r['changed_by_email']}&gt;</td><td>#{r['source']} #{r['version']}</td><td>#{r['login']}</td></tr>"
end
puts "</table>"
sth.finish
puts "Query:<br><pre>#{q}</pre>"
