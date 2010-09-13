#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
require 'cgi'

puts "Content-type: text/html\n\n"

RELEASE_RESTRICT = [
  ['squeeze', 'squeeze', 'id in (select id from bugs_rt_affects_testing)'],
  ['sid', 'sid', 'id in (select id from bugs_rt_affects_unstable)'],
  ['squeeze_and_sid', 'squeeze and sid', 'id in (select id from bugs_rt_affects_testing_and_unstable)'],
  ['squeeze_or_sid', 'squeeze or sid', 'id in (select id from bugs_rt_affects_testing union select id from bugs_rt_affects_unstable)'],
  ['squeeze_not_sid', 'squeeze, not sid', 'id in (select id from bugs_rt_affects_testing) and id not in (select id from bugs_rt_affects_unstable)'],
  ['sid_not_squeeze', 'sid, not squeeze', 'id in (select id from bugs_rt_affects_unstable) and id not in (select id from bugs_rt_affects_testing)']
]

FILTERS = [
 ['patch', 'tagged patch', 'id in (select id from bugs_tags where tag=\'patch\')'],
 ['pending', 'tagged pending', 'id in (select id from bugs_tags where tag=\'pending\')'],
 ['security', 'tagged security', 'id in (select id from bugs_tags where tag=\'security\')'],
 ['notmain', 'packages not in main', 'id not in (select id from bugs_packages, sources where bugs_packages.source = sources.source and component=\'main\')'],
 ['notsqueeze', 'packages not in squeeze', 'id not in (select id from bugs_packages, sources where bugs_packages.source = sources.source and release=\'squeeze\')'],
 ['merged', 'merged bugs', 'id in (select id from bugs_merged_with where id > merged_with)'],
 ['done', 'marked as done', 'status = \'done\''],
]

TYPES = [
  ['rc', 'release-critical bugs', 'severity >= \'serious\'', true ],
  ['ipv6', 'release goal: IPv6 support', 'id in (select id from bugs_tags where tag=\'ipv6\')', false ],
  ['lfs', 'release goal: Large File Support', 'id in (select id from bugs_tags where tag=\'lfs\')', false ],
  ['boot', 'release goal: boot performance (init.d dependencies)', 'id in (select id from bugs_usertags where email = \'initscripts-ng-devel@lists.alioth.debian.org\')', false],
  ['oldgnome', 'release goal: remove obsolete GNOME libraries', 'id in (select id from bugs_usertags where email = \'pkg-gnome-maintainers@lists.alioth.debian.org\' and tag=\'oldlibs\')', false],
]

SORTS = [
  ['id', 'bug#'],
  ['source', 'source package'],
  ['package', 'binary package'],
  ['last_modified', 'last modified']
]

cgi = CGI::new
# releases
if RELEASE_RESTRICT.map { |r| r[0] }.include?(cgi.params['release'][0])
  release = cgi.params['release'][0]
else
  release = 'squeeze'
end
# sorts
if SORTS.map { |r| r[0] }.include?(cgi.params['sortby'][0])
  sortby = cgi.params['sortby'][0]
else
  sortby = 'id'
end
if ['asc', 'desc'].include?(cgi.params['sorto'][0])
  sorto = cgi.params['sorto'][0]
else
  sorto = 'asc'
end
# filters
filters = {}
FILTERS.map { |r| r[0] }.each do |e|
  if ['notconsidered', 'only', 'ign'].include?(cgi.params[e][0])
    filters[e] = cgi.params[e][0]
  else
    filters[e] = (e == 'merged' ? 'ign' : 'notconsidered')
  end
end
# filter: newer than X days
if ['notconsidered', 'only', 'ign'].include?(cgi.params['fnewer'][0])
  fnewer = cgi.params['fnewer'][0]
else
  fnewer = 'notconsidered'
end
if cgi.params['fnewerval'][0] =~ /^[0-9]+$/
  fnewerval = cgi.params['fnewerval'][0].to_i
else
  fnewerval = 7
end
# types
types = {}
TYPES.each do |t|
  if cgi.params == {}
    types[t[0]] = t[3]
  else
    if cgi.params[t[0]][0] == '1'
      types[t[0]] = true
    else
      types[t[0]] = false
    end
  end
end

puts <<-EOF
<html>
<head>
<style type="text/css">
  table.buglist td, table.buglist th {
    border: 1px solid gray;
    padding-left: 3px;
    padding-right: 3px;
  }
  table.buglist tr:hover  {
    background-color: #ccc;
  }
  table {
    border-collapse: collapse;
  }

</style>
<title>RC Bugs List @ UDD</title>
</head>
<body>
<h1>Release Critical Bugs List</h1>

<form action="bugs.cgi" method="get">
<p><b>Bugs affecting:</b>
EOF

