#!/usr/bin/ruby

require 'dbi'
require 'pp'
require 'net/http'
require 'yaml'

puts "Content-type: text/plain\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')


pkgs = Net::HTTP.get(URI::parse('http://blop.info/pub/pkgs')).split(/\n/)
pkgss= pkgs.join("','")
sth = dbh.prepare("select source, changed_by_name as name, extract(epoch from date) as ts, not
exists(select * from upload_history uh2 where uh1.source = uh2.source and
uh1.date > uh2.date) as new from upload_history uh1 order by date asc")
sth.execute ; rows = sth.fetch_all
rows.each do |r|
  puts "#{r['ts'].to_i}|#{r['name']}|#{r['new']?'A':'M'}|#{r['source']}"
end
sth.finish
