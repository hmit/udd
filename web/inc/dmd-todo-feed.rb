require "rss"

class TodoFeed
    def initialize(items)
        rss = RSS::Maker.make("atom") do |maker|
          maker.channel.author = "Debian Maintainer Dashboard"
          maker.channel.updated = Time.now.to_s
          maker.channel.about = "http://www.ruby-lang.org/en/feeds/news.rss"
          maker.channel.title = "DMD Todo List"

          items.each do |e|
              maker.items.new_item do |item|
                item.link = e[:link]
                item.title = e[:title]
                item.updated = Time.now.to_s
              end
          end
        end
        puts "Content-type: text/xml\n\n"
        puts rss.to_s
    end
end
