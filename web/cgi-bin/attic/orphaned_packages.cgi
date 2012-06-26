#!/usr/bin/ruby -w
require 'dbi'

puts "Content-type: text/html\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

puts "<html><body>"

sth = dbh.prepare("select sources.source, insts, date(op.orphaned_time), op.type, op.bug
from sources, popcon_src, orphaned_packages op, bugs b
where sources.source = popcon_src.source
and distribution = 'debian' and release = 'sid'
and sources.source = op.source
and b.id = op.bug
and op.type in ('O', 'ITA')
and insts < 500
and date(op.orphaned_time) < '2008-07-24'
and date(b.last_modified) < '2008-07-24'")
sth.execute
puts "<table>"
sth.fetch_all.each do |r|
  puts "<tr><td><a href=\"http://packages.qa.debian.org/#{r[0]}\">#{r[0]}</a></td><td>#{r[1]}</td><td>#{r[2]}</td><td><a href=\"http://bugs.debian.org/#{r[4]}\">#{r[3]}</a></td></tr>"
end
puts "</table>"
sth.finish
