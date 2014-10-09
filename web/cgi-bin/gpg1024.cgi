#!/usr/bin/ruby
# encoding: utf-8

require 'dbi'
require 'pp'
require 'cgi'

STDERR.reopen(STDOUT)

Encoding.default_external = Encoding::UTF_8


puts "Content-type: text/plain\n\n"

d = `mktemp -d`.chomp

s = `gpg --no-options --options /dev/null --homedir #{d} --fingerprint --no-default-keyring --list-keys --with-colons         --keyring /srv/keyring.debian.org/keyrings/debian-keyring.gpg         --keyring /srv/keyring.debian.org/keyrings/debian-maintainers.gpg`

system("rm -rf #{d}")

s = s.encode(Encoding::ASCII, {:invalid => :replace, :undef => :replace}).split(/\n/)

oldkey = false
oldkeys = []
s.each do |l|
  if l =~ /^pub:.:1024:/
    oldkey = true
  end
  if oldkey and l =~ /^fpr:/
    a, b, c = l.split(/:+/)
    oldkeys << b
    oldkey = false
  end
end

#pp oldkeys

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

sth = dbh.prepare("select distinct date, signed_by_name, signed_by_email, key_id, fingerprint, source from upload_history uh1 where (fingerprint, date) in (select fingerprint, max(date) from upload_history uh2 where date < '2015-01-01' group by fingerprint) order by date desc;")
sth.execute ; rows = sth.fetch_all

puts "# Old keys used for uploads to Debian"

rows.each do |r|
  next if not oldkeys.include?(r['fingerprint'])
  puts "#{r['date']} #{r['fingerprint']} #{r['signed_by_name']} (#{r['source']})"
end
sth.finish
