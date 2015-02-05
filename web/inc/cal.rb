#!/usr/bin/ruby

# Hack: the wheezy version of vpim is broken (it does not support ruby1.9)
# so we just add the 1.8 path to the load path
$:.unshift '/usr/lib/ruby/1.8/'
require 'vpim/icalendar'
require 'vpim/vtodo'
# </hack>
$:.delete('/usr/lib/ruby/1.8/')

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
