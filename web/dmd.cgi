#!/usr/bin/ruby
$LOAD_PATH.unshift File.dirname(__FILE__) + '/inc'
#STDERR.reopen(STDOUT) #makes live debugging easier
require 'dmd-data'

now = Time::now
cgi = CGI::new
params = UDDData.parse_cgi_params(cgi.params)

if cgi.params != {}
  uddd = UDDData::new(
      params['emails'],
      params['packages'],
      params['bin2src'] == 'on',
      params['ignpackages'],
      params['ignbin2src'] == 'on',
      cgi.params['debug'][0] != nil)

  uddd.get_all_data

  feeditems = []
  uddd.dmd_todos.each do |t|
    feedtitle = "%s: %s: %s" % [t[:source], t[:description], t[:details]]
    feeditems.push({:link  => "%s" % t[:link],
                    :title => feedtitle,
                    :updated => t[:updated] })
  end
  data = uddd.dmd_todos
end

format = cgi.params['format'][0]
page = Page.new(
    data,
    format,
    'templates/dmd.erb',
    {:params => params, :uddd => uddd, :tstart => now },
    'Debian Maintainer Dashboard',
    feeditems)
page.render
