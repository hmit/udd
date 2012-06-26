#!/usr/bin/ruby -w
# Used by Harvest@Ubuntu

require 'dbi'

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
sth = dbh.prepare("select source, version
from sources_uniq where distribution='debian' and release='squeeze' and component='main' and (architecture = 'all' or architecture = 'any' or architecture ~ 'amd64') order by source")
sth.execute
while row = sth.fetch do
  puts "#{row['source']} #{row['version']} #{row['component']}"
end
sth.finish
