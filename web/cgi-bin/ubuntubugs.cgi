#!/usr/bin/ruby -w

require 'dbi'

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:udd')
sth = dbh.prepare("select package, count(distinct bugs.bug)
from ubuntu_bugs_tasks tasks,ubuntu_bugs bugs
where tasks.bug = bugs.bug
and distro in ('', 'Ubuntu')
and status not in ('Invalid', 'Fix Released', 'Won''t Fix')
group by package order by package asc")
sth.execute
while row = sth.fetch do
  puts "#{row['package']}|#{row['count']}"
end
sth.finish
