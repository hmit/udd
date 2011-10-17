#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
RELEASE='precise'

puts "Content-type: text/plain\n\n"

def gcomp(rows, comp)
  t = rows.select { |r| r[0] == comp }
  if t == []
    return 0
  else
    return t[0][1]
  end
end 
def getnums(rows)
  m = gcomp(rows, 'main') + gcomp(rows, 'restricted')
  u = gcomp(rows, 'universe') + gcomp(rows, 'multiverse')
  return [ m, u, m + u ]
end

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')
sth = dbh.prepare("select count(*) from ubuntu_sources where distribution = 'ubuntu' and release = '#{RELEASE}'")
sth.execute ; rows = sth.fetch_all
allpkgs = rows[0][0]

puts "Source packages in Ubuntu: #{allpkgs}"
puts "Source packages per component: [main+restricted, universe+multiverse, total]"
sth = dbh.prepare("select component,count(*) from ubuntu_sources where distribution = 'ubuntu' and release = '#{RELEASE}' group by component")
sth.execute ; rows = sth.fetch_all
pp getnums(rows)

puts "Not Ubuntu specific:"
sth = dbh.prepare("select component, count(*) from ubuntu_sources where distribution = 'ubuntu' and release = '#{RELEASE}'
AND source !~ '^language-(support|pack)-.*' AND source !~ '^kde-l10n-.*'
AND source !~ 'ubuntu' AND source !~ 'launchpad'
group by component")
sth.execute ; rows = sth.fetch_all
pp getnums(rows)

puts "Not Ubuntu specific, not in debian (not in lenny or sid):"
sth = dbh.prepare("select component, count(*) from ubuntu_sources where distribution = 'ubuntu' and release = '#{RELEASE}'
AND source !~ '^language-(support|pack)-.*' AND source !~ '^kde-l10n-.*'
AND source !~ 'ubuntu' AND source !~ 'launchpad'
AND source not in (select source from sources where distribution='debian' and release in ('sid', 'lenny'))
 group by component")
sth.execute ; rows = sth.fetch_all
pp getnums(rows)

puts "Also in debian, version ~ /ubuntu/:"
sth = dbh.prepare("select component, count(*) from ubuntu_sources where distribution = 'ubuntu' and release = '#{RELEASE}'
AND source !~ '^language-(support|pack)-.*' AND source !~ '^kde-l10n-.*' AND source !~ 'ubuntu' AND source !~ 'launchpad'
AND source in (select source from sources where distribution='debian' and release in ('sid', 'lenny'))
AND version ~ 'ubuntu'
 group by component")
sth.execute ; rows = sth.fetch_all
pp getnums(rows)

puts "Also in Debian, diverged + new upstream (version ~ /-0ubuntu/):"
sth = dbh.prepare("select component, count(*) from ubuntu_sources where distribution = 'ubuntu' and release = '#{RELEASE}'
AND source !~ '^language-(support|pack)-.*' AND source !~ '^kde-l10n-.*' AND source !~ 'ubuntu' AND source !~ 'launchpad'
AND source in (select source from sources where distribution='debian' and release in ('sid', 'lenny'))
AND version ~ '-0ubuntu'
 group by component")
sth.execute ; rows = sth.fetch_all
pp getnums(rows)

puts "Also in Debian, (version !~ /ubuntu/):"
sth = dbh.prepare("select component, count(*) from ubuntu_sources where distribution = 'ubuntu' and release = '#{RELEASE}'
AND source !~ '^language-(support|pack)-.*' AND source !~ '^kde-l10n-.*' AND source !~ 'ubuntu' AND source !~ 'launchpad'
AND source in (select source from sources where distribution='debian' and release in ('sid', 'lenny'))
AND version !~ 'ubuntu'
 group by component")
sth.execute ; rows = sth.fetch_all
pp getnums(rows)


puts "diverged+new upstream (main):"
sth = dbh.prepare("select source from ubuntu_sources where distribution = 'ubuntu' and release = '#{RELEASE}' and component = 'main'
AND source !~ '^language-(support|pack)-.*' AND source !~ '^kde-l10n-.*' AND source !~ 'ubuntu' AND source !~ 'launchpad'
AND source in (select source from sources where distribution='debian' and release in ('sid', 'lenny'))
AND version ~ '-0ubuntu' order by source")
sth.execute ; rows = sth.fetch_all
rows.each do |r|
  print  r[0] + ' '
end
puts
puts

puts "diverged+new upstream (universe):"
sth = dbh.prepare("select source from ubuntu_sources where distribution = 'ubuntu' and release = '#{RELEASE}' and component = 'universe'
AND source !~ '^language-(support|pack)-.*' AND source !~ '^kde-l10n-.*' AND source !~ 'ubuntu' AND source !~ 'launchpad'
AND source in (select source from sources where distribution='debian' and release in ('sid', 'lenny'))
AND version ~ '-0ubuntu' order by source")
sth.execute ; rows = sth.fetch_all
rows.each do |r|
  print  r[0] + ' '
end
puts

puts "diverged+new upstream, newer than in wheezy (main):"
sth = dbh.prepare("select u.source, u.version, d.version from ubuntu_sources u, sources d
where u.distribution = 'ubuntu' and u.release = '#{RELEASE}' and u.component = 'main'
and d.distribution = 'debian' and d.release = 'wheezy'
AND u.source !~ '^language-(support|pack)-.*' AND u.source !~ '^kde-l10n-.*' AND u.source !~ 'ubuntu' AND u.source !~ 'launchpad'
AND u.source in (select source from sources where distribution='debian' and release in ('sid', 'lenny'))
AND u.version ~ '-0ubuntu'
AND u.source = d.source
AND u.version > d.version
order by source")
sth.execute ; rows = sth.fetch_all
rows.each do |r|
  print  r[0] + ' '
end
puts
puts

puts "diverged+new upstream, newer than in wheezy (universe):"
sth = dbh.prepare("select u.source, u.version, d.version from ubuntu_sources u, sources d
where u.distribution = 'ubuntu' and u.release = '#{RELEASE}' and u.component = 'universe'
and d.distribution = 'debian' and d.release = 'wheezy'
AND u.source !~ '^language-(support|pack)-.*' AND u.source !~ '^kde-l10n-.*' AND u.source !~ 'ubuntu' AND u.source !~ 'launchpad'
AND u.source in (select source from sources where distribution='debian' and release in ('sid', 'lenny'))
AND u.version ~ '-0ubuntu'
AND u.source = d.source
AND u.version > d.version
order by source")
sth.execute ; rows = sth.fetch_all
rows.each do |r|
  print  r[0] + ' '
end
puts
puts

sth.finish
