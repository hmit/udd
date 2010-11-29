#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
require 'cgi'

puts "Content-type: text/html\n\n"

RELEASE_RESTRICT = [
  ['squeeze', 'squeeze', 'id in (select id from bugs_rt_affects_testing)'],
  ['sid', 'sid', 'id in (select id from bugs_rt_affects_unstable)'],
  ['squeeze_and_sid', 'squeeze and sid', 'id in (select id from bugs_rt_affects_testing) and id in (select id from bugs_rt_affects_unstable)'],
  ['squeeze_or_sid', 'squeeze or sid', 'id in (select id from bugs_rt_affects_testing union select id from bugs_rt_affects_unstable)'],
  ['squeeze_not_sid', 'squeeze, not sid', 'id in (select id from bugs_rt_affects_testing) and id not in (select id from bugs_rt_affects_unstable)'],
  ['sid_not_squeeze', 'sid, not squeeze', 'id in (select id from bugs_rt_affects_unstable) and id not in (select id from bugs_rt_affects_testing)'],
  ['lenny', 'lenny', 'id in (select id from bugs_rt_affects_stable)'],
  ['any', 'any', 'id in (select id from bugs where status!=\'done\')'],
]

FILTERS = [
 ['patch', 'tagged patch', 'id in (select id from bugs_tags where tag=\'patch\')'],
 ['pending', 'tagged pending', 'id in (select id from bugs_tags where tag=\'pending\')'],
 ['security', 'tagged security', 'id in (select id from bugs_tags where tag=\'security\')'],
 ['wontfix', 'tagged wontfix', 'id in (select id from bugs_tags where tag=\'wontfix\')'],
 ['upstream', 'tagged upstream', 'id in (select id from bugs_tags where tag=\'upstream\')'],
 ['unreproducible', 'tagged unreproducible', 'id in (select id from bugs_tags where tag=\'unreproducible\')'],
 ['forwarded', 'forwarded upstream', 'forwarded != \'\''],
 ['claimed', 'claimed bugs', "id in (select id from bugs_usertags where email='bugsquash@qa.debian.org')"],
 ['deferred', 'fixed in deferred/delayed', "id in (select id from deferred_closes)"],
 ['notmain', 'packages not in main', 'id not in (select id from bugs_packages, sources where bugs_packages.source = sources.source and component=\'main\')'],
 ['notsqueeze', 'packages not in squeeze', 'id not in (select id from bugs_packages, sources where bugs_packages.source = sources.source and release=\'squeeze\')'],
 ['base', 'packages in base system', 'bugs.source in (select source from sources where priority=\'required\' or priority=\'important\')'],
 ['standard', 'packages in standard installation', 'bugs.source in (select source from sources where priority=\'standard\')'],
 ['merged', 'merged bugs', 'id in (select id from bugs_merged_with where id > merged_with)'],
 ['done', 'marked as done', 'status = \'done\''],
 ['outdatedsqueeze', 'outdated binaries in squeeze', "bugs.source in (select distinct p1.source from packages_summary p1, packages_summary p2 where p1.source = p2.source and p1.release='squeeze' and p2.release='squeeze' and p1.source_version != p2.source_version)"],
 ['outdatedsid', 'outdated binaries in sid', "bugs.source in (select distinct p1.source from packages_summary p1, packages_summary p2 where p1.source = p2.source and p1.release='sid' and p2.release='sid' and p1.source_version != p2.source_version)"],
 ['needmig', 'different versions in squeeze and sid', "bugs.source in (select s1.source from sources s1, sources s2 where s1.source = s2.source and s1.release = 'squeeze' and s2.release='sid' and s1.version != s2.version)"],
 ['newerubuntu', 'newer in Ubuntu than in sid', "bugs.source in (select s1.source from sources_uniq s1, ubuntu_sources s2 where s1.source = s2.source and s1.release = 'sid' and s2.release='natty' and s1.version < s2.version)"],
]

