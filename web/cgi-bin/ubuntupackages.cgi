#!/usr/bin/ruby -w
# Used by DDPO

require 'dbi'

RELEASE='karmic'

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')
sth = dbh.prepare("select source, version
from ubuntu_sources
where distribution = 'ubuntu'
and release = '#{RELEASE}'
order by source asc")
sth.execute
while row = sth.fetch do
  puts "#{row['source']} #{row['version']}"
end
sth.finish
