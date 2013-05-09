#!/usr/bin/ruby

require 'dbi'
require 'pp'

EXC_SRC = [ ]
INC_SRC = [ ]
POPCON_PERCENT = 5 # x% of submissions must have the package installed

puts "Content-type: text/plain\n\n"
STDERR.reopen(STDOUT)

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
sth = dbh.prepare("select max(insts) from popcon")
sth.execute
rows = sth.fetch_all
sth.finish
minpopcon = rows[0][0].to_i * POPCON_PERCENT/100
puts "# Popcon submissions: #{rows[0][0]} -- #{POPCON_PERCENT}% = #{minpopcon}"

srcs = []
puts "# building initial list"
sth = dbh.prepare <<-EOF
select distinct source from sources where release='sid' and (
source in (select source from popcon_src where insts >= #{minpopcon})
or source in (select source from packages where release='sid' and priority in ('standard', 'important', 'required'))
or source in (select source from packages where section='debian-installer' and release='sid')
);
EOF
sth.execute
rows = sth.fetch_all
srcs = rows.map { |r| r[0] } + INC_SRC - EXC_SRC
sth.finish

puts "# Initial list: #{srcs.sort}"
puts "# Now recursively getting build-depends..."
round = 1
begin
  puts "# Round #{round}, #srcs = #{srcs.length}"
  round += 1
  puts "# Getting build-depends for sources"
  sth = dbh.prepare("select distinct build_depends from sources where release='sid' and source in ('#{srcs.join('\', \'')}')")
  sth.execute
  rows = sth.fetch_all - [[nil]]
  bdeps = []
  rows.each do |r|
    bdeps += r[0].split(/\s*[|,]\s*/).map { |e| e.gsub(/( |\(|\[).*/, '') }
  end
  bdeps.uniq!
  puts "# Getting sources for build-depends"
  sth = dbh.prepare("select distinct source from packages where package in ('#{bdeps.join('\', \'')}')")
  sth.execute
  bdep_srcs = sth.fetch_all.map { |r| r[0] }
  newsrcs = bdep_srcs - srcs
  srcs += bdep_srcs
  srcs.uniq!
  puts "# Adding #{newsrcs.length} source packages: #{newsrcs.sort}"
end until newsrcs.empty?

puts "# Final list of #{srcs.length} important source packages:"
puts srcs.sort.join("\n")

# bugs affecting sid
sth = dbh.prepare("select count(*) from bugs 
where id in (select id from bugs_rt_affects_unstable) 
and not (id in (select id from bugs_merged_with where id > merged_with)) 
AND (severity >= 'serious')")
sth.execute
affsid = sth.fetch_all[0][0]
sth = dbh.prepare("select count(*) from bugs 
where id in (select id from bugs_rt_affects_unstable) 
and not (id in (select id from bugs_merged_with where id > merged_with)) 
AND (severity >= 'serious')
AND source in ('#{srcs.join('\',\'')}')")
sth.execute
affsidimp = sth.fetch_all[0][0]
puts "# #{affsid} RC bugs affecting sid, #{affsidimp} RC bugs affecting sid's important packages"
exit(0)

