#!/usr/bin/ruby -w
# Used by bdmurray @ ubuntu

require 'dbi'

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
sth = dbh.prepare("
select distinct bugs.id, bugs.package, bugs.source from bugs
 where id in (select id from bugs_tags where tag='patch')
 and id not in (select id from bugs_usertags where email='ubuntu-devel@lists.ubuntu.com' and tag = 'ubuntu-patch')
and status != 'done'")
sth.execute
while row = sth.fetch do
  puts "#{row['source']},http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=#{row['id']},#{row['id']}"
end
sth.finish
