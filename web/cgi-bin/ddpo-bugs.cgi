#!/usr/bin/ruby -w

# Used by DDPO and the PTS

require 'dbi'

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

COMQM = "select bugs_packages.source, count(*) as cnt from bugs, bugs_packages where bugs.id = bugs_packages.id and bugs.id not in (select id from bugs_merged_with where id > merged_with) and status != 'done'"
COMQ = "select bugs_packages.source, count(*) as cnt from bugs, bugs_packages where bugs.id = bugs_packages.id and status != 'done'"
NOPEND = "and bugs.id not in (select id from bugs_tags where tag in ('pending','fixed'))"
ENDQ = "group by bugs_packages.source"
rc = Hash::new { 0 }
rc_m = Hash::new { 0 }
sth = dbh.prepare("#{COMQM} #{NOPEND} and severity >= 'serious' #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| rc[r['source']] = r['cnt'] }
sth.finish
sth = dbh.prepare("#{COMQ} #{NOPEND} and severity >= 'serious' #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| rc_m[r['source']] = r['cnt'] }
sth.finish

ino = Hash::new { 0 }
ino_m = Hash::new { 0 }
sth = dbh.prepare("#{COMQM} #{NOPEND} and severity in ('important','normal') #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| ino[r['source']] = r['cnt'] }
sth.finish
sth = dbh.prepare("#{COMQ} #{NOPEND} and severity in ('important','normal') #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| ino_m[r['source']] = r['cnt'] }
sth.finish

mw = Hash::new { 0 }
mw_m = Hash::new { 0 }
sth = dbh.prepare("#{COMQM} #{NOPEND} and severity in ('minor','wishlist') #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| mw[r['source']] = r['cnt'] }
sth.finish
sth = dbh.prepare("#{COMQ} #{NOPEND} and severity in ('minor','wishlist') #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| mw_m[r['source']] = r['cnt'] }
sth.finish

fp = Hash::new { 0 }
fp_m = Hash::new { 0 }
sth = dbh.prepare("#{COMQM} and bugs.id in (select id from bugs_tags where tag in ('pending','fixed')) #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| fp[r['source']] = r['cnt'] }
sth.finish
sth = dbh.prepare("#{COMQ} and bugs.id in (select id from bugs_tags where tag in ('pending','fixed')) #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| fp_m[r['source']] = r['cnt'] }
sth.finish

patch = Hash::new { 0 }
patch_m = Hash::new { 0 }
sth = dbh.prepare("#{COMQM} #{NOPEND} and bugs.id in (select id from bugs_tags where tag = 'patch') #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| patch[r['source']] = r['cnt'] }
sth.finish
sth = dbh.prepare("#{COMQ} #{NOPEND} and bugs.id in (select id from bugs_tags where tag = 'patch') #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| patch_m[r['source']] = r['cnt'] }
sth.finish

pkgs = (rc.keys + ino.keys + mw.keys + fp.keys + patch.keys).uniq.sort
pkgs.each do |pkg|
  print "#{pkg}:"
  print "#{rc[pkg]}(#{rc_m[pkg]}) "
  print "#{ino[pkg]}(#{ino_m[pkg]}) "
  print "#{mw[pkg]}(#{mw_m[pkg]}) "
  print "#{fp[pkg]}(#{fp_m[pkg]}) "
  puts "#{patch[pkg]}(#{patch_m[pkg]})"
end
