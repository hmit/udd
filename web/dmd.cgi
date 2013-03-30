#!/usr/bin/ruby

require 'cgi'
require 'yaml'

STDERR.reopen(STDOUT) # makes live debugging much easier
puts "Content-type: text/html\n\n"

require File.expand_path(File.dirname(__FILE__))+'/inc/dmd-data'

cgi = CGI::new

tstart = Time::now

default_packages = ''
default_packages = CGI.escapeHTML(cgi.params['packages'][0]) if cgi.params['packages'][0]
default_bin2src = ''
default_bin2src = CGI.escapeHTML(cgi.params['bin2src'][0]) if cgi.params['bin2src'][0]

defaults = {}
defaults['nosponsor'] = {}
defaults['nouploader'] = {}
defaults['email'] = {}
['1','2','3'].each do |i|
  ['nosponsor', 'nouploader','email'].each do |s|
    if cgi.params[s+i][0]
      defaults[s][i] = CGI.escapeHTML(cgi.params[s+i][0])
    else
      defaults[s][i] = ''
    end
  end
end


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
<script type="text/javascript" src="js/jquery.cookie.min.js"></script>
<script>
$(function() {
  $( "#tabs" ).tabs();
  $( "#email1" ).autocomplete({
    source: "dmd-emails.cgi",
    select: function(event, ui) {
        $("#email1").val(ui.item.value);
        $("#searchForm").submit();
    }
  });
  $( "#email2" ).autocomplete({
    source: "dmd-emails.cgi",
    select: function(event, ui) {
        $("#email2").val(ui.item.value);
        $("#searchForm").submit();
    }
  });
  $( "#email3" ).autocomplete({
    source: "dmd-emails.cgi",
    select: function(event, ui) {
        $("#email3").val(ui.item.value);
        $("#searchForm").submit();
    }
  });
});
$(document).ready(function() {
$("table.tablesorter").each(function(index) { $(this).tablesorter() });
$("tbody.todos tr").each(function(index, elem) { if ($.cookie(elem.id) == '1') $(elem).hide(); });
});
function hide_todo(id) {
  $.cookie(id, '1', { expires: 3650 });
  $("tbody.todos tr#"+id).hide();
}

function reset_todos() {
$("tbody.todos tr").each(function(index, elem) {
 $.cookie(elem.id, null);
 $(elem).show();
});
}

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
<h1 style="margin-bottom : 5px"><img src="http://qa.debian.org/debian.png" alt="Debian logo" width="188" height="52" style="vertical-align : -13px; ">Maintainer Dashboard <span style="color :#c70036">@</span> UDD</h1>
<div id="body">
<br/>
<form id="searchForm" action="dmd.cgi" method="get">
EOF

['1','2','3'].each do |i|
  puts <<-EOF
email: <input id="email#{i}" type='text' size='100' name='email#{i}' value='#{defaults['email'][i]}'/>
&nbsp;&nbsp;ignore:
<input id="nouploader#{i}" name="nouploader#{i}" type="checkbox" #{defaults['nouploader'][i] != '' ? 'checked':''}/> co-maintained &nbsp;&nbsp;
<input id="nosponsor#{i}" name="nosponsor#{i}" type="checkbox" #{defaults['nosponsor'][i] != '' ? 'checked' : ''}/> sponsored / NMUed <br/>
  EOF
end
puts <<-EOF
<br/>
additional (source) packages (one per line or space-separated):<br/>
<textarea id="packages" name="packages" cols="80" rows="1"/>#{default_packages}</textarea><br/>
<input id="bin2src" name="bin2src" type="checkbox" #{default_bin2src != '' ? 'checked' : ''}/> Packages are binary packages, convert to source packages<br/>

&nbsp;&nbsp; <input type='submit' value='Go' onsubmit="removeBlankFields(this);"/>
</form>
EOF

