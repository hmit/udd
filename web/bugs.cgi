#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
require 'cgi'
require 'time'

puts "Content-type: text/html\n\n"

RELEASE_RESTRICT = [
  ['wheezy', 'wheezy', 'id in (select id from bugs_rt_affects_testing)'],
  ['sid', 'sid', 'id in (select id from bugs_rt_affects_unstable)'],
  ['wheezy_and_sid', 'wheezy and sid', 'id in (select id from bugs_rt_affects_testing) and id in (select id from bugs_rt_affects_unstable)'],
  ['wheezy_or_sid', 'wheezy or sid', 'id in (select id from bugs_rt_affects_testing union select id from bugs_rt_affects_unstable)'],
  ['wheezy_not_sid', 'wheezy, not sid', 'id in (select id from bugs_rt_affects_testing) and id not in (select id from bugs_rt_affects_unstable)'],
  ['sid_not_wheezy', 'sid, not wheezy', 'id in (select id from bugs_rt_affects_unstable) and id not in (select id from bugs_rt_affects_testing)'],
  ['squeeze', 'squeeze', 'id in (select id from bugs_rt_affects_stable)'],
  ['lenny', 'lenny', 'id in (select id from bugs_rt_affects_oldstable)'],
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
 ['notwheezy', 'packages not in wheezy', 'id not in (select id from bugs_packages, sources where bugs_packages.source = sources.source and release=\'wheezy\')'],
 ['base', 'packages in base system', 'bugs.source in (select source from sources where priority=\'required\' or priority=\'important\')'],
 ['standard', 'packages in standard installation', 'bugs.source in (select source from sources where priority=\'standard\')'],
 ['orphaned', 'orphaned packages', 'bugs.source in (select source from orphaned_packages where type in (\'ITA\', \'O\'))'],
 ['merged', 'merged bugs', 'id in (select id from bugs_merged_with where id > merged_with)'],
 ['done', 'marked as done', 'status = \'done\''],
 ['outdatedwheezy', 'outdated binaries in wheezy', "bugs.source in (select distinct p1.source from packages_summary p1, packages_summary p2 where p1.source = p2.source and p1.release='wheezy' and p2.release='wheezy' and p1.source_version != p2.source_version)"],
 ['outdatedsid', 'outdated binaries in sid', "bugs.source in (select distinct p1.source from packages_summary p1, packages_summary p2 where p1.source = p2.source and p1.release='sid' and p2.release='sid' and p1.source_version != p2.source_version)"],
 ['needmig', 'different versions in wheezy and sid', "bugs.source in (select s1.source from sources s1, sources s2 where s1.source = s2.source and s1.release = 'wheezy' and s2.release='sid' and s1.version != s2.version)"],
 ['newerubuntu', 'newer in Ubuntu than in sid', "bugs.source in (select s1.source from sources_uniq s1, ubuntu_sources s2 where s1.source = s2.source and s1.release = 'sid' and s2.release='precise' and s1.version < s2.version)"],
 ['rtwheezy-will-remove', 'RT tag for wheezy: will-remove', "id in (select id from bugs_usertags where email='release.debian.org@packages.debian.org' and tag='wheezy-will-remove')"],
 ['rtwheezy-can-defer', 'RT tag for wheezy: can-defer', "id in (select id from bugs_usertags where email='release.debian.org@packages.debian.org' and tag='wheezy-can-defer')"],
 ['rtwheezy-is-blocker', 'RT tag for wheezy: is-blocker', "id in (select id from bugs_usertags where email='release.debian.org@packages.debian.org' and tag='wheezy-is-blocker')"],
]

