#!/usr/bin/ruby -w
require 'dbi'
require 'cgi'
require 'actions'

puts "Content-type: text/html\n\n"

WAIT_RM_O = 50
WAIT_RM_RM = 100
WAIT_O_O = 50
WAIT_ORM_RM = 50

DATEZERO = Date::parse('0000-01-01')
CURDATE = Date::today

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')
cgi = CGI.new

type = cgi.params['t']
if not type.nil?
  type = type[0]
end

if type == 'o'
  orphaned = true
  query = "select * from bapase where type is not null order by orphaned_age desc"
elsif type == 'nmu'
  orphaned = true
  query = "select * from bapase where nmu and nmus > 1 order by nmus desc"
elsif type == 'testing'
  orphaned = true
  query = "select * from bapase where source not in (select source from sources where distribution='debian' and release='squeeze') order by testing_age desc, first_seen asc"
elsif type == 'nodd'
  orphaned = true
  query = <<EOF
select * from bapase where source in (
SELECT source
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
OR email ~ '.*@lists.(alioth.)?debian.org'))
) order by upload_age desc
EOF
elsif type == 'maintnmu'
  orphaned = true
  query = <<EOF
select * from bapase where source in (
  select source from sources where distribution='debian' and release='squeeze' and maintainer_email in (
select nmus.email from
(select email, count(*) as tot from
(select maintainer_email as email, source from sources
where release = 'sid'
and distribution = 'debian'
and component = 'main'
union
select email, source from uploaders 
where release = 'sid'
and distribution = 'debian'
and component = 'main') as foo
group by email) as tot,
(select email, count(*) as nmus from
(select sources.maintainer_email as email, sources.source from sources, upload_history uh
where release = 'sid'
and distribution = 'debian'
and component = 'main'
and sources.source = uh.source and sources.version = uh.version
and uh.nmu
union
select email, uploaders.source from uploaders, upload_history uh
where release = 'sid'
and distribution = 'debian'
and component = 'main'
and uploaders.source = uh.source and uploaders.version = uh.version
and uh.nmu
) as foo
group by email) as nmus
where nmus * 100 / tot >= 100
and nmus.email = tot.email)
union (select source from uploaders where distribution='debian' and release='squeeze' and email in (
select nmus.email from
(select email, count(*) as tot from
(select maintainer_email as email, source from sources
where release = 'sid'
and distribution = 'debian'
and component = 'main'
union
select email, source from uploaders 
where release = 'sid'
and distribution = 'debian'
and component = 'main') as foo
group by email) as tot,
(select email, count(*) as nmus from
(select sources.maintainer_email as email, sources.source from sources, upload_history uh
where release = 'sid'
and distribution = 'debian'
and component = 'main'
and sources.source = uh.source and sources.version = uh.version
and uh.nmu
union
select email, uploaders.source from uploaders, upload_history uh
where release = 'sid'
and distribution = 'debian'
and component = 'main'
and uploaders.source = uh.source and uploaders.version = uh.version
and uh.nmu
) as foo
group by email) as nmus
where nmus * 100 / tot >= 100
and nmus.email = tot.email
))) order by nmus
EOF
else
  puts <<-EOF
  <a href="bapase.cgi?t=o">Orphaned packages</a><br/>
  <a href="bapase.cgi?t=nmu">Packages maintained with NMUs</a><br/>
  <a href="bapase.cgi?t=testing">Packages not in testing</a><br/>
  <a href="bapase.cgi?t=nodd">Packages not maintained by DDs</a><br/>
  <a href="bapase.cgi?t=maintnmu">Packages maintained or co-maintained by people with lots of NMUs</a><br/>
  </body></html>
  EOF
  exit(0)
end

# FIXME add case where type is uknown

$actions = Actions::fetch

puts <<-EOF
<html><head>
<style type="text/css">
  td, th {
    border: 1px solid gray;
    padding-left: 2px;
    padding-right: 2px;
  }
  th {
    font-size: 8pt;
  }
  tr:hover  {
    background-color: #ccc;
  }
  table {
    border-collapse: collapse;
  }
</style>
<title>Bapase</title>
</head><body>
<table border="1"><tr>
<th></th><th>Package</th><th>Action</th>
EOF
puts "<th>Orphaned</th>" if orphaned
puts <<-EOF
<th>Testing</th>
<th>Migrate</th>
<th>Popcon</th>
<th>Bugs</th>
<th>Last upload</th>
<th>NMUs</th>
<th>Comments</th>
</tr>
EOF
sth = dbh.prepare(query)
sth.execute
res = sth.fetch_all
n = 0
res.each do |r|
  n += 1
  pkg = r['source']
  puts "<tr><td>#{n}</td>"
  puts "<td><a href=\"http://packages.qa.debian.org/#{pkg}\">#{pkg}</a>"
  # FIXME removals
  if $actions[pkg]
    if $actions[pkg].act_todo
      puts "<td><b>#{$actions[pkg].act_status}</b></td>"
    else
      puts "<td>#{$actions[pkg].act_status}</td>"
    end
  else
    puts "<td></td>"
  end
  if orphaned
    if r['type']
      puts "<td><a href=\"http://bugs.debian.org/#{r['bug']}\">#{r['type']}</a>&nbsp;(#{r['orphaned_age']})</td>"
    else
      puts "<td></td>"
    end
  end
  if r['testing_age'] and r['testing_age'] > 1
    puts "<td>#{r['testing_age']}</td>"
  else
    puts "<td></td>"
  end
  if r['sync_age'] and r['sync_age'] > 1
    puts "<td>#{r['sync_age']}</td>"
  else
    puts "<td></td>"
  end
  puts "<td>#{r['insts']}&nbsp;/&nbsp;#{r['vote']}</td>"
  puts "<td><a href=\"http://bugs.debian.org/src:#{pkg}\">#{r['rc_bugs']}&nbsp;/&nbsp;#{r['all_bugs']}</a></td>"
  puts "<td>#{r['upload_age']}</td>"
  puts "<td>#{r['nmus']}</td>"
  puts "<td></td>"
  if $actions[pkg]
    comment = $actions[pkg].act_comment.gsub(/#\d+/) do |bug|
      bugn = bug.gsub(/^#/, '')
      "<a href=\"http://bugs.debian.org/#{bugn}\">#{bug}</a>"
    end
    puts "<td>#{comment}</td>"
  else
    puts "<td></td>"
  end
  puts "</tr>"
end
puts "</table>"

puts " -- #{res.length} packages listed."
puts "</body></html>"




#sth.finish
