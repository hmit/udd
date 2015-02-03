#!/usr/bin/ruby
require 'cgi'
require 'uri'
require 'yaml'
$LOAD_PATH.unshift File.dirname(__FILE__) + '/inc'
require 'dmd-data'
require 'page'

STDERR.reopen(STDOUT) # makes live debugging much easier

cgi = CGI::new
tstart = Time::now

three = {'1' => '', '2' => '', '3' => ''}
params = {'email'       => three.clone,
          'nosponsor'   => three.clone,
          'nouploader'  => three.clone,
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
['packages', 'bin2src', 'ignpackages', 'ignbin2src'].each do |s|
  p = cgi.params[s][0]
  params[s] = CGI.escapeHTML(p) if p
end


if cgi.params != {}
  emails = {}

  # for compatibility purposes
  if cgi.params["email"][0] and cgi.params["email"][0] != ''
    emails[cgi.params["email"][0]] = [ :maintainer, :uploader, :sponsor ]
  end

  [1, 2, 3].each do |i|
    if cgi.params["email#{i}"][0] and cgi.params["email#{i}"][0] != ''
      em = cgi.params["email#{i}"][0]
      types = [ :maintainer, :uploader, :sponsor ]
      types.delete(:uploader) if cgi.params["nouploader#{i}"][0] == 'on'
      types.delete(:sponsor) if cgi.params["nosponsor#{i}"][0] == 'on'
      parsed_emails[email] = types
    end
  end
  $uddd = UDDData::new(parsed_emails, cgi.params["packages"][0] || "", cgi.params["bin2src"][0] == 'on', cgi.params["ignpackages"][0] || "", cgi.params["ignbin2src"][0] == 'on')

  $uddd.get_sources
  $uddd.get_sources_status
  $uddd.get_autoremovals
  $uddd.get_dmd_todos
  $uddd.get_ubuntu_bugs

  feeditems = []
  $uddd.dmd_todos.each do |t|
  feeditems.push({:link  => "%s" % t[:link],
                :title => "%s: %s: %s" % [t[:source], t[:description], t[:details]],
                :updated => t[:updated] })
  end

  def src_reason(pkg)
    s = $uddd.sources[pkg]
    raise "bug!" if s.nil?
    if s[0] == :manually_listed
      return "Manually listed"
    elsif s[0] == :maintainer
      return "Maintained by #{s[1]}"
    elsif s[0] == :uploader
      return "Co-maintained by #{s[1]}"
    elsif s[0] == :sponsor
      return "Was uploaded by #{s[1]}"
    end
  end

  $uddd.dmd_todos.each do |t|
    pkg = t[:source]
    t[:reason] = src_reason(pkg)
  end

  $uddd.sources.each do |s|
    h = Hash.new
    src = s[0]
    reason = src_reason(src)
    h[src] = Hash.new
    h[src][:reason] = reason

    next if not $uddd.versions[src]
    dv = $uddd.versions[src]['debian']
    t_oldstable = t_stable = t_testing = t_unstable = t_experimental = t_vcs = ''

    t_oldstable += dv['squeeze'][:version] if dv['squeeze']
    t_oldstable += "<br>sec: #{dv['squeeze-security'][:version]}" if dv['squeeze-security']
    t_oldstable += "<br>upd: #{dv['squeeze-updates'][:version]}" if dv['squeeze-updates']
    t_oldstable += "<br>pu: #{dv['squeeze-proposed-updates'][:version]}" if dv['squeeze-proposed-updates']
    t_oldstable += "<br>bpo: #{dv['squeeze-backports'][:version]}" if dv['squeeze-backports']
    t_oldstable += "<br>bpo-sl: #{dv['squeeze-backports-sloppy'][:version]}" if dv['squeeze-backports-sloppy']

    t_stable += dv['wheezy'][:version] if dv['wheezy']
    t_stable += "<br>sec: #{dv['wheezy-security'][:version]}" if dv['wheezy-security']
    t_stable += "<br>upd: #{dv['wheezy-updates'][:version]}" if dv['wheezy-updates']
    t_stable += "<br>pu: #{dv['wheezy-proposed-updates'][:version]}" if dv['wheezy-proposed-updates']
    t_stable += "<br>bpo: #{dv['wheezy-backports'][:version]}" if dv['wheezy-backports']
    t_stable += "<br>bpo-sl: #{dv['wheezy-backports-sloppy'][:version]}" if dv['wheezy-backports-sloppy']

    t_testing += dv['jessie'][:version] if dv['jessie']
    t_testing += "<br>sec: #{dv['jessie-security'][:version]}" if dv['jessie-security']
    t_testing += "<br>upd: #{dv['jessie-updates'][:version]}" if dv['jessie-updates']
    t_testing += "<br>pu: #{dv['jessie-proposed-updates'][:version]}" if dv['jessie-proposed-updates']

    if dv['sid']
      t_unstable += dv['sid'][:version]
      sid = dv['sid'][:version]
    else
      sid = ''
    end

    if dv['experimental']
      t_experimental += dv['experimental'][:version]
      exp = dv['experimental'][:version]
    else
      exp = ''
    end

    vcs = $uddd.versions[src]['vcs']
    if vcs
      t = UDDData.compare_versions(sid, vcs[:version])
      te = UDDData.compare_versions(exp, vcs[:version])
      if (t == -1 or te == -1) and t != 0 and te != 0 and ['unstable', 'experimental'].include?(vcs[:distribution])
        t_vcs += "<a href=\"https://qa.debian.org/cgi-bin/vcswatch?package=#{src}\"><span class=\"prio_high\" title=\"Ready for upload to #{vcs[:distribution]}\">#{vcs[:version]}</span></a>"
      elsif (t == -1 or te == -1) and t != 0 and te != 0
        t_vcs += "<a href=\"https://qa.debian.org/cgi-bin/vcswatch?package=#{src}\"><span class=\"prio_med\" title=\"Work in progress\">#{vcs[:version]}</span></a>"
      elsif t == 1 and te == 1
        t_vcs += "<a href=\"https://qa.debian.org/cgi-bin/vcswatch?package=#{src}\"><span class=\"prio_high\" title=\"Version in archive newer than version in VCS\">#{vcs[:version]}</span></a>"
      else
        t_vcs += "#{vcs[:version]}"
      end
    end

    h[src][:versions] = UDDData.group_values(t_oldstable, t_stable, t_testing, t_unstable, t_experimental, t_vcs)
    $uddd.sources[src] = h[src]
  end


  $ubuntu = Array.new
  ur = YAML::load(IO::read('ubuntu-releases.yaml'))
  USTB = ur['stable']
  UDEV = ur['devel']
  $uddd.sources.keys.sort.each do |src|
    next if not $uddd.versions.include?(src)
    next if (not $uddd.versions[src].include?('debian') or not $uddd.versions[src].include?('ubuntu'))

    ub = $uddd.ubuntu_bugs[src]
    if ub.nil?
      bugs = 0
      patches = 0
    else
      bugs = ub[:bugs]
      patches = ub[:patches]
    end

    dv = $uddd.versions[src]['debian']
    if dv['sid']
      sid = dv['sid'][:version]
    else
      sid = ''
    end

    du = $uddd.versions[src]['ubuntu']
    ustb = ''
    udev = ''
    if not du.nil?
      ustb = du[USTB][:version] if du[USTB]
      ustb += "<br>sec:&nbsp;#{du["#{USTB}-security"][:version]}" if du["#{USTB}-security"]
      ustb += "<br>upd:&nbsp;#{du["#{USTB}-updates"][:version]}" if du["#{USTB}-updates"]
      ustb += "<br>prop:&nbsp;#{du["#{USTB}-proposed"][:version]}" if du["#{USTB}-proposed"]
      ustb += "<br>bpo:&nbsp;#{du["#{USTB}-backports"][:version]}" if du["#{USTB}-backports"]

      udev = du[UDEV][:version] if du[UDEV]
      if udev == sid
        if bugs == 0 and patches == 0
          next
        end
      elsif sid != ''
        if UDDData.compare_versions(udev, sid) == -1
          if udev =~ /ubuntu/
            udev = "<a href=\"http://ubuntudiff.debian.net/?query=-FPackage+#{src}\"><span class=\"prio_high\" title=\"Outdated version in Ubuntu, with an Ubuntu patch\">#{udev}</span></a>"
          else
            udev = "<span class=\"prio_med\" title=\"Outdated version in Ubuntu\">#{udev}</span>"
          end
        elsif UDDData.compare_versions(udev, sid) == 1
          udevnb = udev.gsub(/build\d+$/,'')
          if UDDData.compare_versions(udevnb, sid) == 1
            udev = "<a href=\"http://ubuntudiff.debian.net/?query=-FPackage+#{src}\"><span class=\"prio_high\" title=\"Newer version in Ubuntu\">#{udev}</span></a>"
          end
        end
      end
      udev += "<br>sec:&nbsp;#{du["#{UDEV}-security"][:version]}" if du["#{UDEV}-security"]
      udev += "<br>upd:&nbsp;#{du["#{UDEV}-updates"][:version]}" if du["#{UDEV}-updates"]
      udev += "<br>prop:&nbsp;#{du["#{UDEV}-proposed"][:version]}" if du["#{UDEV}-proposed"]
      udev += "<br>bpo:&nbsp;#{du["#{UDEV}-backports"][:version]}" if du["#{UDEV}-backports"]
    end

    values = UDDData.group_values(ustb, udev, sid)
    $ubuntu.push({:src => src,
                  :bugs => bugs,
                  :patches => patches,
                  :pts => "https://tracker.debian.org/#{src}",
                  :launchpad => "https://bugs.launchpad.net/ubuntu/+source/#{src}",
                  :values => values
    })
    $ustb = USTB
    $udev = UDEV
  end

  data = $uddd.dmd_todos
end

format = cgi.params['format'][0]
page = Page.new(data, format, 'templates/dmd.erb',
                {:params => params,
                 :uddd => $uddd,
                 :ubuntu => $ubuntu,
                 :USTB => $ustb,
                 :UDEV => $udev,
                 :tstart => tstart },
               'Debian Maintainer Dashboard', feeditems)
page.render()