if cgi.params != {}
  emails = {}

  # for compatibility purposes
  if cgi.params["email"][0] and cgi.params["email"][0] != ''
    emails[cgi.params["email"][0]] = [ :maintainer, :uploader, :sponsor ]
  end

  [1, 2, 3].each do |i|
    if cgi.params["email#{i}"][0] and cgi.params["email#{i}"][0] != ''
      em = cgi.params["email#{i}"][0]
      types = [ :maintainer, :uploader, :sponsor ]
      types.delete(:uploader) if cgi.params["nouploader#{i}"][0] == 'on'
      types.delete(:sponsor) if cgi.params["nosponsor#{i}"][0] == 'on'
      emails[em] = types
    end
  end
  $uddd = UDDData::new(emails, cgi.params["packages"][0] || "", cgi.params["bin2src"][0] == 'on')
  $uddd.get_sources
  $uddd.get_sources_status
  $uddd.get_dmd_todos
  $uddd.get_ubuntu_bugs

  def src_reason(pkg)
    s = $uddd.sources[pkg]
    if s[0] == :manually_listed
      return "<span title=\"manually listed\"><b>#{pkg}</b></span>"
    elsif s[0] == :maintainer
      return "<span title=\"maintained by #{s[1]}\"><b>#{pkg}</b></span>"
    elsif s[0] == :uploader
      return "<span title=\"co-maintained by #{s[1]}\">#{pkg}</span>"
    elsif s[0] == :sponsor
      return "<span title=\"was uploaded by #{s[1]}\"><i>#{pkg}</i></span>"
    end
  end

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
<th>type</th><th>source</th><th>description</th><th>&nbsp;&nbsp;&nbsp;&nbsp;hide&nbsp;&nbsp;&nbsp;&nbsp;</th>
</tr>
</thead><tbody class='todos'>
  EOF
  $uddd.dmd_todos.each do |t|
    puts "<tr id='#{t[:shortname]}'><td>#{t[:type]}</td>"
    puts "<td class=\"left\"><a href=\"http://packages.qa.debian.org/#{t[:source]}\">#{src_reason(t[:source])}</a></td>"
    puts "<td class=\"left\">#{t[:description]}</td>"
    puts "<td><a href=\"#\" onclick=\"hide_todo('#{t[:shortname]}'); return false;\">hide</a></td>"
  end
  puts "</tbody></table>"
  puts "<p align=\"center\"><a href=\"#\" onclick=\"reset_todos()\">show all hidden todos</a></p>"
  puts "</div>" # tabs-todo

	puts '<div id="tabs-versions">'

  puts <<-EOF
