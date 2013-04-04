#!/usr/bin/ruby

Encoding.default_internal='UTF-8'

require 'dbi'
require 'pp'
require 'uri'
require 'net/http'
require 'json/pure'
require 'pp'

puts "Content-type: application/json\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')

sth = dbh.prepare("select * from bugs where package='sponsorship-requests'")
sth.execute ; rows = sth.fetch_all

ids = rows.map { |r| r['id'] }

sth2 = dbh.prepare("select * from bugs_tags where id in (#{ids.join(',')})")
sth2.execute ; rowst = sth2.fetch_all

tags = {}
rowst.each do |r|
  tags[r['id']] ||= []
  tags[r['id']] << r['tag']
end

h = []

rows.each do |r|
  mybug = r.to_h
  if tags[mybug['id']]
    mybug['tags'] = tags[mybug['id']]
  else
    mybug['tags'] = []
  end
  h << mybug
end

puts JSON::pretty_generate(h)