TYPES = [
  ['rc', 'release-critical bugs', 'severity >= \'serious\'', true ],
  ['ipv6', 'release goal: IPv6 support', 'id in (select id from bugs_tags where tag=\'ipv6\')', false ],
  ['lfs', 'release goal: Large File Support', 'id in (select id from bugs_tags where tag=\'lfs\')', false ],
  ['boot', 'release goal: boot performance (init.d dependencies)', 'id in (select id from bugs_usertags where email = \'initscripts-ng-devel@lists.alioth.debian.org\')', false],
  ['oldgnome', 'release goal: remove obsolete GNOME libraries', 'id in (select id from bugs_usertags where email = \'pkg-gnome-maintainers@lists.alioth.debian.org\' and tag=\'oldlibs\')', false],
  ['ruby', 'Ruby bugs', "bugs.source in (select source from sources where maintainer ~ 'ruby' or uploaders ~ 'ruby')\nOR bugs.package in (select source from packages where (package ~ 'ruby' or depends ~ 'ruby') and source != 'subversion')\nOR title ~ 'ruby'"],
  ['l10n', 'Localisation bugs', 'id in (select id from bugs_tags where tag=\'l10n\')', false],
  ['xsf', 'X Strike Force bugs', "bugs.source in (select source from sources where maintainer ~ 'debian-x@lists.debian.org')\n"],
  ['allbugs', 'All bugs', 'true', false],
]

SORTS = [
  ['id', 'bug#'],
  ['source', 'source package'],
  ['package', 'binary package'],
  ['last_modified', 'last modified'],
  ['severity', 'severity'],
  ['popcon', 'popularity contest'],
]

COLUMNS = [
  ['cpopcon', 'popularity contest'],
  ['chints', 'release team hints'],
  ['cseverity', 'severity'],
  ['ctags', 'tags'],
  ['cclaimed', 'claimed by'],
  ['cdeferred', 'deferred/delayed'],
]

cgi = CGI::new
# releases
if RELEASE_RESTRICT.map { |r| r[0] }.include?(cgi.params['release'][0])
  release = cgi.params['release'][0]
else
  release = 'squeeze'
end
# columns
cols = {}
COLUMNS.map { |r| r[0] }.each do |r|
  if cgi.params[r][0]
    cols[r] = true
  else
    cols[r] = false
  end
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
# hack to enable popcon column if sortby = popcon
cols['cpopcon'] = true if sortby == 'popcon'
cols['cseverity'] = true if sortby == 'severity'
# filters
filters = {}
FILTERS.map { |r| r[0] }.each do |e|
  if ['', 'only', 'ign'].include?(cgi.params[e][0])
    filters[e] = cgi.params[e][0]
  else
    filters[e] = (e == 'merged' ? 'ign' : '')
  end
end
# filter: newer than X days
if ['', 'only', 'ign'].include?(cgi.params['fnewer'][0])
  fnewer = cgi.params['fnewer'][0]
else
  fnewer = ''
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

  body {
    font-family : "DejaVu Sans", "Bitstream Vera Sans", sans-serif;"
  }

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

div#body {
  border-top: 2px solid #d70751;
}

div.footer {
    padding: 0.3em 0;
    background-color: #fff;
    text-align: center;
    border-top: 2px solid #d70751;
    margin: 0 0 0 0;
    border-bottom: 0;
    font-size: 85%;
}
</style>
<title>Debian Bugs Search @ UDD</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
</head>
<body>
<h1 style="margin-bottom : 5px"><img src="http://qa.debian.org/debian.png" alt="Debian logo" width="188" height="52" style="vertical-align : -13px; ">Bugs Search <span style="color :#c70036">@</span> UDD</h1>
<div id="body">

<form action="bugs.cgi" method="get">
<p><b>Bugs affecting:</b>
EOF

RELEASE_RESTRICT.each do |r|
  checked = (release == r[0] ? 'CHECKED=\'1\'':'')
  puts "<input type='radio' name='release' value='#{r[0]}' #{checked}/>#{r[1]}&nbsp;&nbsp;"
