#!/usr/bin/ruby

require 'cgi'
require 'dbi'
require 'pp'

csvflag = false

cgi = CGI::new

if cgi.has_key?('out') and cgi.params['out'][0] == 'csv'
  csvflag = true
end

puts "Content-type: text/html\n\n"

unless csvflag
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
  <title>Latest uploads for Debian developers</title>
  </head>
  <body>
  EOF
end

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

q = "
select changed_by_email, changed_by_name, date, source, version from upload_history
where (changed_by_name, changed_by_email, date) in (
select changed_by_name, changed_by_email, max(date)
from upload_history
group by changed_by_name, changed_by_email)
order by date desc
"

#in case of csv output just get 100 results
q << " LIMIT 100" if csvflag


sth = dbh.prepare(q)
sth.execute ; rows = sth.fetch_all
unless csvflag
  puts "<h2>Latest uploads for Debian developers</h2>"
  puts "(Looking at Changed-By: only, so developers can appear more than once if they changed the email they are using for Debian work)"

  puts "<table>"
  puts "<tr><th>date</th><th>uploader</th><th>package</th></tr>"
end

rows.each do |r|
  unless csvflag
    puts "<tr><td>#{r['date'].to_s.split(' ')[0]}</td><td>#{r['changed_by_name']} &lt;#{r['changed_by_email']}&gt;</td><td>#{r['source']} #{r['version']}</td></tr>"
  else
    puts "#{r['date'].to_s.split(' ')[0]},#{r['changed_by_name']},#{r['changed_by_email']},#{r['source']} #{r['version']}"
  end

end

unless csvflag
  puts "</table>"
  puts "Query:<br><pre>#{q}</pre>"
end

sth.finish
