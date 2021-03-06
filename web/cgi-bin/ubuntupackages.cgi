#!/usr/bin/ruby
# Used by DDPO

require 'dbi'
require 'yaml'

RELEASE=YAML::load(IO::read('../ubuntu-releases.yaml'))['devel']

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
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
