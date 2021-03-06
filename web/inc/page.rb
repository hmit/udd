#!/usr/bin/ruby
require "erb"
require 'oj'
require 'yaml'
$LOAD_PATH.unshift File.dirname(__FILE__)
require 'feed'
require 'cal'

class Page
  attr_accessor :data, :format, :template, :title, :feeditems

  def initialize(data, format, template, hash, title='UDD', feeditems=[])
    @data = data
    @format = format
    @template = template
    hash.each do |key, value|
      singleton_class.send(:define_method, key) { value }
    end 
    @title = title
    @feeditems = feeditems
  end

  def render
    if @format == 'json'
      puts "Content-type: application/json\n\n"
      puts Oj.dump(@data)
    elsif @format == 'yaml'
      puts "Content-type: application/x-yaml\n\n"
      # ruby encoding is too hard, use oj to do the work
      puts Oj.load(Oj.dump(@data)).to_yaml
    elsif @format == 'rss'
      TodoFeed.new(@feeditems, @title)
    elsif @format == 'ics'
      TodoCalendar.new(@feeditems, @title)
    else
      content = File.read(File.expand_path(@template))
      t = ERB.new(content)
      puts "Content-type: text/html\n\n"
      puts t.result(binding)
    end
  end

  def gentags(tags)
      return '' if tags.nil? or tags.empty?
      tags.sort!
      texttags = tags.map do |tag|
        error = "unknowntag: #{tag}" if TagsSingleLetter[tag].nil?
        "<abbr title='#{tag}'>#{TagsSingleLetter[tag]}</abbr>".force_encoding("ASCII-8BIT")
      end
      return '[' + texttags.join('|') + ']'
  end

  def gen_hints_unblocks(hints, unblocks)
    s = ''
    hints.each do |h|
      v = h['version'] ? h['version'] + ' ' : ''
      t = h['type'] == 'age-days' ? "age/#{h['argument']}" : h['type']
      s += "<a href=\"http://release.debian.org/britney/hints/#{h['file']}\" title=\"#{v}#{h['file']} #{h['comment']}\">#{t}</a> "
    end
    unblocks.each do |u|
      if (u['type'] != "unblock")
        s += " #{u['type']}";
      else
        s += "req"
      end
      s += ":<a href=\"http://bugs.debian.org/#{u['id']}\">##{u['id']}</a> "
      s += gentags(u['tags'])
    end
    s
  end

  def pooldir(pkg)
    if pkg =~ /^lib/
      return pkg[0..3]
    else
      return pkg[0]
    end
  end

end