RELEASE_RESTRICT.each do |r|
  checked = (release == r[0] ? 'CHECKED=\'1\'':'')
  puts "<input type='radio' name='release' value='#{r[0]}' #{checked}/>#{r[1]}&nbsp;&nbsp;"
end
puts <<-EOF
</p>
<table class="invisible"><tr><td>
<table class="buglist">
<tr><th colspan='4'>FILTERS</th></tr>
<tr><th>not considered</th><th>only</th><th>ignore</th><th>type</th></tr>
EOF
FILTERS.each do |r|
  puts <<-EOF
  <tr>
  <td style='text-align: center;'><input type='radio' name='#{r[0]}' value='' #{filters[r[0]]=='notconsidered'?'CHECKED=\'1\'':''}/></td>
  <td style='text-align: center;'><input type='radio' name='#{r[0]}' value='only' #{filters[r[0]]=='only'?'CHECKED=\'1\'':''}/></td>
  <td style='text-align: center;'><input type='radio' name='#{r[0]}' value='ign' #{filters[r[0]]=='ign'?'CHECKED=\'1\'':''}'/></td>
  <td>#{r[1]}</td>
  </tr>
  EOF
end
# newer than
puts <<-EOF
  <tr>
  <td style='text-align: center;'><input type='radio' name='fnewer' value='' #{fnewer=='notconsidered'?'CHECKED=\'1\'':''}/></td>
  <td style='text-align: center;'><input type='radio' name='fnewer' value='only' #{fnewer=='only'?'CHECKED=\'1\'':''}/></td>
  <td style='text-align: center;'><input type='radio' name='fnewer' value='ign' #{fnewer=='ign'?'CHECKED=\'1\'':''}'/></td>
  <td>newer than <input type='text' size='3' name='fnewerval' value='#{fnewerval}'/> days</td>
  </tr>
EOF
puts "</table></td><td style='padding-left: 20px'><table class='buglist'>"
puts "<tr><th colspan='2'>Bug types</th></tr>"
TYPES.each do |t|
  checked = types[t[0]]?" checked='1'":""
  puts "<tr><td><input type='checkbox' name='#{t[0]}' value='1'#{checked}/></td><td>#{t[1]}</td></tr>"
end
puts "</table></td></tr></table>"
puts "<p><b>Sort by:</b> "
SORTS.each do |r|
  checked = (sortby == r[0] ? 'CHECKED=\'1\'':'')
  puts "<input type='radio' name='sortby' value='#{r[0]}' #{checked}/>#{r[1]}&nbsp;&nbsp;"
end
puts "<b> -- </b>"
[['asc', 'increasing'],[ 'desc', 'decreasing']].each do |r|
  checked = (sorto == r[0] ? 'CHECKED=\'1\'':'')
  puts "<input type='radio' name='sorto' value='#{r[0]}' #{checked}/>#{r[1]}&nbsp;&nbsp;"
end
puts <<-EOF
</p><input type='submit' value='Update'/>
</form>
EOF
if cgi.params != {}

# Generate and execute query
tstart = Time::now
dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')
q = "select id, bugs.package, bugs.source, title, last_modified from bugs \n"
q += "where #{RELEASE_RESTRICT.select { |r| r[0] == release }[0][2]} \n"
FILTERS.each do |f|
  if filters[f[0]] == 'only'
    q += "and #{f[2]} \n"
  elsif filters[f[0]] == 'ign'
    q += "and not (#{f[2]}) \n"
  end
end
if fnewer == 'only'
  q += "and (current_timestamp - interval '#{fnewerval} days' <= arrival) \n"
elsif fnewer == 'ign'
  q += "and (current_timestamp - interval '#{fnewerval} days' > arrival) \n"
end
q += "AND ("
q += TYPES.select { |t| types[t[0]] }.map { |t| t[2] }.join("\n OR ")
q += ")\n "
q += "order by #{sortby} #{sorto}"
sth = dbh.prepare(q)
sth.execute
rows = sth.fetch_all

puts "<p><b>#{rows.length} bugs found.</b></p>"
puts <<-EOF
<table class="buglist">
<tr><th>bug#</th><th>source pkg</th><th>binary pkg</th><th>title</th><th>last&nbsp;modified</th></tr>
EOF
rows.each do |r|
  puts "<tr><td style='text-align: center;'><a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']}</a></td>"
  puts "<td style='text-align: center;'>"
  puts r['source'].split(/,\s*/).map { |pkg| "<a href=\"http://packages.qa.debian.org/#{pkg}\">#{pkg}</a>" }.join(', ')
  puts "</td>"
  puts <<-EOF
  <td style='text-align: center;'>#{r['package']}</td>
  <td>#{r['title']}</td>
  <td style='text-align: center;'>#{r['last_modified'].to_date}</td>
  </tr>
  EOF