<table class="buglist tablesorter">
<thead>
<tr>
<th>&nbsp;&nbsp;&nbsp;&nbsp;source&nbsp;&nbsp;&nbsp;&nbsp;</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;squeeze&nbsp;&nbsp;&nbsp;&nbsp;</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;wheezy&nbsp;&nbsp;&nbsp;&nbsp;</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;sid&nbsp;&nbsp;&nbsp;&nbsp;</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;experimental&nbsp;&nbsp;&nbsp;&nbsp;</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;vcs&nbsp;&nbsp;&nbsp;&nbsp;</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;upstream&nbsp;&nbsp;&nbsp;&nbsp;</th>
</tr>
</thead>
<tbody>
  EOF
  $uddd.sources.keys.sort.each do |src|
    next if not $uddd.versions.include?(src)
    next if not $uddd.versions[src].include?('debian')
    dv = $uddd.versions[src]['debian']
    puts "<tr><td class=\"left\"><a href=\"http://packages.qa.debian.org/#{src}\">#{src_reason(src)}</a></td>"

    t_stable = t_testing = t_unstable = t_experimental = t_vcs = ''

    t_stable += dv['squeeze'][:version] if dv['squeeze']
    t_stable += "<br>sec: #{dv['squeeze-security'][:version]}" if dv['squeeze-security']
    t_stable += "<br>pu: #{dv['squeeze-proposed-updates'][:version]}" if dv['squeeze-proposed-updates']
    t_stable += "<br>bpo: #{dv['squeeze-backports'][:version]}" if dv['squeeze-backports']

    t_testing += dv['wheezy'][:version] if dv['wheezy']
    t_testing += "<br>sec: #{dv['wheezy-security'][:version]}" if dv['wheezy-security']
    t_testing += "<br>pu: #{dv['wheezy-proposed-updates'][:version]}" if dv['wheezy-proposed-updates']

    if dv['sid']
      t_unstable += dv['sid'][:version]
      sid = dv['sid'][:version]
    else
      sid = ''
    end

    if dv['experimental']
      t_experimental += dv['experimental'][:version]
      exp = dv['experimental'][:version]
    else
      exp = ''
    end

    vcs = $uddd.versions[src]['vcs']
    if vcs
      t = UDDData.compare_versions(sid, vcs[:version])
      te = UDDData.compare_versions(exp, vcs[:version])
      if (t == -1 or te == -1) and t != 0 and te != 0 and ['unstable', 'experimental'].include?(vcs[:distribution])
        t_vcs += "<a href=\"http://pet.debian.net/#{vcs[:team]}/pet.cgi\"><span class=\"prio_high\" title=\"Ready for upload to #{vcs[:distribution]}\">#{vcs[:version]}</span></a>"
      elsif (t == -1 or te == -1) and t != 0 and te != 0
        t_vcs += "<a href=\"http://pet.debian.net/#{vcs[:team]}/pet.cgi\"><span class=\"prio_med\" title=\"Work in progress\">#{vcs[:version]}</span></a>"
      elsif t == 1 and te == 1
        t_vcs += "<a href=\"http://pet.debian.net/#{vcs[:team]}/pet.cgi\"><span class=\"prio_high\" title=\"Version in archive newer than version in VCS\">#{vcs[:version]}</span></a>"
      else
        t_vcs += "#{vcs[:version]}"
      end
    end

    UDDData.group_values(t_stable, t_testing, t_unstable, t_experimental, t_vcs).each do |v|
      if v[:count] == 1
        puts "<td>"
      else
        puts "<td colspan=#{v[:count]}>"
      end
      puts v[:value]
      puts "</td>"
    end

    up = $uddd.versions[src]['upstream']
    puts "<td>"
    if up
      s = case up[:status]
          when :error then "<span class=\"prio_high\" title=\"uscan returned an error\">error</a>"
          when :up_to_date then up[:version]
          when :newer_in_debian then "<span class=\"prio_high\" title=\"Debian version newer than upstream version. debian/watch bug?\">#{up[:version]}</a>"
          when :out_of_date then "<span class=\"prio_high\" title=\"Newer upstream version available\">#{up[:version]}</a>"
          when :out_of_date_in_unstable then "<span class=\"prio_med\" title=\"Newer upstream version available (already packaged in experimental)\">#{up[:version]}</a>"
          else "Unhandled case!"
          end
      puts s
    end
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
  bc = $uddd.bugs_count
  bc.keys.sort.each do |src|
    b = bc[src]
    next if b[:all] == 0
    puts "<tr><td class=\"left\"><a href=\"http://packages.qa.debian.org/#{src}\">#{src_reason(src)}</a></td>"
    puts "<td><a href=\"http://bugs.debian.org/cgi-bin/pkgreport.cgi?src=#{src}\">#{b[:all] > 0 ? b[:all] : ''}</a></td>"
    puts "<td><a href=\"http://bugs.debian.org/cgi-bin/pkgreport.cgi?src=#{src}&sev-inc=critical&sev-inc=grave&sev-inc=serious\">#{b[:rc] > 0 ? b[:rc] : ''}</a></td>"
    puts "<td><a href=\"http://bugs.debian.org/cgi-bin/pkgreport.cgi?src=#{src}&include=tags:patch\">#{b[:patch] > 0 ? b[:patch] : ''}</a></td>"
    puts "<td><a href=\"http://bugs.debian.org/cgi-bin/pkgreport.cgi?src=#{src}&pend-inc=pending-fixed&pend-inc=fixed\">#{b[:pending] > 0 ? b[:pending] : ''}</a></td></tr>"
  end
  puts "</tbody></table>"
  puts "</div>"

  puts '<div id="tabs-ubuntu">'

  ur = YAML::load(IO::read('ubuntu-releases.yaml'))
  USTB=ur['stable']
  UDEV=ur['devel']
  puts <<-EOF
