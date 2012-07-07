#!/usr/bin/ruby

require 'cgi'

STDERR.reopen(STDOUT) # makes live debugging much easier
puts "Content-type: text/html\n\n"

require File.expand_path(File.dirname(__FILE__))+'/inc/dmd-data'

cgi = CGI::new

tstart = Time::now

puts <<-EOF
<html>
<head>
<style type="text/css" rel="stylesheet">
@import "css/dmd.css";
@import "css/jquery-ui-1.8.21.custom.css";
</style>
<title>Debian Maintainer Dashboard @ UDD</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<script type="text/javascript" src="js/jquery.min.js"></script>
<script type="text/javascript" src="js/jquery.tablesorter.min.js"></script>
<script type="text/javascript" src="js/jquery-ui.custom.min.js"></script>
<script>
$(function() {
  $( "#tabs" ).tabs();
  $( "#email" ).autocomplete({
    source: "cgi-bin/maintainers.cgi",
    select: function(event, ui) {
        $("#email").val(ui.item.value);
        $("#searchForm").submit();
    }
  });
});
</script>
</head>
<body>
<h1 style="margin-bottom : 5px"><img src="http://qa.debian.org/debian.png" alt="Debian logo" width="188" height="52" style="vertical-align : -13px; ">Maintainer Dashboard <span style="color :#c70036">@</span> UDD</h1>
<div id="body">
<br/>
<form id="searchForm" action="dmd.cgi" method="get">
email: <input id="email" type='text' size='100' name='email' value='pkg-ruby-extras-maintainers@lists.alioth.debian.org'/>
<input type='submit' value='Go'/>
</form>
EOF

if cgi.params != {}
  emails = { cgi.params['email'][0] => [:maintainer, :uploader]}
  uddd = UDDData::new(emails)
  uddd.get_sources
  uddd.get_sources_status
  uddd.get_dmd_todos
  uddd.get_ubuntu_bugs

  puts <<-EOF
<div id="tabs">
	<ul>
		<li><a href="#tabs-todo">TODO list</a></li>
		<li><a href="#tabs-versions">Versions</a></li>
		<li><a href="#tabs-bugs">Bugs</a></li>
		<li><a href="#tabs-ubuntu">Ubuntu</a></li>
	</ul>
	<div id="tabs-todo">
<table class="buglist">
<tr>
<th>type</th><th>source</th><th>description</th>
</tr>
  EOF
  uddd.dmd_todos.each do |t|
    puts "<tr><td>#{t[:type]}</td><td>#{t[:source]}</td><td>#{t[:description]}</td></tr>"
  end
  puts "</table>"
  puts "</div>" # tabs-todo

	puts '<div id="tabs-versions">'

  puts <<-EOF
<table class="buglist">
<tr>
<th>source</th><th>squeeze</th><th>wheezy</th><th>sid</th><th>experimental</th>
<th>upstream</th><th>vcs</th>
</tr>
  EOF
  uddd.sources.keys.sort.each do |src|
    next if not uddd.versions.include?(src)
    next if not uddd.versions[src].include?('debian')
    dv = uddd.versions[src]['debian']
    puts "<tr><td>#{src}</td>"

    puts "<td>"
    puts dv['squeeze'][:version] if dv['squeeze']
    puts "<br>sec: #{dv['squeeze-security'][:version]}" if dv['squeeze-security']
    puts "<br>pu: #{dv['squeeze-proposed-updates'][:version]}" if dv['squeeze-proposed-updates']
    puts "<br>bpo: #{dv['squeeze-backports'][:version]}" if dv['squeeze-backports']
    puts "</td>"

    puts "<td>"
    puts dv['wheezy'][:version] if dv['wheezy']
    puts "<br>sec: #{dv['wheezy-security'][:version]}" if dv['wheezy-security']
    puts "<br>pu: #{dv['wheezy-proposed-updates'][:version]}" if dv['wheezy-proposed-updates']
    puts "</td>"

    puts "<td>"
    puts dv['sid'][:version] if dv['sid']
    puts "</td>"

    puts "<td>"
    puts dv['experimental'][:version] if dv['experimental']
    puts "</td>"

    up = uddd.versions[src]['upstream']
    puts "<td>"
    puts "#{up[:version]} (#{up[:status]})" if up
    puts "</td>"

    vcs = uddd.versions[src]['vcs']
    puts "<td>"
    # FIXME show status
    puts "#{vcs[:version]}" if vcs
    puts "</td>"

    puts "</tr>"
  end

  puts <<-EOF
</table>
</div>
<div id="tabs-bugs">
<table class="buglist">
<tr>
<th>source</th><th>all</th><th>RC</th><th>with patch</th><th>pending</th>
</tr>
  EOF
  bc = uddd.bugs_count
  bc.keys.sort.each do |src|
    b = bc[src]
    next if b[:all] == 0
    puts "<tr><td>#{src}</td><td>#{b[:all]}</td><td>#{b[:rc]}</td><td>#{b[:patch]}</td><td>#{b[:pending]}</td></tr>"
  end
  puts "</table>"
  puts "</div>"

  puts '<div id="tabs-ubuntu">'

  puts <<-EOF
<table class="buglist">
<tr>
<th>source</th><th>sid</th><th>precise (stable)</th><th>quantal (devel)</th><th>bugs (patches)</th>
</tr>
  EOF
  uddd.sources.keys.sort.each do |src|
    next if not uddd.versions.include?(src)
    next if (not uddd.versions[src].include?('debian') or not uddd.versions[src].include?('ubuntu'))
    dv = uddd.versions[src]['debian']
    puts "<tr><td>#{src}</td>"

    puts "<td>"
    puts dv['sid'][:version] if dv['sid']
    puts "</td>"

    du = uddd.versions[src]['ubuntu']
    if du.nil?
      puts "<td></td><td></td>"
    else
      puts "<td>"
      puts du['precise'][:version] if du['precise']
      puts "</td>"

      puts "<td>"
      puts du['quantal'][:version] if du['quantal']
      puts "</td>"
    end

    ub = uddd.ubuntu_bugs[src]
    if ub.nil?
      bugs = 0
      patches = 0
    else
      bugs = ub[:bugs]
      patches = ub[:patches]
    end
    puts "<td>"
    puts "#{bugs} (#{patches})"
    puts "</td>"

    puts "</tr>"
  end

  puts <<-EOF
</table>
</div>
  EOF

  puts "</div>" # div#tabs
  puts "<p><b>Generated in #{Time::now - tstart} seconds.</b></p>"

end # cgi.params

puts <<-EOF
<div class="footer">
<small>Suggestions / comments / patches to lucas@debian.org. <a href="hacking.html">
source code</a>.</small>
</div>
</body></html>
EOF

