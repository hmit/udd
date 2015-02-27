#!/usr/bin/ruby

require 'dbi'
require 'pp'

EXC_SRC = [ ]
INC_SRC = [ 'debian-installer', 'debian-cd' ]
POPCON_PERCENT = 5 # x% of submissions must have the package installed

puts "Content-type: text/plain\n\n"
STDERR.reopen(STDOUT)

$dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
def get_sources(popcon_percent)
  sth = $dbh.prepare("select max(insts) from popcon")
  sth.execute
  rows = sth.fetch_all
  sth.finish
  minpopcon = rows[0][0].to_i * popcon_percent/100

  srcs = []
  sth = $dbh.prepare <<-EOF
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

  round = 1
  begin
    round += 1
    sth = $dbh.prepare("select distinct build_depends from sources where release='sid' and source in ('#{srcs.join('\', \'')}')")
    sth.execute
    rows = sth.fetch_all - [[nil]]
    bdeps = []
    rows.each do |r|
      bdeps += r[0].split(/\s*[|,]\s*/).map { |e| e.gsub(/( |\(|\[).*/, '') }
    end
    bdeps.uniq!
    sth = $dbh.prepare("select distinct source from packages where package in ('#{bdeps.join('\', \'')}')")
    sth.execute
    bdep_srcs = sth.fetch_all.map { |r| r[0] }
    newsrcs = bdep_srcs - srcs
    srcs += bdep_srcs
    srcs.uniq!
  end until newsrcs.empty?
  return srcs.sort
end

last_pc = 5
last_srcs = get_sources(last_pc)
(6..50).each do |pc|
  srcs = get_sources(pc)
  puts "Going from #{last_pc}% to #{pc}%, #{(last_srcs - srcs).length} packages no longer key; bugs:"
  s = last_srcs - srcs
  sth = $dbh.prepare("select id, bugs.source, title, last_modified  from bugs 
  where id in (select id from bugs_rt_affects_testing) 
  and not (id in (select id from bugs_merged_with where id > merged_with)) 
  AND (severity >= 'serious')
  AND source in ('#{s.join('\',\'')}') order by id")
  sth.execute
  rems = sth.fetch_all
  rems.each do |r|
    puts "## #{r[1]} #{r[0]} #{r[2]} (last modified: #{r[3]}"
  end
  last_pc = pc
  last_srcs = srcs
end
