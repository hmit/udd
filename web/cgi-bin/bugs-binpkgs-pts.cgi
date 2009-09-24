#!/usr/bin/ruby -w

# Used by the PTS

require 'dbi'

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guest')

COMQ = "select bugs_packages.package, count(*) as cnt from bugs, bugs_packages where bugs.id = bugs_packages.id and status != 'done'"
NOPEND = "and bugs.id not in (select id from bugs_tags where tag in ('pending','fixed'))"
ENDQ = "group by bugs_packages.package"

rc_m = Hash::new { 0 }
sth = dbh.prepare("#{COMQ} #{NOPEND} and severity >= 'serious' #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| rc_m[r['package']] = r['cnt'] }
sth.finish

ino_m = Hash::new { 0 }
sth = dbh.prepare("#{COMQ} #{NOPEND} and severity in ('important','normal') #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| ino_m[r['package']] = r['cnt'] }
sth.finish

mw_m = Hash::new { 0 }
sth = dbh.prepare("#{COMQ} #{NOPEND} and severity in ('minor','wishlist') #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| mw_m[r['package']] = r['cnt'] }
sth.finish

fp_m = Hash::new { 0 }
sth = dbh.prepare("#{COMQ} and bugs.id in (select id from bugs_tags where tag in ('pending','fixed')) #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| fp_m[r['package']] = r['cnt'] }
sth.finish

patch_m = Hash::new { 0 }
sth = dbh.prepare("#{COMQ} #{NOPEND} and bugs.id in (select id from bugs_tags where tag = 'patch') and bugs.id not in (select id from bugs_tags where tag = 'wontfix') #{ENDQ}")
sth.execute
sth.fetch_all.each { |r| patch_m[r['package']] = r['cnt'] }
sth.finish

pkgs = (rc_m.keys + ino_m.keys + mw_m.keys + fp_m.keys + patch_m.keys).uniq.sort
pkgs.each do |pkg|
  print "#{pkg} "
  print "#{rc_m[pkg]} "
  print "#{ino_m[pkg]} "
  print "#{mw_m[pkg]} "
  print "#{fp_m[pkg]} "
  puts "#{patch_m[pkg]}"
end
