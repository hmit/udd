#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
RELEASE='karmic'

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
s = "select source, version, component from ubuntu_sources where distribution = 'ubuntu' and release = '#{RELEASE}' AND source not in (select source from sources where distribution='debian' and release in ('sid', 'squeeze', 'lenny')) AND version !~ 'ubuntu' and version ~ '-' order by component, source"
sth = dbh.prepare(s)
sth.execute ; rows = sth.fetch_all
puts "# #{s}"
rows.each do |r|
  puts "#{r.join(' ')}"
end