TYPES = [
  ['rc', 'release-critical bugs', 'severity >= \'serious\'', true ],
  ['ipv6', 'release goal: IPv6 support', 'id in (select id from bugs_tags where tag=\'ipv6\')', false ],
  ['lfs', 'release goal: Large File Support', 'id in (select id from bugs_tags where tag=\'lfs\')', false ],
  ['boot', 'release goal: boot performance (init.d dependencies)', 'id in (select id from bugs_usertags where email = \'initscripts-ng-devel@lists.alioth.debian.org\')', false],
  ['oldgnome', 'release goal: remove obsolete GNOME libraries', 'id in (select id from bugs_usertags where email = \'pkg-gnome-maintainers@lists.alioth.debian.org\' and tag=\'oldlibs\')', false],
  ['ruby', 'Ruby bugs', "bugs.source in (select source from sources where maintainer ~ 'ruby' or uploaders ~ 'ruby')\nOR bugs.package in (select source from packages where (package ~ 'ruby' or depends ~ 'ruby') and source != 'subversion')\nOR title ~ 'ruby'"],
  ['php', 'PHP bugs', "bugs.source in (select source from packages_summary where package in (select package from debtags where tag = 'implemented-in::php'))"],
  ['l10n', 'Localisation bugs', 'id in (select id from bugs_tags where tag=\'l10n\')', false],
  ['xsf', 'X Strike Force bugs', "bugs.source in (select source from sources where maintainer ~ 'debian-x@lists.debian.org')\n"],
  ['kfreebsd', 'GNU/kFreeBSD bugs', 'id in (select id from bugs_usertags where email = \'debian-bsd@lists.debian.org\' and tag=\'kfreebsd\')', false],
  ['hurd', 'GNU/Hurd bugs', 'id in (select id from bugs_usertags where email = \'debian-hurd@lists.debian.org\' and tag=\'hurd\')', false],
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
  ['cpopcon', 'popularity&nbsp;contest'],
  ['chints', 'release&nbsp;team&nbsp;hints'],
  ['cseverity', 'severity'],
  ['ctags', 'tags'],
  ['cclaimed', 'claimed&nbsp;by'],
  ['cdeferred', 'deferred/delayed'],
  ['caffected', 'affected&nbsp;releases'],
  ['crttags', 'release&nbsp;team&nbsp;tags&nbsp;for&nbsp;wheezy'],
]

cgi = CGI::new
# releases
if RELEASE_RESTRICT.map { |r| r[0] }.include?(cgi.params['release'][0])
  release = cgi.params['release'][0]
else
  release = 'wheezy'
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
<script type="text/javascript" src="js/jquery.min.js"></script>
<script type="text/javascript" src="js/jquery.tablesorter.min.js"></script>
<style type="text/css">

  body {
    font-family : "DejaVu Sans", "Bitstream Vera Sans", "sans-serif;"
  }

  table.buglist td, table.buglist th {
    border: 1px solid gray;
    padding-left: 3px;
    padding-right: 3px;
  }
  table.buglist tr:hover  {
    background-color: #ccc;
    color: #000;
  }
  table.buglist tr:hover :link {
    color: #00f;
  }
  table.buglist tr:hover :visited {
    color: #707;
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
    color: #000;
    text-align: center;
    border-top: 2px solid #d70751;
    margin: 0 0 0 0;
    border-bottom: 0;
    font-size: 85%;
}
  div.footer :link {
    color: #00f;
  }
  div.footer :visited {
    color: #707;
  }

  /* tablesorter */
table.tablesorter thead tr .header {
	text-align: left;
	background-image: url(images/tablesorter/bg.gif);
	background-repeat: no-repeat;
	background-position: center right;
	cursor: pointer;
}
table.tablesorter thead tr .headerSortUp {
	background-image: url(images/tablesorter/asc.gif);
}
table.tablesorter thead tr .headerSortDown {
	background-image: url(images/tablesorter/desc.gif);
}
table.tablesorter thead tr .headerSortDown, table.tablesorter thead tr .headerSortUp {
    background-color: #ddd;
}
</style>
<title>Debian Bugs Search @ UDD</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<script type="text/javascript">
function removeBlankFields(form) {
	var inputs = form.getElementsByTagName("input");
	var removeList = new Array();
	for (var i=0; i<inputs.length; i++) {
		if (inputs[i].value == "") {
			removeList.push(inputs[i]);
		}
	}
	for (x in removeList) {
		removeList[x].parentNode.removeChild(removeList[x]);
	}
}
</script>
</head>
<body>
<h1 style="margin-bottom : 5px"><img src="http://qa.debian.org/debian.png" alt="Debian logo" width="188" height="52" style="vertical-align : -13px; ">Bugs Search <span style="color :#c70036">@</span> UDD</h1>
<div id="body">

<form action="bugs.cgi" method="get" onsubmit="removeBlankFields(this);">
<p><b>Bugs affecting:</b>
EOF

RELEASE_RESTRICT.each do |r|
  checked = (release == r[0] ? 'CHECKED=\'1\'':'')
  puts "<label><input type='radio' name='release' value='#{r[0]}' #{checked}/>#{r[1]}</label>&nbsp;&nbsp;"
end
puts <<-EOF
<br/>(This already uses release tags ('sid', 'wheezy') and xxx-ignore ('wheezy-ignore') to include/exclude bugs)</p>
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
  puts "<tr><td><input type='checkbox' id='#{t[0]}' name='#{t[0]}' value='1'#{checked}/></td><td><label for='#{t[0]}'>#{t[1]}</label></td></tr>"
