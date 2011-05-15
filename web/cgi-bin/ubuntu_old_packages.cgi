#!/usr/bin/ruby -w
# Used by DDPO

require 'dbi'

RELEASE='oneiric'

puts "Content-type: text/html\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')
sth = dbh.prepare("select insts from ubuntu_popcon_src where source='coreutils'")
sth.execute
popcon = sth.fetch_all[0][0]
sth.finish
puts "Popcon for coreutils: #{popcon}<br>"
mpc = popcon/1000*100
puts "0.2% of coreutils popcon: #{mpc}<br>"

puts "### was in etch | lenny<br>"
sth = dbh.prepare("select src1.source, src1.version, coalesce(insts, 0) insts
from ubuntu_sources src1
join ubuntu_sources src2 using (source, version)
left join ubuntu_popcon_src popcon using (source)
where src1.component in ('universe', 'multiverse')
and src1.release='#{RELEASE}' and src2.release='hardy'
and src1.source not in
  (select source from sources where release = 'sid')
and src1.source in
  (select source from sources where release in ('etch','lenny'))
and insts < #{mpc}
order by insts asc")
sth.execute
sth.fetch_all.each do |r|
  puts "<a href=\"http://packages.ubuntu.com/search?searchon=sourcenames&keywords=#{r['source']}\">#{r['source']}</a> #{r['version']} #{r['insts']} <a href=\"http://packages.qa.debian.org/#{r['source']}\">PTS</a><br>"
end

puts "### was NOT in etch | lenny<br>"
sth = dbh.prepare("select src1.source, src1.version, coalesce(insts, 0) insts
from ubuntu_sources src1
join ubuntu_sources src2 using (source, version)
left join ubuntu_popcon_src popcon using (source)
where src1.component in ('universe', 'multiverse')
and src1.release='#{RELEASE}' and src2.release='hardy'
and src1.source not in
  (select source from sources where release = 'sid')
and src1.source not in
  (select source from sources where release in ('etch','lenny'))
and insts < #{mpc}
order by insts asc")
sth.execute
sth.fetch_all.each do |r|
  puts "<a href=\"http://packages.ubuntu.com/search?searchon=sourcenames&keywords=#{r['source']}\">#{r['source']}</a> #{r['version']} #{r['insts']} <a href=\"http://packages.qa.debian.org/#{r['source']}\">PTS</a><br>"
end