end
puts <<-EOF
<br/>(also uses release tags and xxx-ignore information)</p>
<table class="invisible"><tr><td>
<table class="buglist">
<tr><th colspan='4'>FILTERS</th></tr>
<tr><th>not considered</th><th>only</th><th>ignore</th><th>type</th></tr>
EOF
FILTERS.each do |r|
  puts <<-EOF
  <tr>
  <td style='text-align: center;'><input type='radio' name='#{r[0]}' value='' #{filters[r[0]]==''?'CHECKED=\'1\'':''}/></td>
  <td style='text-align: center;'><input type='radio' name='#{r[0]}' value='only' #{filters[r[0]]=='only'?'CHECKED=\'1\'':''}/></td>
  <td style='text-align: center;'><input type='radio' name='#{r[0]}' value='ign' #{filters[r[0]]=='ign'?'CHECKED=\'1\'':''}/></td>
  <td>#{r[1]}</td>
  </tr>
  EOF
end
# newer than
puts <<-EOF
  <tr>
  <td style='text-align: center;'><input type='radio' name='fnewer' value='' #{fnewer==''?'CHECKED=\'1\'':''}/></td>
  <td style='text-align: center;'><input type='radio' name='fnewer' value='only' #{fnewer=='only'?'CHECKED=\'1\'':''}/></td>
  <td style='text-align: center;'><input type='radio' name='fnewer' value='ign' #{fnewer=='ign'?'CHECKED=\'1\'':''}/></td>
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
puts "<br/>\n<b>Additional information:</b> "
COLUMNS.each do |r|
  checked = cols[r[0]] ? 'checked':''
  puts "<input type='checkbox' name='#{r[0]}' value='1' #{checked}/>#{r[1]}&nbsp;&nbsp;"
end
puts <<-EOF
<br/>\n<input type='submit' value='Search'/></p>
</form>
EOF
if cgi.params != {}

# Generate and execute query
tstart = Time::now
dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')
if cols['cpopcon']
  q = "select id, bugs.package, bugs.source, severity, title, last_modified, coalesce(popcon_src.insts, 0) as popcon\nfrom bugs left join popcon_src on (bugs.source = popcon_src.source) \n"
else
  q = "select id, bugs.package, bugs.source, severity, title, last_modified from bugs \n"
end
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
q2 = TYPES.select { |t| types[t[0]] }.map { |t| t[2] }.join("\n OR ")
if q2 != ""
  q += "AND (#{q2})\n"
else
  puts "<p><b>Must select at least one bug type!</b></p>"
  q += "AND FALSE\n"
end
q += "order by #{sortby} #{sorto}"
begin
  sth = dbh.prepare(q)
  sth.execute
  rows = sth.fetch_all
rescue DBI::ProgrammingError => e
  puts "<p>The query generated an error, please report it to lucas@debian.org: #{e.message}</p>"
  puts "<pre>#{q}</pre>"
  exit(0)
end

if cols['chints']
  sthh = dbh.prepare("select distinct source, type, argument, version, file, comment from relevant_hints order by type")
  sthh.execute
  rowsh = sthh.fetch_all
  hints = {}
  rowsh.each do |r|
    hints[r['source']] ||= []
    hints[r['source']] << r
  end
end

if cols['ctags']
  ids = rows.map { |r| r['id'] }.join(',')
  stht = dbh.prepare("select id, tag from bugs_tags where id in (#{ids})")
  stht.execute
  rowst = stht.fetch_all
  tags = {}
  rowst.each do |r|
    tags[r['id']] ||= []
    tags[r['id']] << r['tag']
  end
end

if cols['cclaimed']
  ids = rows.map { |r| r['id'] }.join(',')
  stht = dbh.prepare("select id, tag from bugs_usertags where email='bugsquash@qa.debian.org' and id in (#{ids})")
  stht.execute
  rowst = stht.fetch_all
  claimedbugs = {}
  rowst.each do |r|
    claimedbugs[r['id']] ||= []
    claimedbugs[r['id']] << r['tag']
  end
end

if cols['cdeferred']
  ids = rows.map { |r| r['id'] }.join(',')
  sthd = dbh.prepare("select id, deferred.source, deferred.version, extract (day from delayed_until) as du from deferred, deferred_closes where deferred.source = deferred_closes.source and deferred.version = deferred_closes.version and deferred_closes.id in (#{ids})")
  sthd.execute
  rowsd = sthd.fetch_all
  deferredbugs = {}
  rowsd.each do |r|
    d = r['du'].to_i
    deferredbugs[r['id']] = "#{r['version']} (#{d}&nbsp;day#{d==1?'':'s'})"
  end
end