end
puts "</table></td></tr></table>"
puts "<p><b>Sort by:</b> "
SORTS.each do |r|
  checked = (sortby == r[0] ? 'CHECKED=\'1\'':'')
  puts "<label><input type='radio' name='sortby' value='#{r[0]}' #{checked}/>#{r[1]}</label>&nbsp;&nbsp;"
end
puts "<b> -- </b>"
[['asc', 'increasing'],[ 'desc', 'decreasing']].each do |r|
  checked = (sorto == r[0] ? 'CHECKED=\'1\'':'')
  puts "<label><input type='radio' name='sorto' value='#{r[0]}' #{checked}/>#{r[1]}</label>&nbsp;&nbsp;"
end
puts "<br/>\n<b>Additional information:</b> "
COLUMNS.each do |r|
  checked = cols[r[0]] ? 'checked':''
  puts "<label><input type='checkbox' name='#{r[0]}' value='1' #{checked}/>#{r[1]}</label>&nbsp;&nbsp;"
end
puts <<-EOF
<br/>\n<input type='submit' value='Search'/></p>
</form>
EOF
if cgi.params != {}

# Generate and execute query
tstart = Time::now
dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
dbh.execute("SET statement_timeout TO 90000")
if cols['cpopcon']
  q = "select id, bugs.package, bugs.source, severity, title, last_modified, affects_stable, affects_testing, affects_unstable, affects_experimental, coalesce(popcon_src.insts, 0) as popcon\nfrom bugs left join popcon_src on (bugs.source = popcon_src.source) \n"
else
  q = "select id, bugs.package, bugs.source, severity, title, last_modified, affects_stable, affects_testing, affects_unstable, affects_experimental from bugs \n"
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

load = IO::read('/proc/loadavg').split[1].to_f
if load > 20
  puts "<p><b>Current system load (#{load}) is too high. Please retry later!</b></p>"
  puts "<pre>#{q}</pre>"
  exit(0)
end

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
  sthh = dbh.prepare("select id, title from bugs where source='release.debian.org' and status='pending' and title ~ '^unblock'")
  sthh.execute
  rowsh = sthh.fetch_all
  unblockreq = {}
  ids = []
  rowsh.each do |r|
    src = r['title'].split(" ")[1].split('/')[0]
    unblockreq[src] ||= []
    unblockreq[src] << r['id']
    ids << r['id']
  end
  ids = ids.join(',')
  stht = dbh.prepare("select id, tag from bugs_tags where id in (#{ids})")
  stht.execute
  rowst = stht.fetch_all
  unblockreqtags = {}
  rowst.each do |r|
    unblockreqtags[r['id']] ||= []
    unblockreqtags[r['id']] << r['tag']
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
  stht = dbh.prepare("select distinct id, tag from bugs_usertags where email='bugsquash@qa.debian.org' and id in (#{ids})")
  stht.execute
  rowst = stht.fetch_all
  claimedbugs = {}
  rowst.each do |r|
    claimedbugs[r['id']] ||= []
    claimedbugs[r['id']] << r['tag']
  end
end

if cols['crttags']
  ids = rows.map { |r| r['id'] }.join(',')
  stht = dbh.prepare("select distinct id, tag from bugs_usertags where email='release.debian.org@packages.debian.org' and id in (#{ids})")
  stht.execute
  rowst = stht.fetch_all
  rttags = {}
  rowst.each do |r|
    rttags[r['id']] ||= []
    rttags[r['id']] << r['tag']
  end
end


if cols['cdeferred']
  ids = rows.map { |r| r['id'] }.join(',')
  sthd = dbh.prepare("select id, deferred.source, deferred.version, extract (day from delay_remaining) as du from deferred, deferred_closes where deferred.source = deferred_closes.source and deferred.version = deferred_closes.version and deferred_closes.id in (#{ids})")
  sthd.execute
  rowsd = sthd.fetch_all
  deferredbugs = {}
  rowsd.each do |r|
    d = r['du'].to_i
    deferredbugs[r['id']] = "#{r['version']} (#{d}&nbsp;day#{d==1?'':'s'})"
  end
end

puts "<p><b>#{rows.length} bugs found.</b></p>"
puts '<table class="buglist tablesorter">'
puts '<thead>'
puts '<tr><th>bug#</th><th>package</th><th>title</th>'
puts '<th>popcon</th>' if cols['cpopcon']
puts '<th>severity</th>' if cols['cseverity']
puts '<th>hints</th>' if cols['chints']
puts '<th>claimed by</th>' if cols['cclaimed']
puts '<th>deferred</th>' if cols['cdeferred']
puts '<th>RT tag</th>' if cols['crttags']
puts '<th>last&nbsp;modified</th></tr>'
puts '</thead>'
puts '<tbody>'

