#!/usr/bin/ruby
$LOAD_PATH.unshift File.dirname(__FILE__) + '/inc'
#STDERR.reopen(STDOUT) #makes live debugging easier
require 'dmd-data'

now = Time::now
cgi = CGI::new
three = {'1' => '', '2' => '', '3' => ''}
params = {'email'       => three.clone,
          'nosponsor'   => three.clone,
          'nouploader'  => three.clone,
          'emails'      => {},
          'packages'    => '',
          'bin2src'     => '',
          'ignpackages' => '',
          'ignbin2src'  => ''}
['email', 'nosponsor', 'nouploader'].each do |s|
  params[s].each do |k, v|
    p = cgi.params[s + k][0]
    params[s][k] = CGI.escapeHTML(p) if p
  end
end
params['email'].each do |k, v|
  roles = [:maintainer, :uploader, :sponsor]
  roles.delete(:uploader) if params['nouploader'][k] == 'on'
  roles.delete(:sponsor) if params['nosponsor'][k] == 'on'
  params['emails'][v] = roles
end
['packages', 'bin2src', 'ignpackages', 'ignbin2src'].each do |s|
  p = cgi.params[s][0]
  params[s] = CGI.escapeHTML(p) if p
end

if cgi.params != {}
  uddd = UDDData::new(
      params['emails'],
      params['packages'],
      params['bin2src'] == 'on',
      params['ignpackages'],
      params['ignbin2src'] == 'on')

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