puts "<p><b>#{rows.length} bugs found.</b></p>"
puts '<table class="buglist">'
puts '<tr><th>bug#</th><th>package</th><th>title</th>'
puts '<th>popcon</th>' if cols['cpopcon']
puts '<th>severity</th>' if cols['cseverity']
puts '<th>hints</th>' if cols['chints']
puts '<th>claimed by</th>' if cols['cclaimed']
puts '<th>deferred</th>' if cols['cdeferred']
puts '<th>last&nbsp;modified</th></tr>'

def genhints(source, hints)
  return '' if hints.nil?
  s = ''
  hints.each do |h|
    v = h['version'] ? h['version'] + ' ' : ''
    t = h['type'] == 'age-days' ? "age/#{h['argument']}" : h['type']
    s += "<a href=\"http://release.debian.org/britney/hints/#{h['file']}\" title=\"#{v}#{h['file']} #{h['comment']}\">#{t}</a> "
  end
  s
end

# copied from /org/bugs.debian.org/etc/config
$TagsSingleLetter = {
  'patch' => '+',
  'wontfix' => '☹',
  'moreinfo' => 'M',
  'unreproducible' => 'R',
  'security' => 'S',
  'pending' => 'P',
  'fixed'   => 'F',
  'help'    => 'H',
  'fixed-upstream' => 'U',
  'upstream' => 'u',
# Added tags
  'confirmed' => 'C',
  'etch-ignore' => 'etc-i',
  'lenny-ignore' => 'len-i',
  'sarge-ignore' => 'sar-i',
  'squeeze-ignore' => 'squ-i',
  'woody' => 'wod',
  'sarge' => 'sar',
  'etch' => 'etc',
  'lenny' => 'len',
  'squeeze' => 'squ',
  'sid' => 'sid',
  'experimental' => 'exp',
  'l10n' => 'l10n',
  'd-i' => 'd-i',
  'ipv6' => 'ipv6',
  'lfs' => 'lfs',
  'fixed-in-experimental' => 'fie',
}

def gentags(tags)
  return '' if tags.nil?
  tags.sort!
  texttags = tags.map do |tag|
    puts "unknowntag: #{tag}" if $TagsSingleLetter[tag].nil?
    "<abbr title='#{tag}'>#{$TagsSingleLetter[tag]}</abbr>"
  end
  return '&nbsp;[' + texttags.join('|') + ']'
end

rows.each do |r|
  print "<tr><td style='text-align: left;'><a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']}</a>"
  puts "#{gentags(tags[r['id']])}" if cols['ctags']
  puts "</td>"
  puts "<td style='text-align: center;'>"
  srcs = r['source'].split(/,\s*/)
  bins = r['package'].split(/,\s*/)
  puts (0...bins.length).map { |i| "<a href=\"http://packages.qa.debian.org/#{srcs[i]}\">#{bins[i]}</a>" }.join(', ')
  puts "</td>"
  puts "<td>#{CGI::escapeHTML(r['title'])}</td>"
  puts "<td>#{r['popcon']}</td>" if cols['cpopcon']
  puts "<td>#{r['severity']}</td>" if cols['cseverity']
  puts "<td>#{genhints(r['source'], hints[r['source']])}</td>" if cols['chints']
  puts "<td>#{claimedbugs[r['id']]}</td>" if cols['cclaimed']
  puts "<td>#{deferredbugs[r['id']]}</td>" if cols['cdeferred']
  puts "<td style='text-align: center;'>#{r['last_modified'].to_date}</td></tr>"
end

puts "</table>"
sth2 = dbh.prepare("select max(start_time) from timestamps where source = 'bugs' and command = 'run'")
sth2.execute ; r2 = sth2.fetch_all
puts "<p><b>Generated in #{Time::now - tstart} seconds. Last data update: #{r2[0][0]}"
puts " (%.1f hours ago)</b></p>" % ((Time::now - r2[0][0].to_time) / 3600)
puts "<pre>#{q}</pre>"
end # if cgi.params != {}
puts <<-EOF
</div>
<div class="footer">
<small>Suggestions / comments / patches to lucas@debian.org. <a href="http://svn.debian.org/wsvn/collab-qa/udd/web/bugs.cgi">source code</a>.</small>
</div>
</body>
</html>
EOF
