#!/usr/bin/ruby

require 'cgi'
require 'yaml'
require 'dbi'
require 'debian'

include Debian

class DebVersion
  def initialize(s)
    @version = s
  end

  def version
    @version
  end

  def to_s
    @version
  end

  def < (deb)
    Dpkg.compare_versions(self.version, '<<', deb.version)
  end
  def <= (deb)
    Dpkg.compare_versions(self.version, '<=', deb.version)
  end
  def == (deb)
    Dpkg.compare_versions(self.version, '=', deb.version)
  end
  def >= (deb)
    Dpkg.compare_versions(self.version, '>=', deb.version)
  end
  def > (deb)
    Dpkg.compare_versions(self.version, '>>', deb.version)
  end
end

STDERR.reopen(STDOUT) # makes live debugging much easier
puts "Content-type: text/html\n\n"


puts <<-EOF
<html>
<head>
<style type="text/css" rel="stylesheet">
@import "../css/jquery-ui-1.8.21.custom.css";
@import "../css/dmd.css";
</style>
<title>Mentors @ UDD</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<script type="text/javascript" src="../js/jquery.min.js"></script>
<script type="text/javascript" src="../js/jquery.tablesorter.min.js"></script>
<script type="text/javascript" src="../js/jquery-ui.custom.min.js"></script>
<script type="text/javascript" src="../js/jquery.cookie.min.js"></script>
<script>
$(document).ready(function() {
$("table.tablesorter").each(function(index) { $(this).tablesorter() });
});
</script>
</head>
<body>
<h1 style="margin-bottom : 5px"><img src="http://qa.debian.org/debian.png" alt="Debian logo" width="188" height="52" style="vertical-align : -13px; ">Mentors <span style="color :#c70036">@</span> UDD</h1>
<div id="body">
<br/>
<p>This is a simple CGI that demonstrates what can be done with the mentors data using UDD.</p>
EOF

$dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
def dbget(q, *args)
  rows, sth = nil
  sth = $dbh.prepare(q)
  sth.execute(*args)
  rows = sth.fetch_all
end

def quote(s)
  DBI::DBD::Pg::quote(s)
end

pkgs = dbget("select mp.name, mpv.version, mpv.distribution, pc.insts, mpv.uploaded
            from mentors_raw_packages mp
            inner join mentors_most_recent_package_versions mpv on (mp.id = mpv.package_id)
            left join popcon_src pc on (pc.source = mp.name)
            where needs_sponsor = 1 order by name")

sprequests = dbget("select * from sponsorship_requests")

srcnames = pkgs.map { |e| e['name'] }

srcstatus = dbget("select source, version, release from sources where source in (#{srcnames.map { |e| quote(e) }.join(',')}) and release not in ('squeeze', 'wheezy', 'jessie')")

itps = dbget("select * from wnpp where type='ITP'")

puts <<-EOF
<table class="buglist tablesorter">
<thead>
<tr>
<th>bug</th><th>source</th><th>version</th><th>distribution</th><th>uploaded</th><th>&nbsp;&nbsp;&nbsp;popcon&nbsp;&nbsp;&nbsp;</th><th>in Debian</th><th>status</th><th>links</th>
</tr>
</thead>
<tbody>
EOF
pkgs.each do |l|
  st = srcstatus.select { |e| e['source'] == l['name'] }
  if st.empty?
    itp = itps.select { |i| i['source'] == l['name'] }[0]
    if itp.nil?
      status = "not in Debian (no ITP)"
    else
      status = "not in Debian (<a href=\"http://bugs.debian.org/#{itp['id']}\">ITP</a>)"
    end
  else
    v = nil
    if l['distribution'] == 'unstable'
      v = st.select { |e| e['release'] == 'sid' }.first
      next if not v.nil? and DebVersion::new(v['version']) >= DebVersion::new(l['version'])
    elsif l['distribution'] == 'experimental'
      v = st.select { |e| e['release'] == 'experimental' }.first
      next if not v.nil? and DebVersion::new(v['version']) >= DebVersion::new(l['version'])
      if v.nil?
        v = st.select { |e| e['release'] == 'sid' }.first
        next if not v.nil? and DebVersion::new(v['version']) >= DebVersion::new(l['version'])
      end
    end
    if v
      mentversion = l['version'].gsub(/-[\da-zA-Z.~+]+$/,'')
      debversion = v['version'].gsub(/-[\da-zA-Z.~+]+$/,'')
      if mentversion == debversion
        status = "already in Debian"
      else
        status = "already in Debian, new upstream release"
      end
    else
      status = 'already in Debian, status unknown'
    end
  end
  bug = sprequests.select { |e| e['source'] == l['name'] and e['version'] == l['version'] }.first
  puts "<tr>"
  if bug
    id = bug['id']
    puts "<td><a href=\"http://bugs.debian.org/#{id}\">##{id}</a></td>"
  else
    puts "<td></td>"
  end
  puts "<td>#{l['name']}</td>"
  puts "<td>#{l['version']}</td>"
  puts "<td>#{l['distribution']}</td>"
  puts "<td>#{l['uploaded'].to_s.split('T')[0]}</td>"
  puts "<td>#{l['insts']}</td>"
  puts "<td>"
  puts st.map { |l2| "#{l2['release']}: #{l2['version']}" }.join("<br/>")
  puts "</td>"
  puts "<td>"
  puts status
  puts "</td>"
  puts "<td>"
  puts "<a href=\"http://packages.qa.debian.org/#{l['name']}\">PTS</a>"
  puts "<a href=\"http://mentors.debian.net/package/#{l['name']}\">mentors</a>"
  puts "</td>"
  puts "</tr>"
end

puts <<-EOF
</tbody>
</table>
<br/>
<div class="footer">
<small><a href="https://wiki.debian.org/UltimateDebianDatabase/Hacking">hacking / bug reporting / contact information</a> - <a href="http://anonscm.debian.org/gitweb/?p=collab-qa/udd.git;a=blob_plain;f=web/cgi-bin/mentors.cgi">source code</a></small>
</div>
</body></html>
EOF

