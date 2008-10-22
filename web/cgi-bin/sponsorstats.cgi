#!/usr/bin/ruby -w

require 'dbi'

puts "Content-type: text/html\n\n"

dbh = DBI::connect('DBI:Pg:udd')
sth = dbh.prepare("select s.source, s.version, u.changed_by, nmu, key_id, cl.login
from sources s, upload_history u, carnivore_emails ce1, carnivore_emails ce2, carnivore_login cl
where s.distribution = 'debian' and s.release = 'sid'
and s.source = u.package
and s.version = u.version
and substring(u.changed_by from '<(.*)>') = ce1.email
and substring(u.key_id from '<(.*)>') = ce2.email
and ce1.id != ce2.id
and ce2.id = cl.id")
sth.execute
names = {}
uploaders = {}
uploads = {}
while row = sth.fetch do
  if not uploaders.has_key?(row['login'])
    uploaders[row['login']] = {}
    names[row['login']] = row['key_id']
    uploads[row['login']] = 0
  end
  uploads[row['login']] += 1
  if not uploaders[row['login']].has_key?(row['changed_by'])
    uploaders[row['login']][row['changed_by']] = []
  end
  uploaders[row['login']][row['changed_by']] << [ row['source'], row['version'], row['nmu'] ]
end

puts "<html><body>"
puts "<h1>Sponsoring stats, powered by UDD!</h2>"
puts "<p>Uploads in <b>bold</b> were NMUs.</p>"
puts '<a href="http://svn.debian.org/wsvn/collab-qa/udd/web/cgi-bin/sponsorstats.cgi?op=file&rev=0&sc=0">source code</a><br/>'

puts "<ul>"
uploaders.to_a.sort { |a,b| uploads[a[0]] <=> uploads[b[0]] }.reverse.each do |k|
  k, v = k
  puts "<li>#{k} -- #{names[k]} (#{uploads[k]} uploads)\n<ul>"
  v.to_a.sort { |a,b| a[1].length <=> b[1].length }.reverse.each do |k2|
    k2, v = k2
    puts "<li>#{k2} (#{v.length} uploads)\n<ul>"
    v.each do |u|
      if u[2]
        puts "<li><b>#{u[0]} #{u[1]}</b></li>"
      else
        puts "<li>#{u[0]} #{u[1]}</li>"
      end
    end
    puts "</ul></li>"
  end
  puts "</ul></li>"
end
puts "</ul>"
sth.finish
