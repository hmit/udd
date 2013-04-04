#!/usr/bin/ruby
# Used by Marco Rodrigues to track bugs in removed packages
require 'dbi'

# see merkel:/org/bugs.debian.org/etc/pseudo-packages.description
PSEUDO_PKGS = ['base', 'cdrom', 'spam', 'press', 'kernel', 'project',
'general', 'listarchives', 'nm.debian.org', 'qa.debian.org',
'ftp.debian.org', 'www.debian.org', 'bugs.debian.org', 'lists.debian.org',
'wnpp', 'cdimage.debian.org', 'tech-ctte', 'mirrors', 'security.debian.org',
'installation-reports', 'upgrade-reports', 'release-notes', 'wiki.debian.org',
'security-tracker', 'release.debian.org', 'debian-policy', 'debian-i18n',
'buildd.emdebian.org', 'buildd.debian.org', 'snapshot.debian.org' ]

EXCLUDED = [
  /^(linux|kernel)-(image|source)-/, # we don't care about those bugs for now
]

puts "Content-type: text/html\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

puts "<html><body>"

sth = dbh.prepare <<-EOF
SELECT source, package, id from bugs
where not affects_unstable and not affects_testing
and not affects_stable and not affects_experimental
and not exists (
select * from bugs_packages where bugs_packages.id = bugs.id and bugs_packages.source in (select source from sources where distribution='debian' and release in ('squeeze', 'wheezy', 'sid', 'experimental')))
and not exists (select * from bugs_packages where bugs_packages.id = bugs.id
and source in (#{PSEUDO_PKGS.map { |p| "'#{p}'"}.join(",")}))
and not package ~ '^(linux|kernel)-(image|source)-'
and status != 'done'
order by source, id
EOF
sth.execute
puts "<table border=\"1\">"
n = 0
sth.fetch_all.each do |r|
  puts "<tr><td><a href=\"http://packages.qa.debian.org/#{r[0]}\">#{r[0]}</a></td>"
  puts "<td><a href=\"http://packages.debian.org/#{r[1]}\">#{r[1]}</a></td>"
  puts "<td><a href=\"http://bugs.debian.org/#{r[2]}\">#{r[2]}</a></td></tr>"
  n += 1
end
puts "</table>"
puts "#{n} bugs found."
sth.finish
