#!/usr/bin/ruby
# encoding: utf-8

require 'dbi'
require 'pp'
require 'cgi'
require 'time'
require 'yaml'

#STDERR.reopen(STDOUT)

puts "Content-type: text/html\n\n"

RELEASE_RESTRICT = [
  ['wheezy', 'wheezy'], 
  ['jessie', 'jessie'], 
  ['sid', 'sid'], 
  ['squeeze', 'squeeze'], 
  ['any', 'any'], 
]

BUGTYPES = [
  ['unarchived', 'unarchived bugs'],
  ['archived', 'archived bugs'],
  ['both', 'both'],
]

SORTS = [
  ['source', 'source package'],
  ['maintainer_name', 'maintainer'],
  ['popcon', 'popularity contest'],
  ['firstupload', 'first upload in debian'],
  ['lastupload', 'last upload in debian'],
]

COLUMNS = [
  ['cpopcon', 'popularity&nbsp;contest'],
  ['firstupload', 'first upload in debian'],
  ['lastupload', 'last upload in debian'],
]

cgi = CGI::new
# releases
if RELEASE_RESTRICT.map { |r| r[0] }.include?(cgi.params['release'][0])
  release = cgi.params['release'][0]
else
  release = 'wheezy'
end
# bugtypes
if BUGTYPES.map { |r| r[0] }.include?(cgi.params['bugtypes'][0])
  bugtypes = cgi.params['bugtypes'][0]
else
  bugtypes = 'both'
end
archived = true
unarchived = true
if bugtypes == "archived"
  unarchived = false
elsif bugtypes == "unarchived"
  archived = false
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
  sortby = 'source'
end
if ['asc', 'desc'].include?(cgi.params['sorto'][0])
  sorto = cgi.params['sorto'][0]
else
  sorto = 'asc'
end
# hack to enable popcon column if sortby = popcon
cols['cpopcon'] = true if sortby == 'popcon'
cols['firstupload'] = true if sortby == 'firstupload'
cols['lastupload'] = true if sortby == 'lastupload'

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

<form action="nobugs.cgi" method="get" onsubmit="removeBlankFields(this);">
EOF

puts "<p><b>Packages in:</b>"
RELEASE_RESTRICT.each do |r|
  checked = (release == r[0] ? 'CHECKED=\'1\'':'')
  puts "<label><input type='radio' name='release' value='#{r[0]}' #{checked}/>#{r[1]}</label>&nbsp;&nbsp;"
end
puts "<br/>"

puts "<p><b>Show packages having no bugs of type:</b>"
BUGTYPES.each do |r|
  checked = (bugtypes == r[0] ? 'CHECKED=\'1\'':'')
  puts "<label><input type='radio' name='bugtypes' value='#{r[0]}' #{checked}/>#{r[1]}</label>&nbsp;&nbsp;"
end
puts "<br/>"

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

puts "<p>\n<b>Additional information:</b> "
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

q = "select sources.source, min(sources.maintainer_name) as maintainer_name, min(sources.maintainer_email) as maintainer_email "

if cols['cpopcon'] == true
  q += ", coalesce(max(popcon_src.insts), 0) as popcon "
end

if cols['firstupload'] == true
  q += ", min(upload_history.date) as firstupload "
end

if cols['lastupload'] == true
  q += ", max(upload_history.date) as lastupload "
end

q += "\nfrom sources "

if cols['cpopcon'] == true
  q += " left join popcon_src on (sources.source = popcon_src.source) \n"
end

if cols['firstupload'] == true || cols['lastupload'] == true
  q += " left join upload_history on (sources.source = upload_history.source) \n"
end


if unarchived
  q += " left join bugs on sources.source = bugs.source \n"
end

if archived
  q += " left join archived_bugs on sources.source = archived_bugs.source \n"
end

where = false
if release != "any"
  q += "where sources.release = '#{release}' "
  where = true
end

if unarchived
  if where
    q += " and "
  else
  	q += " where "
	where = true
  end
  q += " bugs.source is null "
end

if archived
  if where
    q += " and "
  else
  	q += " where "
	where = true
  end
  q += " archived_bugs.source is null "
end

q += " group by sources.source "
q += " order by #{sortby} #{sorto}\n"


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

puts "<p><b>#{rows.length} packages found.</b></p>"

if rows.length > 0

  puts '<table class="buglist tablesorter">'
  puts '<thead>'
  puts '<tr><th>package</th>'
  puts '<th>maintainer</th>'
  puts '<th>popcon</th>' if cols['cpopcon']
  puts '<th>first upload</th>' if cols['firstupload']
  puts '<th>last upload</th>' if cols['lastupload']
  puts '</thead>'
  puts '<tbody>'

  rows.each do |r|
    print "<tr>"
	print "<td><a href=\"http://tracker.debian.org/#{r['source']}\">#{r['source']}</a></td>"
	print "<td><a href=\"http://qa.debian.org/developer.php?login=#{r['maintainer_email']}\">#{r['maintainer_name']}</a></td>"
    puts "<td>#{r['popcon']}</td>" if cols['cpopcon']
	if cols['firstupload']
	  if r['firstupload']
	  then
        d = r['firstupload']
        d = Date::new(d.year, d.month, d.day)
        puts "<td>#{d}</td>"
	  else
	    puts "<td></td>"
	  end
	end
	if cols['lastupload']
	  if r['lastupload']
	  then
        d = r['lastupload']
        d = Date::new(d.year, d.month, d.day)
        puts "<td>#{d}</td>"
	  else
	    puts "<td></td>"
	  end
	end
	puts "</tr>"
  end

  puts "</tbody></table>"
end

sth2 = dbh.prepare("select max(start_time) from timestamps where source = 'bugs' and command = 'run'")
sth2.execute ; r2 = sth2.fetch_all
puts "<p><b>Generated in #{Time::now - tstart} seconds. Last data update: #{r2[0][0]}"
puts " (%.1f hours ago)</b></p>" % ((Time::now - Time::parse(r2[0][0].to_s)) / 3600)
puts "<pre>#{q}</pre>"
end # if cgi.params != {}
puts <<-EOF
</div>

<div class="footer">
<small><a href="https://wiki.debian.org/UltimateDebianDatabase/Hacking">hacking / bug reporting / contact information</a> - <a href="http://anonscm.debian.org/gitweb/?p=collab-qa/udd.git;a=blob_plain;f=web/bugs.cgi">source code</a></small>
</div>
</body>
</html>
<script type="text/javascript">
$(document).ready(function() {
$("table.tablesorter").tablesorter();
});
</script>
EOF
