#!/usr/bin/ruby -w
require 'dbi'

puts "Content-type: text/html\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')

puts "<html><body>"

sth = dbh.prepare("SELECT count(*) 
FROM sources
WHERE distribution = 'debian' AND release = 'sid'")
sth.execute
nb_tot = sth.fetch_all[0][0].to_i
puts "Packages in sid: #{nb_tot}"

puts "<h1>Packages not maintained or co-maintained by DDs or teams</h1>"
sth = dbh.prepare("SELECT count(*) 
FROM sources
WHERE distribution = 'debian' AND release = 'sid'
AND sources.source NOT IN (
SELECT sources.source
FROM sources
LEFT OUTER JOIN uploaders ON (sources.source = uploaders.source AND sources.version = uploaders.version AND sources.distribution = uploaders.distribution AND sources.release = uploaders.release AND sources.component = uploaders.component)
WHERE sources.distribution = 'debian' AND sources.release = 'sid'
AND (maintainer_email in (SELECT email FROM carnivore_emails, active_dds WHERE active_dds.id = carnivore_emails.id)
OR email in (SELECT email FROM carnivore_emails, active_dds WHERE active_dds.id = carnivore_emails.id)
OR maintainer_email ~ '.*@lists.(alioth.)?debian.org'
OR email ~ '.*@lists.(alioth.)?debian.org'
))")
sth.execute
nb_nondd = sth.fetch_all[0][0]
puts "#{nb_nondd} packages (#{nb_nondd*100/nb_tot}%)<br/>"
sth = dbh.prepare("SELECT sources.source, insts
FROM sources, popcon_src
WHERE distribution = 'debian' AND release = 'sid'
AND sources.source = popcon_src.source
AND sources.source NOT IN (
SELECT sources.source
FROM sources
LEFT OUTER JOIN uploaders ON (sources.source = uploaders.source AND sources.version = uploaders.version AND sources.distribution = uploaders.distribution AND sources.release = uploaders.release AND sources.component = uploaders.component)
WHERE sources.distribution = 'debian' AND sources.release = 'sid'
AND (maintainer_email in (SELECT email FROM carnivore_emails, active_dds WHERE active_dds.id = carnivore_emails.id)
OR email in (SELECT email FROM carnivore_emails, active_dds WHERE active_dds.id = carnivore_emails.id)
OR maintainer_email ~ '.*@lists.(alioth.)?debian.org'
OR email ~ '.*@lists.(alioth.)?debian.org'
)
) ORDER BY insts DESC LIMIT 20")
sth.execute
puts "Top 20 packages, sorted by popcon installations"
puts "<table>"
sth.fetch_all.each do |r|
  puts "<tr><td>#{r[0]}</td><td>#{r[1]}</td></tr>"
end
puts "</table>"

### ORPHANED
puts "<h1>Orphaned packages</h1>"
sth = dbh.prepare("select count(*) from sources
                  where distribution='debian' and release='sid'
                  and source in (select source from orphaned_packages where type in ('O', 'ITA'))")
sth.execute
nb_orph = sth.fetch_all[0][0]
puts "#{nb_orph} packages (#{nb_orph*100/nb_tot}%)<br/>"
sth = dbh.prepare("select sources.source, insts from sources, popcon_src
                  where distribution='debian' and release='sid'
                  and sources.source = popcon_src.source
                  and sources.source in (select source from orphaned_packages where type in ('O', 'ITA')) order by insts desc limit 20")
sth.execute
puts "Top 20 packages, sorted by popcon installations"
puts "<table>"
sth.fetch_all.each do |r|
  puts "<tr><td>#{r[0]}</td><td>#{r[1]}</td></tr>"
end
puts "</table>"

puts "<h1>RC-buggy packages in unstable</h1>"
sth = dbh.prepare("select count(*) from sources
                  where distribution='debian' and release='sid'
                  and source in (select bugs.source from bugs_rt_affects_unstable brt, bugs where bugs.id = brt.id and bugs.severity >= 'serious')")
sth.execute
nb_rc = sth.fetch_all[0][0]
puts "#{nb_rc} packages (#{nb_rc*100/nb_tot}%)<br/>"
sth = dbh.prepare("select sources.source, insts from sources, popcon_src
                  where distribution='debian' and release='sid'
                  and sources.source = popcon_src.source
                  and sources.source in (select bugs.source from bugs_rt_affects_unstable brt, bugs where bugs.id = brt.id and bugs.severity >= 'serious') order by insts desc limit 20")
sth.execute
puts "Top 20 packages, sorted by popcon installations"
puts "<table>"
sth.fetch_all.each do |r|
  puts "<tr><td>#{r[0]}</td><td>#{r[1]}</td></tr>"
end
puts "</table>"

puts "<h1>Not Ubuntu-specific, not in Debian</h1>"
sth = dbh.prepare("select count(*) from ubuntu_sources us, ubuntu_popcon_src
WHERE us.distribution = 'ubuntu'
AND us.release = 'karmic'
AND us.source = ubuntu_popcon_src.source
AND us.source !~ '^language-(support|pack)-.*'
AND us.source !~ '^kde-l10n-.*'
AND us.source !~ 'ubuntu'
AND us.source !~ 'launchpad'
AND us.source not in (select source from sources where distribution='debian' and release in ('sid', 'squeeze', 'lenny'))")
sth.execute
nb_u = sth.fetch_all[0][0]
puts "#{nb_u} packages (#{nb_u*100/nb_tot}%)<br/>"
sth = dbh.prepare("select us.source, insts from ubuntu_sources us, ubuntu_popcon_src
WHERE us.distribution = 'ubuntu'
AND us.release = 'karmic'
AND us.source = ubuntu_popcon_src.source
AND us.source !~ '^language-(support|pack)-.*'
AND us.source !~ '^kde-l10n-.*'
AND us.source !~ 'ubuntu'
AND us.source !~ 'launchpad'
AND us.source not in (select source from sources where distribution='debian' and release in ('sid', 'squeeze', 'lenny'))
ORDER BY INSTS DESC")
sth.execute
puts "Top 20 packages, sorted by popcon installations"
puts "<table>"
sth.fetch_all.each do |r|
  puts "<tr><td>#{r[0]}</td><td>#{r[1]}</td></tr>"
end
puts "</table>"


sth.finish
