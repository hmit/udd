#!/usr/bin/ruby

require 'dbi'
require 'pp'
require 'cgi'
require 'time'

puts "Content-type: text/html\n\n"

$dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
$dbh.execute("SET statement_timeout TO 90000")

puts "<html><body>"

q= <<EOF
  SELECT id, severity >= 'serious' as sev from bugs where id in (
  SELECT fixed.id FROM public.bugs_fixed_in fixed, public.bugs_found_in found
  WHERE fixed.id=found.id AND regexp_replace(fixed.version, '.*/', '') = regexp_replace(found.version, '.*/', '')
  ) order by id;
EOF
sth = $dbh.prepare(q)
sth.execute
rows = sth.fetch_all

if not rows.empty?
  puts "<h1>Bugs found and fixed in the same version (bold ones are RC)</h1>"
  puts "<ul>"
  rows.each do |r|
    if r['sev']
      puts "<li><b><a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']}</a></b></li>"
    else
      puts "<li><a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']}</a></li>"
    end
  end
  puts "</ul>"
end

q= <<EOF
  SELECT id, severity >= 'serious' as sev from bugs
  where id in ( SELECT id FROM bugs_packages group by id having count(distinct package) > 1)
  AND id in (select id from bugs_fixed_in)
  AND (
    EXISTS (
      (SELECT package FROM bugs_packages where bugs_packages.id = bugs.id) EXCEPT (select distinct regexp_replace(version, '/.*', '') from bugs_fixed_in where bugs_fixed_in.id = bugs.id)
           )
    OR 
    EXISTS ( 
      (select distinct regexp_replace(version, '/.*', '') from bugs_fixed_in where bugs_fixed_in.id = bugs.id)
        EXCEPT
      (SELECT package FROM bugs_packages where bugs_packages.id = bugs.id)
           )
  )
  order by id;
EOF
sth = $dbh.prepare(q)
sth.execute
rows = sth.fetch_all

if not rows.empty?
  puts "<h1>Bugs affecting several packages, fixed in one package, but not in all of them</h1>"
  puts "<ul>"
  rows.each do |r|
    if r['sev']
      puts "<li><b><a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']}</a></b></li>"
    else
      puts "<li><a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']}</a></li>"
    end
  end
  puts "</ul>"
end

puts "</body></html>"
