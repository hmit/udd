#!/usr/bin/ruby

require "ostruct"
require "erb"

require File.expand_path(File.dirname(__FILE__))+'/inc/page'

page = Page.new({ :title => 'Ultimate Debian Database' })
puts "Content-type: text/html\n\n"
puts page.render("templates/index.erb")