<table class="buglist tablesorter">
<thead>
<tr>
<th>source</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;bugs&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;patches&nbsp;&nbsp;&nbsp;&nbsp;</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;#{USTB} (stable)&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;#{UDEV} (devel)&nbsp;&nbsp;&nbsp;&nbsp;</th><th>&nbsp;&nbsp;&nbsp;&nbsp;sid&nbsp;&nbsp;&nbsp;&nbsp;</th>
<th>&nbsp;&nbsp;&nbsp;&nbsp;links&nbsp;&nbsp;&nbsp;&nbsp;</th>
</tr>
</thead>
<tbody>
  EOF
  $uddd.sources.keys.sort.each do |src|
    next if not $uddd.versions.include?(src)
    next if (not $uddd.versions[src].include?('debian') or not $uddd.versions[src].include?('ubuntu'))

    ub = $uddd.ubuntu_bugs[src]
    if ub.nil?
      bugs = 0
      patches = 0
    else
      bugs = ub[:bugs]
      patches = ub[:patches]
    end

    dv = $uddd.versions[src]['debian']
    if dv['sid']
      sid = dv['sid'][:version]
    else
      sid = ''
    end

    du = $uddd.versions[src]['ubuntu']
    ustb = ''
    udev = ''
    if not du.nil?
      ustb = du[USTB][:version] if du[USTB]
      ustb += "<br>sec:&nbsp;#{du["#{USTB}-security"][:version]}" if du["#{USTB}-security"]
      ustb += "<br>upd:&nbsp;#{du["#{USTB}-updates"][:version]}" if du["#{USTB}-updates"]
      ustb += "<br>prop:&nbsp;#{du["#{USTB}-proposed"][:version]}" if du["#{USTB}-proposed"]
      ustb += "<br>bpo:&nbsp;#{du["#{USTB}-backports"][:version]}" if du["#{USTB}-backports"]

      udev = du[UDEV][:version] if du[UDEV]
      if udev == sid
        if bugs == 0 and patches == 0
          next
        end
      elsif sid != ''
        if UDDData.compare_versions(udev, sid) == -1
          if udev =~ /ubuntu/
            udev = "<a href=\"http://ubuntudiff.debian.net/?query=-FPackage+#{src}\"><span class=\"prio_high\" title=\"Outdated version in Ubuntu, with an Ubuntu patch\">#{udev}</span></a>"
          else
            udev = "<span class=\"prio_med\" title=\"Outdated version in Ubuntu\">#{udev}</span>"
          end
        elsif UDDData.compare_versions(udev, sid) == 1
          udevnb = udev.gsub(/build\d+$/,'')
          if UDDData.compare_versions(udevnb, sid) == 1
            udev = "<a href=\"http://ubuntudiff.debian.net/?query=-FPackage+#{src}\"><span class=\"prio_high\" title=\"Newer version in Ubuntu\">#{udev}</span></a>"
          end
        end
      end
      udev += "<br>sec:&nbsp;#{du["#{UDEV}-security"][:version]}" if du["#{UDEV}-security"]
      udev += "<br>upd:&nbsp;#{du["#{UDEV}-updates"][:version]}" if du["#{UDEV}-updates"]
      udev += "<br>prop:&nbsp;#{du["#{UDEV}-proposed"][:version]}" if du["#{UDEV}-proposed"]
      udev += "<br>bpo:&nbsp;#{du["#{UDEV}-backports"][:version]}" if du["#{UDEV}-backports"]
    end

    puts "<tr><td class=\"left\">#{src_reason(src)}&nbsp;</td>"
    if bugs > 0
      puts "<td><a href=\"https://bugs.launchpad.net/ubuntu/+source/#{src}\">#{bugs}</a></td>"
    else
      puts "<td></td>"
    end
    if patches > 0
      puts "<td><a href=\"https://bugs.launchpad.net/ubuntu/+source/#{src}/+patches\">#{patches}</a></td>"
    else
      puts "<td></td>"
    end

    UDDData.group_values(ustb, udev, sid).each do |v|
      if v[:count] == 1
        puts "<td>"
      else
        puts "<td colspan=#{v[:count]}>"
      end
      puts v[:value]
      puts "</td>"
    end
    puts "<td><a href=\"http://packages.qa.debian.org/#{src}\">PTS</a>&nbsp;<a href=\"https://launchpad.net/ubuntu/+source/#{src}\">LP</a></td>"
    puts "</tr>"
  end

  puts <<-EOF
</tbody>
</table>
<p>Packages with the same version in <i>#{UDEV}</i> and <i>Debian sid</i>, no bugs and no patches are not listed.</p>
</div>
  EOF

  puts "</div>" # div#tabs
  puts "<p><b>Generated in #{Time::now - tstart} seconds.</b></p>"

end # cgi.params

puts <<-EOF
<div class="footer">
<small><a href="hacking.html">hacking / bug reporting / contact information</a> - <a href="http://anonscm.debian.org/gitweb/?p=collab-qa/udd.git;a=blob_plain;f=web/dmd.cgi">source code</a></small>
</div>
</body></html>
EOF

