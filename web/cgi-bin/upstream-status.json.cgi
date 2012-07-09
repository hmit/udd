#!/usr/bin/ruby
require 'dbi'
require 'pp'
require 'cgi'
require 'json'

STDERR.reopen(STDOUT)
puts "Content-type: text/json\n\n"

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
q = <<-EOF
select source, debian_mangled_uversion, debian_uversion, status, upstream_url, upstream_version
from upstream
where status is not null
and release='sid'
EOF
sth = dbh.prepare(q)
sth.execute()
rows = sth.fetch_all
rows2 = rows.map { |r| {
  'debian-mangled-uversion' => r['debian_mangled_uversion'],
  'debian-uversion' => r['debian_uversion'],
  'package' => r['source'].to_s,
  'status' => r['status'],
  'upstream-url' => r['upstream_url'],
  'upstream-version' => r['upstream_version']
}
}
puts JSON::pretty_generate(rows2)
