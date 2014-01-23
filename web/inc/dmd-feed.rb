#!/usr/bin/ruby
require "rss"

class TodoFeed
    def initialize(items)
        rss = RSS::Maker.make("2.0") do |maker|
          maker.channel.title = "Maintainer Todo List"
          maker.channel.description = "Debian Maintainer Dashboard Todo List"
          maker.channel.link = "http://udd.debian.org/dmd/"
          maker.channel.updated = Time.now.to_s

          items.each do |e|
              maker.items.new_item do |item|
                item.link = e[:link]
                item.title = e[:title]
                item.updated = Time.now.to_s
              end
          end
        end
        puts rss.to_s
    end
end
