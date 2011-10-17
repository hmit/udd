#!/usr/bin/ruby -w
# Used by DDPO

require 'dbi'

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')
sth = dbh.prepare("SELECT tbugs.package, bugs, patches
from (select package, count(distinct bugs.bug) as bugs
from ubuntu_bugs_tasks tasks,ubuntu_bugs bugs
where tasks.bug = bugs.bug
and distro in ('Ubuntu')
and status not in ('Invalid', 'Fix Released', 'Won''t Fix', 'Opinion')
group by package) tbugs
full join
(select package, count(distinct bugs.bug) as patches
from ubuntu_bugs_tasks tasks,ubuntu_bugs bugs
where tasks.bug = bugs.bug
and distro in ('', 'Ubuntu')
and status not in ('Invalid', 'Fix Released', 'Won''t Fix', 'Opinion')
and bugs.patches is true
group by package) tpatches on tbugs.package = tpatches.package order by package asc")
sth.execute
while row = sth.fetch do
  puts "#{row['package']}|#{row['bugs']}|#{row['patches'] || 0}"
end
sth.finish
