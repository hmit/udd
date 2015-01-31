#!/usr/bin/ruby
require 'vpim/icalendar'
require 'vpim/vtodo'
require 'date'

# Note:
#
# Requires the vpim package.
#
# The VTODO support in the Vpim code is not quite as polished
# as the VEVENT support.  For example, there is a convenient
# add_event() method for VEVENT but there is no add_todo()
# so we have to create the VTODO using the create() method.
# Rendering of the required VTODO fields appears to work fine.

class TodoCalendar
    def initialize(items, title)
        cal = Vpim::Icalendar.create2

        items.each do |e|
          t = Vpim::Icalendar::Vtodo.create(
            'SUMMARY' => e[:title],
            'DESCRIPTION' => e[:title],
            'URL' => e[:link],
            'ORGANIZER' => 'debian-qa@lists.debian.org')
          cal.push(t)
        end
        puts "Content-type: text/calendar\n"
        puts "Content-Disposition: attachment; filename=\"dmd.ics\"\n\n"
        puts cal.encode
    end
end