end
=begin
release goals:
all
include / only

columns:
id
source
package
title

time
data last refreshed
EOF
=end

=begin
sth = dbh.prepare("select id, bugs.package, bugs.source, insts, title from bugs, popcon_src where bugs.source = popcon_src.source and id in (select id from bugs_rt_affects_testing_and_unstable) and id in (select id from bugs_tags where tag='patch') and id not in (select id from bugs_tags where tag='pending') and severity >= 'serious' order by id")
sth.execute ; rows = sth.fetch_all

puts "<h2>RC bugs tagged patch (and not pending)</h2>"
puts "<table>"
puts "<tr><th>bug</th><th>package</th><th>source</th><th>popcon</th><th>title</th></tr>"
rows.each do |r|
   puts "<tr><td><a href=\"http://bugs.debian.org/#{r['id']}\">#{r['id']}</a></td>"
   puts "<td>#{r['package']}</td>"
   puts "<td><a href=\"http://packages.qa.debian.org/#{r['source']}\">#{r['source']}</a></td>"
   puts "<td>#{r['insts']}</td>"
   puts "<td>#{r['title']}</td>"
end
puts "</table>"
sth.finish

puts "<h2>RC bugs on packages with a newer version in Ubuntu (possible patches), not tagged patch nor pending</h2>"
puts "<table>"
puts "<tr><th>bug</th><th>package</th><th>source</th><th>versions (D/U)</th><th>popcon</th><th>title</th></tr>"

sth = dbh.prepare("WITH ubudeb AS (select distinct on (d.source, u.source) d.source as dsource, u.source as usource, d.version as dversion, u.version as uversion from sources_uniq d, ubuntu_sources u where d.release = 'sid' and d.distribution = 'debian' and u.release = '#{URELEASE}' and u.distribution = 'ubuntu' and u.source = d.source and u.version > d.version order by d.source asc, u.source asc, d.version desc)
select id, bugs.package, bugs.source, title, dversion, uversion, insts from bugs, ubudeb, popcon_src where popcon_src.source = bugs.source and id in (select id from bugs_rt_affects_testing_and_unstable) and id not in (select id from bugs_tags where tag='patch') and id not in (select id from bugs_tags where tag='pending') and severity >= 'serious' and ubudeb.dsource = bugs.source order by id")
sth.execute ; rows = sth.fetch_all
rows.each do |r|
   puts "<tr><td><a href=\"http://bugs.debian.org/#{r['id']}\">#{r['id']}</a></td>"
   puts "<td>#{r['package']}</td>"
   puts "<td><a href=\"http://packages.qa.debian.org/#{r['source']}\">#{r['source']}</a> <a href=\"https://launchpad.net/ubuntu/#{URELEASE}/+source/#{r['source']}/+changelog\">UbCh</a></td>"
   puts "<td>#{r['dversion']} / #{r['uversion']}</td>"
   puts "<td>#{r['insts']}</td>"
   puts "<td>#{r['title']}</td>"
end
puts "</table>"
sth.finish

sth = dbh.prepare("select id, bugs.package, bugs.source, insts, title from bugs, popcon_src where bugs.source = popcon_src.source and id in (select id from bugs_rt_affects_testing) and id not in (select id from bugs_rt_affects_unstable) and severity >= 'serious' order by package")
sth.execute ; rows = sth.fetch_all

puts "<h2>RC bugs affecting only testing (not unstable, and not pending)</h2>"
puts "<table>"
puts "<tr><th>bug</th><th>package</th><th>source</th><th>popcon</th><th>title</th></tr>"
rows.each do |r|
   puts "<tr><td><a href=\"http://bugs.debian.org/#{r['id']}\">#{r['id']}</a></td>"
   puts "<td>#{r['package']}</td>"
   puts "<td><a href=\"http://packages.qa.debian.org/#{r['source']}\">#{r['source']}</a></td>"
   puts "<td>#{r['insts']}</td>"
   puts "<td>#{r['title']}</td>"
end
puts "</table>"
sth.finish

=end
puts "</table>"
sth2 = dbh.prepare("select max(start_time) from timestamps where source = 'bugs' and command = 'run'")
sth2.execute ; r2 = sth2.fetch_all
puts "<p><b>Generated in #{Time::now - tstart} seconds. Last data update: #{r2[0][0]}</b></p>"
puts "<pre>#{q}</pre>"
end # if cgi.params != {}
puts <<-EOF
<hr/>
<small>Suggestions / comments / patches to lucas at debian dot org. <a href="http://svn.debian.org/wsvn/collab-qa/udd/web/cgi-bin/bugs.cgi">source code</a>.</small>
</body>
</html>
EOF
