#!/usr/bin/ruby -w

require 'dbi'
require 'pp'

puts "Content-type: text/html\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
sth = dbh.prepare("select changed_by, count(*) cnt from
upload_history uh, sources s
where s.distribution='debian' and s.release='sid'
and s.source = uh.source and s.version = uh.version
and uh.nmu
and uh.date > current_timestamp - interval '2 months'
group by changed_by having count(*) >= 2 order by cnt desc")
sth.execute ; rows = sth.fetch_all

puts "<h1>People having done more than 2 NMUs over the last 2 months (only uploads still in the archive)</h1>"
puts "<table>"
rows.each do |r|
puts "<tr><td>#{r[0].gsub('<','&lt;').gsub('>','&gt;')}</td><td>#{r[1]}</td></tr>"
end
puts "</table>"


sth = dbh.prepare("select changed_by, count(*) cnt from
upload_history uh, sources s
where s.distribution='debian' and s.release='sid'
and s.source = uh.source and s.version = uh.version
and uh.nmu
group by changed_by order by cnt desc")
sth.execute ; rows = sth.fetch_all

puts "<h1>NMUs uploaded currently in the archive</h1>"
puts "<table>"
rows.each do |r|
puts "<tr><td>#{r[0].gsub('<','&lt;').gsub('>','&gt;')}</td><td>#{r[1]}</td></tr>"
end
puts "</table>"

sth.finish
