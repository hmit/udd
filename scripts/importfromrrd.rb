#!/usr/bin/ruby -w
# Used by DDPO

require 'dbi'

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452', 'udd')
fields = [ 'vcstype_arch',
  'vcstype_bzr' ,
  'vcstype_cvs' ,
  'vcstype_darcs' ,
  'vcstype_git' ,
  'vcstype_hg' ,
  'vcstype_mtn' ,
  'vcstype_svn' ,
  'format_3native' ,
  'format_3quilt' ]

data = eval(IO::read('/home/lucas/out.sources'))
data.each_pair do |date, values|
  s = "insert into history.sources_count(time,"+
     fields.join(",")+") VALUES(\'" + date + "\',"+fields.map { |f| values[f].nil? ? "NULL" : values[f] }.join(",") + ")"
  p s
  sth = dbh.prepare(s)
  sth.execute
end
