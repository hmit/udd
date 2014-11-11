#!/usr/bin/ruby

require 'dbi'
require 'pp'

puts "Content-type: text/html\n\n"

puts <<-EOF
<html>
<head>
<title>WNPP checks</title>
</head>
<body>
<h1>WNPP checks</h1>
EOF

$dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

def dbget(q, *args)
  rows, sth = nil
  sth = $dbh.prepare(q)
  sth.execute(*args)
  rows = sth.fetch_all
  return rows
end

# get list of WNPP bugs, in a rather tolerant way
rows = dbget("SELECT id, SUBSTRING(title from '^([A-Z]{1,3}):.*') as type, SUBSTRING(title from '^[A-Z]{1,3}:[ ]*([^ ]+)') as source, title FROM bugs WHERE package='wnpp' AND status!='done' and id not in (select id from bugs_merged_with where id > merged_with) order by id;")

sources = dbget("SELECT DISTINCT source from sources_uniq where release in ('sid', 'experimental') order by source")

sources = sources.map { |s| s.first }

puts "<h2>RFP/ITP for packaged software</h2>"
puts "<p>Should probably be closed.</p>"
puts "<ul>"
rows.each do |r|
  next if not ['RFP', 'ITP'].include?(r['type'])
  next if not sources.include?(r['source'])
  puts "<li>#{r['source']}: <a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']} (#{r['type']})</a> <a href=\"http://tracker.debian.org/#{r['source']}\">PTS</a> <a href=\"http://tracker.debian.org/#{r['source']}\">tracker</a></li>"
end
puts "</ul>"

puts "<h2>ITA/RFA/RFH/O for packages not in Debian</h2>"
puts "<p>Should probably be closed.</p>"
puts "<ul>"
rows.each do |r|
  next if not ['ITA', 'RFA', 'RFH', 'O'].include?(r['type'])
  next if sources.include?(r['source'])
  puts "<li>#{r['source']}: <a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']} (#{r['type']})</a> <a href=\"http://tracker.debian.org/#{r['source']}\">PTS</a> <a href=\"http://tracker.debian.org/#{r['source']}\">tracker</a></li>"
end
puts "</ul>"

puts "<h2>Packages with more than one WNPP bug</h2>"
puts "<p>Should probably be merged.</p>"
puts "<ul>"
rows.group_by { |r| r['source'] }.each_pair do |src, bugs|
  next if bugs.length < 2
  puts "<li>#{src} (<a href=\"http://tracker.debian.org/#{src}\">PTS</a> <a href=\"http://tracker.debian.org/#{src}\">tracker</a>):<ul>"
  bugs.each do |r|
    puts "<li><a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']} (#{r['type']})</a> #{r['title']}</li>"
  end
  puts "</ul></li>"
end
puts "</ul>"


puts "<h2>WNPP bugs not following defined format</h2>"
puts "<p>Should probably be retitled accordingly.</p>"
inval = dbget("select * from wnpp order by id")
retitles = []
puts "<ul>"
inval.each do |r|
  if not r['title'] =~ /^(RFP|ITP|O|ITA|RFA|RFH): ([^ ]+) -- (.+)$/
    puts "<li><a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']}</a>: #{r['title']}</li>"
    retitles << "bts retitle #{r['id']} #{r['title']}"
  end
end
puts "</ul>"

puts "As a list of bts commands:<pre>"
puts retitles.join("\n")
puts "</pre>"

puts "<h2>Packages maintained by tracker.debian.org without a corresponding ITA or O bug</h2>"
puts "<p>Also listing the first QA upload.</p>"
puts "<p>A WNPP bug should probably be opened.</p>"
ita_o = rows.select { |r| ['ITA', 'O'].include?(r['type']) }.map { |r| r['source'] }

qasrcs = dbget("select source from sources_uniq where release in ('sid', 'experimental') and maintainer_email = 'tracker.debian.org' order by source")
puts "<ul>"
qasrcs.each do |s|
  src = s['source']
  next if ita_o.include?(src)
  last = dbget("select * from upload_history where source='#{src}' and maintainer LIKE '%tracker.debian.org%' order by date asc limit 1")
  if last.length == 1
    last = last.first
    s = "(since #{last['version']} ; #{last['date']} ; #{last['changed_by_name']} &lt;#{last['changed_by_email']}&gt;)"
  else
    s = ""
  end
  puts "<li>#{src}: <a href=\"http://tracker.debian.org/#{src}\">PTS</a> <a href=\"http://tracker.debian.org/#{src}\">tracker</a> #{s}</li>"
end
puts "</ul>"

puts "<h2>ITP and ITA without owners</h2>"
puts "<p>A suitable owner should be determined.</p>"
itpita = rows.select { |r| ['ITA', 'ITP'].include?(r['type']) }.map { |r| r['id'] }.map { |s| "'#{s}'"}.join(', ')
bugs = dbget("select * from bugs where id in (#{itpita}) and owner = '' order by id")
puts "<ul>"
bugs.each do |r|
  puts "<li><a href=\"http://bugs.debian.org/#{r['id']}\">##{r['id']}</a>: #{r['title']}</li>"
end
puts "</ul>"

puts "</body></html>"
