#!/usr/bin/ruby

require 'dbi'
require 'cgi'

puts "Content-type: text/html; charset=utf-8\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
sth = dbh.prepare("select s.source, s.version, u.changed_by, nmu, signed_by, cl.login
from sources s, upload_history u, carnivore_emails ce1, carnivore_emails ce2, carnivore_login cl
where s.distribution = 'debian' and s.release = 'sid'
and s.source = u.source
and s.version = u.version
and u.changed_by_email = ce1.email
and u.signed_by_email = ce2.email
and ce1.id != ce2.id
and ce2.id = cl.id
and u.changed_by_email not in (
select email from carnivore_emails, carnivore_login where carnivore_login.id = carnivore_emails.id)
")
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

puts "<!DOCTYPE html><html><head><title>Sponsoring stats</title></head>"
puts "<body>"
puts "<h1>Sponsoring stats, powered by UDD!</h1>"
puts "<p>Uploads in <b>bold</b> were NMUs.</p>"
puts "<p>That excludes uploads done for people who are now DD, even if the upload was done while they were not DD.</p>"
puts '<a href="http://anonscm.debian.org/viewvc/collab-qa/udd/web/sponsorstats.cgi?view=markup">source code</a><br/>'

puts "<ul>"
rank = 0
uploaders.to_a.sort { |a,b| uploads[a[0]] <=> uploads[b[0]] }.reverse.each do |k|
  k, v = k
  rank += 1
  puts "<li>#{rank}. #{k} -- #{names[k]} (#{uploads[k]} uploads)\n<ul>"
  v.to_a.sort { |a,b| a[1].length <=> b[1].length }.reverse.each do |k2|
    k2, v = k2
    puts "<li>#{CGI.escapeHTML(k2)} (#{v.length} uploads)\n<ul>"
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
