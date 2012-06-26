#!/usr/bin/ruby -w
require 'dbi'

puts "Content-type: text/html\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
# unique emails in Maintainers
# unique emails in Maintainers + Uploaders

puts "<html><body>"

puts "<h1>Releases, source packages and maintainers</h1>"
# source packages
sth = dbh.prepare("
select release, count(*) from sources
where distribution = 'debian'
and release in ('etch', 'lenny', 'sid')
and component = 'main'
group by release")
sth.execute
srcpkgs = {}
sth.fetch_all.each do |r|
srcpkgs[r[0]] = r[1]
end

# co-maintained source packages (at least one uploader) + %
sth = dbh.prepare("
select release, count(*) from sources
where distribution = 'debian'
and release in ('etch', 'lenny', 'sid')
and component = 'main'
and uploaders is not null
group by release")
sth.execute
com_srcpkgs = {}
sth.fetch_all.each do |r|
com_srcpkgs[r[0]] = r[1]
end

# unique emails in Maintainers
sth = dbh.prepare("
select release, count(distinct maintainer_email) from sources
where distribution = 'debian'
and component = 'main'
group by release")
sth.execute
maints = {}
sth.fetch_all.each do |r|
maints[r[0]] = r[1]
end

# unique emails in Maintainers + Uploaders
sth = dbh.prepare("select release, count(distinct email) from (
select release, maintainer_email as email from sources
where distribution = 'debian'
and component = 'main'
union
select release, email from uploaders 
where distribution = 'debian'
and component = 'main') as foo group by release")
sth.execute
comaints = {}
sth.fetch_all.each do |r|
comaints[r[0]] = r[1]
end

puts <<-EOF
<table border='1'><tr><th>Distribution</th><th>etch</th><th>lenny</th><th>sid</th></tr>
<tr><th>Source packages</th><td>#{srcpkgs['etch']}</td><td>#{srcpkgs['lenny']}</td><td>#{srcpkgs['sid']}</td></tr>
<tr><th>Co-maintained source packages (at least one uploader)</th><td>#{com_srcpkgs['etch']} (#{(com_srcpkgs['etch'].to_f/srcpkgs['etch']*100).to_i}%)</td><td>#{com_srcpkgs['lenny']} (#{(com_srcpkgs['lenny'].to_f/srcpkgs['lenny']*100).to_i}%)</td><td>#{com_srcpkgs['sid']} (#{(com_srcpkgs['sid'].to_f/srcpkgs['sid']*100).to_i}%)</td></tr>
<tr><th>Maintainers (=different emails in Maintainer:) ; Packages per maintainer</th>
<td>#{maints['etch']} (#{"%.2f"%(srcpkgs['etch'].to_f/maints['etch'])})</td>
<td>#{maints['lenny']} (#{"%.2f"%(srcpkgs['lenny'].to_f/maints['lenny'])})</td>
<td>#{maints['sid']} (#{"%.2f"%(srcpkgs['sid'].to_f/maints['sid'])})</td></tr>
<tr><th>Maintainers, inc. Uploaders (different emails in Maintainer: or Uploaders:) ; Packages per maintainer</th>
<td>#{comaints['etch']} (#{"%.2f"%(srcpkgs['etch'].to_f/comaints['etch'])})</td>
<td>#{comaints['lenny']} (#{"%.2f"%(srcpkgs['lenny'].to_f/comaints['lenny'])})</td>
<td>#{comaints['sid']} (#{"%.2f"%(srcpkgs['sid'].to_f/comaints['sid'])})</td></tr>
</table>
EOF

puts "<h1>Maintainers that maintain a lot of packages</h1>"
puts "(= number of packages per email listed in Maintainer: or Uploaders:)<br/>"
sth = dbh.prepare("select email, count(distinct source) from (
select maintainer_email as email, source from sources
where release = 'sid'
and distribution = 'debian'
and component = 'main'
union
select email, source from uploaders 
where release = 'sid'
and distribution = 'debian'
and component = 'main') as foo
group by email having count(distinct source) >= 10 order by count desc limit 50")
sth.execute
puts "<table border='1'><tr><th>email</th><th>nb of packages</th></tr>"
sth.fetch_all.each do |r|
puts "<tr><td>#{r[0]}</td><td>#{r[1]}</td></tr>"
end
puts "</table>"

puts "<h1>Maintainers that maintain a lot of packages <b>alone</b></h1>"
puts "(= number of packages per email listed in Maintainer:, excluding packages with uploaders)<br/>"
sth = dbh.prepare("select maintainer_email as email, count(source) from sources
where release = 'sid'
and distribution = 'debian'
and component = 'main'
and uploaders is null
group by email having count(distinct source) >= 10 order by count desc limit 50")
sth.execute
puts "<table border='1'><tr><th>email</th><th>nb of packages</th></tr>"
sth.fetch_all.each do |r|
puts "<tr><td>#{r[0]}</td><td>#{r[1]}</td></tr>"
end
puts "</table>"

puts "<h1>Maintainers with an high workload</h1>"
puts "We assume that the maintainance of a package is shared equally amongst all co-maintainers. We assign a <i>cost</i> of 1 to packages maintained without co-maintainers, 0.5 to packages maintained by 2 co-maintainers, ..., 0.1 to packages maintained by 10 co-maintainers.<br>Of course, that's broken because team emails only count as 1 co-maintainer. But it's better than nothing. (or not?)"

sth = dbh.prepare("create temporary table costs as select source, 1.0/count(distinct email) as cost from (
select maintainer_email as email, source from sources
where release = 'sid'
and distribution = 'debian'
and component = 'main'
union
select email, source from uploaders 
where release = 'sid'
and distribution = 'debian'
and component = 'main') as foo
group by source")
sth.execute

sth = dbh.prepare("select email, sum(cost) as total_cost from (
select maintainer_email as email, source from sources
where release = 'sid'
and distribution = 'debian'
and component = 'main'
union
select email, source from uploaders 
where release = 'sid'
and distribution = 'debian'
and component = 'main') as maintsrcs, costs
where costs.source = maintsrcs.source
group by email having sum(cost) >= 10 order by total_cost desc limit 70")
sth.execute
puts "<table border='1'><tr><th>email</th><th>total <i>cost</i> of all (co-)maintained packages</th></tr>"
sth.fetch_all.each do |r|
puts "<tr><td>#{r[0]}</td><td>#{"%.2f"%(r[1])}</td></tr>"
end
puts "</table>"
puts "</body></html>"
sth.finish
