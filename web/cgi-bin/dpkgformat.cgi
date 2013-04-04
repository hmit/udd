#!/usr/bin/ruby
# Used by DDPO

require 'dbi'

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
sth = dbh.prepare("select format, count(*) as cnt
from sources_uniq
where distribution='debian' and release='sid'
group by format order by format asc")
sth.execute
while row = sth.fetch do
  puts "#{row['cnt']} #{row['format']}"
end
sth.finish
