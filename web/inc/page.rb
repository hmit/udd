#!/usr/bin/ruby

require "erb"

class Page
  def initialize(hash)
    hash.each do |key, value|
      singleton_class.send(:define_method, key) { value }
    end 
  end
  def render(path)
    content = File.read(File.expand_path(path))
    t = ERB.new(content)
    t.result(binding)
  end
end
