#!/usr/bin/ruby
require "rss"

class TodoFeed
    def initialize(items, title)
        rss = RSS::Maker.make("2.0") do |maker|
          maker.channel.title = title
          maker.channel.description = '%s feed' % title
          maker.channel.link = "http://udd.debian.org/"
          date = Time.at(0)

          items.each do |e|
              maker.items.new_item do |item|
                item.link = e[:link]
                item.title = e[:title]
                d = e[:updated] || Time.now
                date = d if d > date
                item.updated = d.to_s
              end
          end
          maker.channel.updated = date.to_s
        end
        puts "Content-type: text/xml\n\n"
        puts rss.to_s
    end
end
