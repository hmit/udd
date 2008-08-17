#!/usr/bin/ruby -w

sources = [ 'debian-sid', 'debian-etch', 'debian-lenny', 'ubuntu-intrepid', 'ubuntu-hardy', 'debian-popcon', 'ubuntu-popcon', 'testing-migrations', 'upload-history', 'bugs', 'orphaned_packages', 'bugs_archived' ]
# 'carnivore', 'lintian'

sources.each do |s|
  ts = Time::now
  system("/org/udd.debian.net/update-and-dispatch.sh #{s}")
  te = Time::now
  puts "#### #{s} first import: #{te-ts}s"
end
sources.each do |s|
  ts = Time::now
  system("/org/udd.debian.net/update-and-dispatch.sh #{s}")
  te = Time::now
  puts "#### #{s} second import: #{te-ts}s"
end
