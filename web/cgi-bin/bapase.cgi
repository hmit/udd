#!/usr/bin/ruby -w
require 'dbi'
require 'cgi'
require 'actions'

puts "Content-type: text/html\n\n"

WAIT_RM_O = 50
WAIT_RM_RM = 100
WAIT_O_O = 50
WAIT_ORM_RM = 50

DATEZERO = Date::parse('0000-01-01')
CURDATE = Date::today

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')
cgi = CGI.new

type = cgi.params['t']
if not type.nil?
  type = type[0]
end

if type == 'o'
  orphaned = true
  query = "select * from bapase where type is not null order by orphaned_age desc"
elsif type == 'nmu'
  orphaned = true
  query = "select * from bapase where nmu and nmus > 1 order by nmus desc"
elsif type == 'testing'
  orphaned = true
  query = "select * from bapase where testing_age > 1 order by testing_age desc"
else
  puts <<-EOF
  <a href="bapase.cgi?t=o">Orphaned packages</a><br/>
  <a href="bapase.cgi?t=nmu">Packages maintained with NMUs</a><br/>
  <a href="bapase.cgi?t=testing">Packages not in testing</a><br/>
  </body></html>
  EOF
  exit(0)
end

# FIXME add case where type is uknown

$actions = Actions::fetch

puts <<-EOF
<html><head>
<style type="text/css">
  td, th {
    border: 1px solid gray;
    padding-left: 2px;
    padding-right: 2px;
  }
  th {
    font-size: 8pt;
  }
  tr:hover  {
    background-color: #ccc;
  }
  table {
    border-collapse: collapse;
  }
</style>
<title>Bapase</title>
</head><body>
<table border="1"><tr>
<th></th><th>Package</th><th>Action</th>
EOF
puts "<th>Orphaned</th>" if orphaned
puts <<-EOF
<th>Testing</th>
<th>Migrate</th>
<th>Popcon</th>
<th>Bugs</th>
<th>Last upload</th>
<th>NMUs</th>
<th>Comments</th>
</tr>
EOF
sth = dbh.prepare(query)
sth.execute
res = sth.fetch_all
n = 0
res.each do |r|
  n += 1
  pkg = r['source']
  puts "<tr><td>#{n}</td>"
  puts "<td><a href=\"http://packages.qa.debian.org/#{pkg}\">#{pkg}</a>"
  # FIXME removals
  if $actions[pkg]
    if $actions[pkg].act_todo
      puts "<td><b>#{$actions[pkg].act_status}</b></td>"
    else
      puts "<td>#{$actions[pkg].act_status}</td>"
    end
  else
    puts "<td></td>"
  end
  if orphaned
    if r['type']
      puts "<td><a href=\"http://bugs.debian.org/#{r['bug']}\">#{r['type']}</a>&nbsp;(#{r['orphaned_age']})</td>"
    else
      puts "<td></td>"
    end
  end
  if r['testing_age'] and r['testing_age'] > 1
    puts "<td>#{r['testing_age']}</td>"
  else
    puts "<td></td>"
  end
  if r['sync_age'] and r['sync_age'] > 1
    puts "<td>#{r['sync_age']}</td>"
  else
    puts "<td></td>"
  end
  puts "<td>#{r['insts']}&nbsp;/&nbsp;#{r['vote']}</td>"
  puts "<td><a href=\"http://bugs.debian.org/src:#{pkg}\">#{r['rc_bugs']}&nbsp;/&nbsp;#{r['all_bugs']}</a></td>"
  puts "<td>#{r['upload_age']}</td>"
  puts "<td>#{r['nmus']}</td>"
  puts "<td></td>"
  if $actions[pkg]
    comment = $actions[pkg].act_comment.gsub(/#\d+/) do |bug|
      bugn = bug.gsub(/^#/, '')
      "<a href=\"http://bugs.debian.org/#{bugn}\">#{bug}</a>"
    end
    puts "<td>#{comment}</td>"
  else
    puts "<td></td>"
  end
  puts "</tr>"
end
puts "</table>"

puts " -- #{res.length} packages listed."
puts "</body></html>"




#sth.finish
