#!/usr/bin/ruby -w

require 'dbi'
require 'pp'

puts "Content-type: text/html\n\n"

puts "<html><body>"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')

sth = dbh.prepare("select email, tag, count(*) from bugs_usertags group by email, tag order by count desc limit 100")
sth.execute ; rows = sth.fetch_all

puts "<h1>Top 100 usertags in Debian</h1>"

puts "<table>"
rows.each do |r|
  if r['email'] =~ /ubuntu/
    puts "<tr><td><b>#{r['email']}</b></td><td><b>#{r['tag']}</b></td><td><b>#{r['count']}</b></td></tr>"
  else
    puts "<tr><td>#{r['email']}</td><td>#{r['tag']}</td><td>#{r['count']}</td></tr>"
  end
end
puts "</table>"
sth.finish

puts "<h1>Ubuntu usertags</h1>"
sth = dbh.prepare("select email, tag, count(*) from bugs_usertags where email='ubuntu-devel@lists.ubuntu.com' group by email, tag order by count desc")
sth.execute ; rows = sth.fetch_all
puts "<table>"
rows.each do |r|
  puts "<tr><td>#{r['email']}</td><td>#{r['tag']}</td><td>#{r['count']}</td></tr>"
end
puts "</table>"
sth.finish

puts "<h1>Submitters of origin-ubuntu bugs (with >5 bugs)</h1>"
puts "(Might not provide accurate information: the origin-ubuntu usertag might have been added when a patch was submitted to an existing bug)"
sth = dbh.prepare("select submitter, count(*) from all_bugs, bugs_usertags where email='ubuntu-devel@lists.ubuntu.com' and all_bugs.id = bugs_usertags.id group by submitter having count(*) >5 order by count desc")
sth.execute ; rows = sth.fetch_all
puts "<table>"
rows.each do |r|
  puts "<tr><td>#{r['submitter']}</td><td>#{r['count']}</td></tr>"
end
puts "</table>"
sth.finish

