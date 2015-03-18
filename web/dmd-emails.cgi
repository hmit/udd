#!/usr/bin/ruby
$LOAD_PATH.unshift File.dirname(__FILE__) + '/inc'
require 'dmd-data'

STDERR.reopen(STDOUT) # makes live debugging much easier
puts "Content-type: text/json\n\n"

require File.expand_path(File.dirname(__FILE__))+'/inc/dmd-data'

cgi = CGI::new

if cgi.params['term'][0]
  term = cgi.params['term'][0]
  uddd = UDDData::new
  puts JSON::dump(uddd.complete_email(term))
end
