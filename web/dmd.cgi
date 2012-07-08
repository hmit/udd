#!/usr/bin/ruby

require 'cgi'

STDERR.reopen(STDOUT) # makes live debugging much easier
puts "Content-type: text/html\n\n"

require File.expand_path(File.dirname(__FILE__))+'/inc/dmd-data'

cgi = CGI::new

tstart = Time::now

default_email = 'pkg-ruby-extras-maintainers@lists.alioth.debian.org'
if cgi.params['email'][0]
  default_email = cgi.params['email'][0]
end

default_email = CGI.escapeHTML(default_email)

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
    source: "dmd-emails.cgi",
    select: function(event, ui) {
        $("#email").val(ui.item.value);
        $("#searchForm").submit();
    }
  });
});
$(document).ready(function() {
$("table.tablesorter").each(function(index) { $(this).tablesorter() });
});
</script>
</head>
<body>
<h1 style="margin-bottom : 5px"><img src="http://qa.debian.org/debian.png" alt="Debian logo" width="188" height="52" style="vertical-align : -13px; ">Maintainer Dashboard <span style="color :#c70036">@</span> UDD</h1>
<div id="body">
<br/>
<form id="searchForm" action="dmd.cgi" method="get">
email: <input id="email" type='text' size='100' name='email' value='#{default_email}'/>
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
<table class="buglist tablesorter">
<thead>
<tr>
<th>type</th><th>source</th><th>description</th>
</tr>
</thead><tbody>
  EOF
  uddd.dmd_todos.each do |t|
    puts "<tr><td>#{t[:type]}</td><td class=\"left\">#{t[:source]}</td><td class=\"left\">#{t[:description]}</td></tr>"
  end
  puts "</tbody></table>"
  puts "</div>" # tabs-todo

	puts '<div id="tabs-versions">'

  puts <<-EOF
<table class="buglist tablesorter">
<thead>
<tr>
<th>source</th><th>squeeze</th><th>wheezy</th><th>sid</th><th>experimental</th>
<th>upstream</th><th>vcs</th>
</tr>
</thead>
<tbody>
  EOF
  uddd.sources.keys.sort.each do |src|
    next if not uddd.versions.include?(src)
    next if not uddd.versions[src].include?('debian')
    dv = uddd.versions[src]['debian']
    puts "<tr><td class=\"left\">#{src}</td>"

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
</tbody>
</table>
</div>
<div id="tabs-bugs">
<table class="buglist tablesorter">
<thead>
<tr>
<th>&nbsp;&nbsp;&nbsp;&nbsp;source&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;all&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;RC&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;with patch&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;pending&nbsp;&nbsp;&nbsp;&nbsp;</th>
</tr>
</thead>
<tbody>
  EOF
  bc = uddd.bugs_count
  bc.keys.sort.each do |src|
    b = bc[src]
    next if b[:all] == 0
    puts "<tr><td class=\"left\">#{src}</td><td>#{b[:all] > 0 ? b[:all] : ''}</td><td>#{b[:rc] > 0 ? b[:rc] : ''}</td><td>#{b[:patch] > 0 ? b[:patch] : ''}</td><td>#{b[:pending] > 0 ? b[:pending] : ''}</td></tr>"
  end
  puts "</tbody></table>"
  puts "</div>"

  puts '<div id="tabs-ubuntu">'

  puts <<-EOF
<table class="buglist tablesorter">
<thead>
<tr>
<th>source</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;bugs&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;patches&nbsp;&nbsp;&nbsp;&nbsp;</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;precise (stable)&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;quantal (devel)&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;sid&nbsp;&nbsp;&nbsp;&nbsp;</th>
</tr>
</thead>
<tbody>
  EOF
  USTB='precise'
  UDEV='quantal'
  uddd.sources.keys.sort.each do |src|
    next if not uddd.versions.include?(src)
    next if (not uddd.versions[src].include?('debian') or not uddd.versions[src].include?('ubuntu'))
    puts "<tr><td class=\"left\">#{src}</td>"

    ub = uddd.ubuntu_bugs[src]
    if ub.nil?
      bugs = 0
      patches = 0
    else
      bugs = ub[:bugs]
      patches = ub[:patches]
    end

    dv = uddd.versions[src]['debian']
    if dv['sid']
      sid = dv['sid'][:version]
    else
      sid = ''
    end

    du = uddd.versions[src]['ubuntu']
    ustb = ''
    udev = ''
    if not du.nil?
      ustb = du[USTB][:version] if du[USTB]
      ustb += "<br>sec:&nbsp;#{du["#{USTB}-security"][:version]}" if du["#{USTB}-security"]
      ustb += "<br>upd:&nbsp;#{du["#{USTB}-updates"][:version]}" if du["#{USTB}-updates"]
      ustb += "<br>prop:&nbsp;#{du["#{USTB}-proposed"][:version]}" if du["#{USTB}-proposed"]
      ustb += "<br>bpo:&nbsp;#{du["#{USTB}-backports"][:version]}" if du["#{USTB}-backports"]

      udev = du[UDEV][:version] if du[UDEV]
      if udev != sid and sid != ''
        if UDDData.compare_versions(udev, sid) == -1
          if udev =~ /ubuntu/
            udev = "<span class=\"prio_high\" title=\"Outdated version in Ubuntu, with an Ubuntu patch\">#{udev}</span>"
          else
            udev = "<span class=\"prio_med\" title=\"Outdated version in Ubuntu\">#{udev}</span>"
          end
        elsif UDDData.compare_versions(udev, sid) == 1
          udevnb = udev.gsub(/build\d+$/,'')
          if UDDData.compare_versions(udevnb, sid) == 1
            udev = "<span class=\"prio_high\" title=\"Newer version in Ubuntu\">#{udev}</span>"
          end
        end
      end
      udev += "<br>sec:&nbsp;#{du["#{UDEV}-security"][:version]}" if du["#{UDEV}-security"]
      udev += "<br>upd:&nbsp;#{du["#{UDEV}-updates"][:version]}" if du["#{UDEV}-updates"]
      udev += "<br>prop:&nbsp;#{du["#{UDEV}-proposed"][:version]}" if du["#{UDEV}-proposed"]
      udev += "<br>bpo:&nbsp;#{du["#{UDEV}-backports"][:version]}" if du["#{UDEV}-backports"]
    end

    puts "<td>#{bugs > 0 ? bugs : ''}</td>"
    puts "<td>#{patches > 0 ? patches : ''}</td>"

    UDDData.group_values(ustb, udev, sid).each do |v|
      if v[:count] == 1
        puts "<td>"
      else
        puts "<td colspan=#{v[:count]}>"
      end
      puts v[:value]
      puts "</td>"
    end

    puts "</tr>"
  end

  puts <<-EOF
</tbody>
</table>
</div>
  EOF

  puts "</div>" # div#tabs
  puts "<p><b>Generated in #{Time::now - tstart} seconds.</b></p>"

end # cgi.params

puts <<-EOF
<div class="footer">
<small>Suggestions / comments / patches to debian-qa@lists.debian.org or lucas@debian.org. <a href="hacking.html">
source code</a>.</small>
</div>
</body></html>
EOF