def genhints(source, hints, unblockreq, tags)
  s = ''
  if not hints.nil?
    hints.each do |h|
      v = h['version'] ? h['version'] + ' ' : ''
      t = h['type'] == 'age-days' ? "age/#{h['argument']}" : h['type']
      s += "<a href=\"http://release.debian.org/britney/hints/#{h['file']}\" title=\"#{v}#{h['file']} #{h['comment']}\">#{t}</a> "
    end
  end
  if not unblockreq.nil?
    unblockreq.each do |u|
      s += "req:<a href=\"http://bugs.debian.org/#{u}\">##{u}</a>#{gentags(tags[u])} "
    end
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
  'wheezy-ignore' => 'whe-i',
  'woody' => 'wod',
  'sarge' => 'sar',
  'etch' => 'etc',
  'lenny' => 'len',
  'squeeze' => 'squ',
  'wheezy' => 'whe',
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

def genaffected(r)
  s = ""
  s += "<abbr title='affects stable'>S</abbr>" if r['affects_stable']
  s += "<abbr title='affects testing'>T</abbr>" if r['affects_testing']
  s += "<abbr title='affects unstable'>U</abbr>" if r['affects_unstable']
  s += "<abbr title='affects unstable'>E</abbr>" if r['affects_experimental']
  return "" if s == ""
  return "&nbsp;("+s+")"
end

rows.each do |r|
  print "<tr><td style='text-align: left;'><a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']}</a>"
  puts "#{gentags(tags[r['id']])}" if cols['ctags']
  puts "#{genaffected(r)}" if cols['caffected']
  puts "</td>"
  puts "<td style='text-align: center;'>"
  srcs = r['source'].split(/,\s*/)
  bins = r['package'].split(/,\s*/)
  puts (0...bins.length).map { |i| "<a href=\"http://packages.qa.debian.org/#{srcs[i]}\">#{bins[i]}</a>" }.join(', ')
  puts "</td>"
  puts "<td>#{CGI::escapeHTML(r['title'])}</td>"
  puts "<td>#{r['popcon']}</td>" if cols['cpopcon']
  puts "<td>#{r['severity']}</td>" if cols['cseverity']
  puts "<td>#{genhints(r['source'], hints[r['source']], unblockreq[r['source']], unblockreqtags)}</td>" if cols['chints']
  puts "<td>#{claimedbugs[r['id']]}</td>" if cols['cclaimed']
  puts "<td>#{deferredbugs[r['id']]}</td>" if cols['cdeferred']
  puts "<td>#{rttags[r['id']]}</td>" if cols['crttags']
  d = r['last_modified']
  d = Date::new(d.year, d.month, d.day)
  puts "<td style='text-align: center;'>#{d}</td></tr>"
end

puts "</tbody></table>"
sth2 = dbh.prepare("select max(start_time) from timestamps where source = 'bugs' and command = 'run'")
sth2.execute ; r2 = sth2.fetch_all
puts "<p><b>Generated in #{Time::now - tstart} seconds. Last data update: #{r2[0][0]}"
puts " (%.1f hours ago)</b></p>" % ((Time::now - Time::parse(r2[0][0].to_s)) / 3600)
puts "<pre>#{q}</pre>"
end # if cgi.params != {}
puts <<-EOF
</div>
<p><b>Useful queries:</b>
<ul>
<li><a href="bugs.cgi?release=wheezy_and_sid&patch=ign&merged=ign&done=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&ctags=1&cdeferred=1"><b>Bug squasher view:</b> Affecting sid and wheezy, not marked as done, not tagged patch; those need to be fixed, probably by a patch+upload</a></li>
<li><a href="bugs.cgi?release=wheezy_and_sid&patch=only&merged=ign&done=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1"><b>Sponsor view:</b> Affecting sid and wheezy, not marked as done, tagged 'patch'; those need a DD to sponsor an upload</a></li>
<li><a href="bugs.cgi?release=wheezy_and_sid&merged=ign&done=only&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&cdeferred=1"><b>Cleaner view:</b> Affecting sid and wheezy, but marked as done; why is it still affecting unstable? missing binaries? wrong changelog?</a></li>
<li><a href="bugs.cgi?release=wheezy_not_sid&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1&crttags=1"><b>Release Team view:</b> Affecting wheezy, but not sid. Help the fix migrate to wheezy!</a></li>
</ul>

<div class="footer">
<small>Suggestions / comments / patches to lucas@debian.org. <a href="http://svn.debian.org/wsvn/collab-qa/udd/web/bugs.cgi">source code</a>.</small>
</div>
</body>
</html>
<script type="text/javascript">
$(document).ready(function() {
$("table.tablesorter").tablesorter();
});
</script>
EOF
