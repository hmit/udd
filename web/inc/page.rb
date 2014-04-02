#!/usr/bin/ruby

require "erb"
require 'oj'
require 'yaml'

class Page
  attr_accessor :data, :format, :template

  def initialize(data, format, template, hash)
    @data = data
    @format = format
    @template = template
    hash.each do |key, value|
      singleton_class.send(:define_method, key) { value }
    end 
  end

  def render
    if @format == 'json'
      puts "Content-type: application/json\n\n"
      puts Oj.dump(@data)
    elsif @format == 'yaml'
      puts "Content-type: application/x-yaml\n\n"
      # ruby encoding is too hard, use oj to do the work
      puts Oj.load(Oj.dump(@data)).to_yaml
    else
      content = File.read(File.expand_path(@template))
      t = ERB.new(content)
      puts "Content-type: text/html\n\n"
      puts t.result(binding)
    end
  end
end
