#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
require 'uri'
require 'net/http'
require 'cgi'

URELEASE='natty'

$cgi = CGI::new

if $cgi.has_key?('csv')
  puts "Content-type: text/plain\n\n"
else
puts "Content-type: text/html\n\n"

puts <<-EOF
<html>
<head>
<style type="text/css">
  td, th {
    border: 1px solid gray;
    padding-left: 3px;
    padding-right: 3px;
  }
  tr:hover  {
    background-color: #ccc;
  }
  table {
    border-collapse: collapse;
  }
</style>
<title>Ubuntu FTBFS</title>
</head>
<body>
<h1>Ubuntu packages that FTBFS</h1>

Contact: <a href="mailto: lucas@ubuntu.com">Lucas Nussbaum</a><br>
EOF
end

STDOUT.flush

res32 = Net::HTTP.get(URI::parse('http://people.ubuntuwire.com/~lucas/ubuntu-nbs/res.ubuntu.32')).split(/\n/)
res64 = Net::HTTP.get(URI::parse('http://people.ubuntuwire.com/~lucas/ubuntu-nbs/res.ubuntu.64')).split(/\n/)

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')

sth = dbh.prepare("select u.source, u.version, u.component, d.version as dversion, d.version > u.version as vercmp from ubuntu_sources u LEFT JOIN (SELECT source, version from sources_uniq where distribution='debian' and release='sid') d on (u.source = d.source) where u.distribution='ubuntu' and u.release='#{URELEASE}' order by u.component, u.source")
sth.execute ; rows_u = sth.fetch_all
sth.finish

fails = {}
res32.each do |l|
  pkg, v, res, reason = l.split(' ', 4)
  fails[pkg] = {} if fails[pkg].nil?
  fails[pkg]['32'] = [res, reason]
  fails[pkg]['version'] = v
end
res64.each do |l|
  pkg, v, res, reason = l.split(' ', 4)
  fails[pkg] = {} if fails[pkg].nil?
  fails[pkg]['64'] = [res, reason]
  fails[pkg]['version'] = v
end
fails.delete_if { |k, v| (v['32'].nil? or v['32'][0] == 'OK') and (v['64'].nil? or v['64'][0] == 'OK') }

outdatedres = []

if not $cgi.has_key?('csv')

puts "#{fails.length} packages failed to build.<br><br>"

puts "<table>"
puts "<tr><th>Package</th><th>Section</th><th>Newer in Debian</th><th>i386</th><th>amd64</th><th>Reason</th></tr>"
end

def showrow(r, fa)
  if $cgi.has_key?('csv')
  print "#{r['source']},#{fa['version']},#{r['component']},"
  if r['dversion'].nil?
    print "Not in Debian"
  elsif r['vercmp']
    print "Yes"
  else
    print "No"
  end
  ['32','64'].each do |a|
    if fa[a].nil?
      print ",N/A"
    else
      print ",http://people.ubuntuwire.org/~lucas/ubuntu-nbs/#{a}/#{r['source']}_#{fa['version']}_lubuntu#{a}.buildlog,#{fa[a][0]}"
    end
  end
  puts
  else
  puts "<tr><td>#{r['source']} #{fa['version']} 
  <a href=\"http://packages.qa.debian.org/#{r['source']}\">PTS</a>
  <a href=\"http://bugs.debian.org/src:#{r['source']}\">BTS</a>
  <a href=\"https://launchpad.net/ubuntu/+source/#{r['source']}\">LP</a>
  </td><td>#{r['component']}</td>"
  if r['dversion'].nil?
    puts "<td>Not in Debian</td>"
  elsif r['vercmp']
    puts "<td>Yes</td>"
  else
    puts "<td>No</td>"
  end
  ['32','64'].each do |a|
    if fa[a].nil?
      puts "<td>N/A</td>"
    else
      puts "<td><a href=\"http://people.ubuntuwire.org/~lucas/ubuntu-nbs/#{a}/#{r['source']}_#{fa['version']}_lubuntu#{a}.buildlog\">#{fa[a][0]}</a></td>"
    end
  end
  if fa['32'].nil? or fa['32'][0] == 'OK' # only amd64 failed
    puts "<td>#{fa['64'][1]}</td>"
  elsif fa['64'].nil? or fa['64'][0] == 'OK' # only i386 failed
    puts "<td>#{fa['32'][1]}</td>"
  elsif fa['32'][1] == fa['64'][1] # both failed with the same message
    puts "<td>#{fa['64'][1]}</td>"
  else
    puts "<td>i386: #{fa['32'][1]}<br>amd64: #{fa['64'][1]}</td>"
  end
  puts "</tr>"
  end
end

rows_u.each do |r|
  fa = fails[r['source']]
  next if fa == nil
  if r['version'] != fa['version']
    outdatedres << r
    next
  end
  showrow(r, fa)
end
if not $cgi.has_key?('csv')
puts "</table>"

puts "<h2>Outdated results</h2>"
puts "Those test builds were done with a version of the package that was superseded by a newer version in ubuntu.<br><br>"
puts "<table>"
puts "<tr><th>Package</th><th>Section</th><th>Newer in Debian</th><th>i386</th><th>amd64</th><th>Reason</th></tr>"
end

outdatedres.each do |r|
  fa = fails[r['source']]
  showrow(r, fa)
end
if not $cgi.has_key?('csv')
puts "</table>"
puts "</body>"
puts "</html>"
end
