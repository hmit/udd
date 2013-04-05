#!/usr/bin/ruby

CURARCH='amd64'

require 'dbi'

puts "Content-type: text/plain\n\n"

# calculate $archs
$archs = {}
ENV['http_proxy=http://proxy:3128/']
pas = `wget -q -O - "http://anonscm.debian.org/gitweb/?p=mirror/packages-arch-specific.git;a=blob_plain;f=Packages-arch-specific;hb=HEAD"`
if $? != 0
  puts "Proxy failed"
  exit 1
end
arr = pas.split(/\n/).grep(/^%?[a-z0-9]/).map { |l| l.gsub(/\s*#.*$/,'') }
allarchs=['alpha','amd64','arm','armeb','freebsd-i386','hppa','hurd-i386','i386','ia64','kfreebsd-i386','m32r','m68k','mips','mipsel','netbsd-i386','powerpc','s390','s390x','sh','sparc']
arr.each do |l|
  pkg, archsl = l.split(/:\s*/, 2)
  if archsl.nil?
     STDERR.puts "NIL: #{l}"
     next
  end
  #next if pkg !~ /^%/ # we ignore binary packages
  pkg = pkg.gsub(/^%/,'')
  archs = archsl.split(' ')
  if archsl =~ /!/
    # remove mode
    march = allarchs.clone
    archs.each do |a|
      march = march - [a.gsub(/^!/,'')]
    end
  else
    march = archs
  end
  $archs[pkg] = march
end

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
sth = dbh.prepare("select source, version, architecture
from sources_uniq where distribution='debian' and release='wheezy' and component='main' and (architecture ~ 'all' or architecture ~ 'any' or architecture ~ 'amd64') order by source")
sth.execute
while row = sth.fetch do
  if row['architecture'] =~ /amd64/ or row['architecture'] =~ /any/
    arch = 'any'
  else
    arch = 'all'
  end
  pkg = row['source']
  if $archs[pkg].nil? or $archs[pkg].include?(CURARCH)
    pas = ""
  else
    pas = "excluded-by-P-A-S"
  end

  puts "#{row['source']} #{row['version']} #{arch} #{pas}"
end
sth.finish
