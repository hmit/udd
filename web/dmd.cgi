#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
require 'cgi'
require 'time'

tstart = Time::now

# testing migration checks
MIN_AGE_IN_DEBIAN = 11
MIN_SYNC_INTERVAL = 11

puts "Content-type: text/html\n\n"
STDERR.reopen(STDOUT) # makes live debugging much easier

pw = IO::read('/srv/udd.debian.org/guestdd-password').chomp
$dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guestdd', pw)
$dbh.execute("SET statement_timeout TO 5000")

### begin of MODEL functions

class DateTime
  def to_date
    return Date::new(year, month, day)
  end
end

class UDDData
  attr_accessor :debug
  attr_reader :sources, :versions, :all_bugs, :bugs_tags, :bugs_count, :migration, :buildd, :dmd_todos

  def initialize(emails)
    @debug = false
    @emails = emails
  end

  def get_sources
    maint_emails = @emails.reject { |k, v| not v.include?(:maintainer) }.keys
    if not maint_emails.empty?
      q = <<-EOF
    select distinct source, maintainer_email from sources_uniq where release in ('sid', 'experimental', 'wheezy', 'squeeze') and maintainer_email in (#{maint_emails.map { |e| quote(e) }.join(',')})
      EOF
      maint_rows = dbget(q)
    else
      maint_rows = []
    end

    upload_emails = @emails.reject { |k, v| not v.include?(:uploader) }.keys
    if not upload_emails.empty?
      q = <<-EOF
    select distinct source, email from uploaders where release in ('sid', 'experimental', 'wheezy', 'squeeze') and email in (#{upload_emails.map { |e| quote(e) }.join(',')})
      EOF
      upload_rows = dbget(q)
    else
      upload_rows = []
    end

    pts_emails = @emails.reject { |k, v| not v.include?(:pts) }.keys
    if not pts_emails.empty?
      q = <<-EOF
    select distinct source, email from pts where email in (#{pts_emails.map { |e| quote(e) }.join(',')})
      EOF
      pts_rows = dbget(q)
    else
      pts_rows = []
    end

    srcs = {}
    pts_rows.each { |p| srcs[p[0]] = [:pts, p[1]] }
    upload_rows.each { |p| srcs[p[0]] = [:uploader, p[1]] }
    maint_rows.each { |p| srcs[p[0]] = [:maintainer, p[1]] }
    @sources = srcs
  end

  def get_sources_versions
    srcs = @sources.keys
    # versions in archives
    q = "select source, version, distribution, release, component from sources_uniq where source in (#{srcs.map { |e| quote(e) }.join(',')})"
    rows = dbget(q)
    q = "select source, version, distribution, release, component from ubuntu_sources where source in (#{srcs.map { |e| quote(e) }.join(',')})"
    rows += dbget(q)

    @versions = {}
    rows.each do |r|
      @versions[r['source']] ||= {}
      @versions[r['source']][r['distribution']] ||= {}
      @versions[r['source']][r['distribution']][r['release']] = { :version => r['version'], :component => r['component'] }
    end

    # upstream versions
    q = "select source, upstream_version, status from upstream where source in (#{srcs.map { |e| quote(e) }.join(',')}) and status is not null"
    rows = dbget(q)
    rows.each do |r|
      st = case r['status']
        when 'up to date': :up_to_date
        when 'Debian version newer than remote site': :newer_in_debian
        when 'Newer version available': :out_of_date
        when 'error': :error
        else nil
      end
      @versions[r['source']]['upstream'] = { :status => st, :version => r['upstream_version'] }
    end
    
    # vcs versions
    q = "select source, team, version, distribution from vcs where source in (#{srcs.map { |e| quote(e) }.join(',')})"
    rows = dbget(q)
    rows.each do |r|
      @versions[r['source']]['vcs'] = { :team => r['team'], :version => r['version'], :distribution => r['distribution'] }
    end

    q = <<-EOF
select source, team, version from vcs
where source in (#{srcs.map { |e| quote(e) }.join(',')})
and distribution!='UNRELEASED' and version > coalesce((select version from sources_uniq where release='sid' and sources_uniq.source = vcs.source), 0::debversion)
EOF
    @ready_for_upload = {}
    dbget(q).each do |r|
      @ready_for_upload[r['source']] = r.to_h
    end
  end

  def get_sources_bugs
    srcs = @sources.keys
    q = "select id, package, source, severity, title, last_modified, affects_stable, affects_testing, affects_unstable, affects_experimental, status from bugs where source in (#{srcs.map { |e| quote(e) }.join(',')})"
    allbugs = dbget(q)
    @all_bugs = allbugs.map { |r| r.to_h }
    ids = @all_bugs.map { |e| e['id'] }
    @bugs_tags = {}
    ids.each do |id|
      @bugs_tags[id] = []
    end
    tags = dbget("select id, tag from bugs_tags where id in (#{ids.join(',')})")
    tags.each do |r|
      @bugs_tags[r['id']] << r['tag']
    end
    # get release team status for bugs
    ['testing', 'unstable'].each do |rel|
      dbget("select id from bugs_rt_affects_#{rel} where id in (#{ids.join(',')})").each do |r|
        @bugs_tags[r['id']] << "rt_affects_#{rel}"
      end
    end

    @bugs_count = {}
    @all_bugs.group_by { |b| b['source'] }.each_pair do |src, bugs|
      openbugs = bugs.select { |b| b['status'] != 'done' }
      rc_bugs = openbugs.select { |b| ['serious', 'grave', 'critical'].include?(b['severity']) }.count
      patches = openbugs.select { |b| (@bugs_tags[b['id']] || []).include?('patch') }.count
      pending = openbugs.select { |b| (@bugs_tags[b['id']] || []).include?('pending') }.count
      @bugs_count[src] = { :rc => rc_bugs, :all => openbugs.count, :patch => patches, :pending => pending }
    end
  end
  
  def get_migration
    srcs = @sources.keys.map { |e| quote(e) }.join(',')
    q = "select source, in_testing, current_date - in_testing as in_testing_age, sync, current_date - sync as sync_age, current_date - first_seen as debian_age from migrations where current_date - in_unstable < 2 and (sync is null or current_date - sync > 1) and source in (#{srcs})"
    rows = dbget(q)
    @migration = {}
    rows.each do |r|
      @migration[r['source']] = {}
      @migration[r['source']]['in_testing_age'] = r['in_testing_age']
      @migration[r['source']]['in_testing'] = r['in_testing'] ? r['in_testing'].to_date : nil
      @migration[r['source']]['debian_age'] = r['debian_age']
      @migration[r['source']]['sync'] = r['sync'] ? r['sync'].to_date : nil
      @migration[r['source']]['sync_age'] = r['sync_age']
    end
  end

  def get_buildd
    srcs = @sources.keys.map { |e| quote(e) }.join(',')
    q = "select source, architecture, state, state_change from wannabuild where distribution='sid' and state not in ('Installed', 'Needs-Build', 'Dep-Wait', 'Not-For-Us', 'Auto-Not-For-Us') and (state not in ('Built', 'Uploaded') or now() - state_change > interval '2 days') and architecture not in ('hurd-i386') and notes <> 'uncompiled' and source in (#{srcs})"
    rows = dbget(q)
    @buildd = {}
    rows.each do |r|
      @buildd[r['source']] ||= []
      @buildd[r['source']] << r.to_h
    end
  end

  def get_sources_status
    get_sources_versions
    get_sources_bugs
    get_migration
    #@debug = true
    get_buildd
  end

  def get_dmd_todos
    @dmd_todos = []
    rc_bugs = @all_bugs.select { |b| ['serious', 'grave', 'critical'].include?(b['severity']) }
    rc_bugs.each do |bug|
      id = bug['id']
      if bug['status'] == 'done' and @bugs_tags[id].include?('rt_affects_unstable')
        @dmd_todos << { :type => 'RC bug', :source => bug['source'],
          :description => "RC bug marked as done but still affects unstable: ##{id}: #{bug['title']}" }
      elsif (not @bugs_tags[id].include?('rt_affects_unstable')) and @bugs_tags[id].include?('rt_affects_testing')
        @dmd_todos << { :type => 'RC bug', :source => bug['source'],
                        :description => "RC bug affecting testing only (ensure the package migrates): ##{id}: #{bug['title']}" }
      elsif @bugs_tags[id].include?('rt_affects_unstable') or @bugs_tags[id].include?('rt_affects_testing')
        @dmd_todos << { :type => 'RC bug', :source => bug['source'],
                        :description => "RC bug needs fixing: ##{id}: #{bug['title']}" }
      end
    end

    @buildd.each_pair do |src, archs|
      archs.each do |arch|
        @dmd_todos << { :type => 'missing build', :source => src,
                        :description => "Missing build on #{arch['architecture']}. state <i>#{arch['state']}</i> since #{arch['state_change'].to_date.to_s}" }
      end
    end

    @migration.each_pair do |src, v|
      if v['in_testing_age'].nil?
        if v['debian_age'] > MIN_AGE_IN_DEBIAN
        @dmd_todos << { :type => 'testing migration', :source => src,
                        :description => "Has been in Debian for #{v['debian_age']}, but never migrated to testing" }
        end
      elsif v['in_testing_age'] > 1 # in case there's some incoherency in udd
        @dmd_todos << { :type => 'testing migration', :source => src,
                        :description => "Not in testing for #{v['in_testing_age']} days" }
      else
        if v['sync_age'].nil?
          #        puts "Interesting buggy case with #{pkg}. Ignore."
        elsif v['sync_age'] > MIN_SYNC_INTERVAL
        @dmd_todos << { :type => 'testing migration', :source => src,
                        :description => "Has been trying to migrate for #{v['sync_age']} days" }
        end
      end
    end

    @ready_for_upload.each_pair do |src, v|
        @dmd_todos << { :type => 'vcs', :source => src,
                        :description => "new version #{v['version']} ready for upload in the #{v['team']} repository" }
    end

    @versions.each_pair do |src, v|
      next if not v.has_key?('upstream')
      next if v['upstream'][:status] != :out_of_date
      @dmd_todos << { :type => 'new upstream', :source => src,
                      :description => "new upstream version available: #{v['upstream'][:version]}" }
    end


    @dmd_todos
  end

  private
  def dbget(q, *args)
    if @debug
      puts "<pre>#{q}</pre>"
      p args if not args.nil?
    end
    rows, sth = nil
    duration = DBI::Utils::measure do 
      sth = $dbh.prepare(q)
      sth.execute(*args)
      rows = sth.fetch_all
    end
    if @debug
      puts "### #{duration}s"
      puts "<pre>"
      puts DBI::Utils::TableFormatter.ascii(sth.column_names, rows)
      puts "</pre>"
    end
    return rows
  end

  def quote(s)
    DBI::DBD::Pg::quote(s)
  end
end


cgi = CGI::new

puts <<-EOF
<html>
<head>
<style type="text/css">

  body {
    font-family : "DejaVu Sans", "Bitstream Vera Sans", sans-serif;"
  }

  table.buglist td, table.buglist th {
    border: 1px solid gray;
    padding-left: 3px;
    padding-right: 3px;
  }
  table.buglist tr:hover  {
    background-color: #ccc;
    color: #000;
  }
  table.buglist tr:hover :link {
    color: #00f;
  }
  table.buglist tr:hover :visited {
    color: #707;
  }
  table {
    border-collapse: collapse;
  }

div#body {
  border-top: 2px solid #d70751;
}

div.footer {
    padding: 0.3em 0;
    background-color: #fff;
    color: #000;
    text-align: center;
    border-top: 2px solid #d70751;
    margin: 0 0 0 0;
    border-bottom: 0;
    font-size: 85%;
}
  div.footer :link {
    color: #00f;
  }
  div.footer :visited {
    color: #707;
  }
</style>
<title>Debian Maintainer Dashboard @ UDD</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<script type="text/javascript">
function removeBlankFields(form) {
	var inputs = form.getElementsByTagName("input");
	var removeList = new Array();
	for (var i=0; i<inputs.length; i++) {
		if (inputs[i].value == "") {
			removeList.push(inputs[i]);
		}
	}
	for (x in removeList) {
		removeList[x].parentNode.removeChild(removeList[x]);
	}
}
</script>
</head>
<body>
<h1 style="margin-bottom : 5px"><img src="http://qa.debian.org/debian.png" alt="Debian logo" width="188" height="52" style="vertical-align : -13px; ">Maintainer Dashboard <span style="color :#c70036">@</span> UDD</h1>
<div id="body">

EOF
puts <<-EOF
<br/>
<form action="dmd.cgi" method="get">
email: <input type='text' size='100' name='email' value='pkg-ruby-extras-maintainers@lists.alioth.debian.org'/>
<input type='submit' value='Go'/>
</form>
EOF

if cgi.params != {}
  emails = { cgi.params['email'][0] => [:maintainer, :uploader, :pts]}
  uddd = UDDData::new(emails)
  uddd.get_sources
  uddd.get_sources_status
  uddd.get_dmd_todos
  #puts "<pre>"
  #pp uddd.sources
  #pp uddd.versions
  #pp uddd.all_bugs
  #pp uddd.bugs_tags
  #pp uddd.bugs_count
  #pp uddd.migration
  #pp uddd.buildd
  #puts "</pre>"

  puts "<h1>TODO items</h1>"
  puts <<-EOF
<table class="buglist">
<tr>
<th>type</th><th>source</th><th>description</th>
</tr>
  EOF
  uddd.dmd_todos.each do |t|
    puts "<tr><td>#{t[:type]}</td><td>#{t[:source]}</td><td>#{t[:description]}</td></tr>"
  end
  puts "</table>"

  puts "<h1>Versions</h1>"

  puts <<-EOF
<table class="buglist">
<tr>
<th>source</th><th>squeeze</th><th>wheezy</th><th>sid</th><th>experimental</th>
<th>precise</th><th>quantal</th>
<th>upstream</th><th>vcs</th>
</tr>
  EOF
  #pp uddd.versions
  #pp uddd.versions.map { |k, v| (v['debian'] || {} ).keys }.uniq
  #pp uddd.versions.map { |k, v| (v['ubuntu'] || {} ).keys }.uniq
  uddd.sources.keys.sort.each do |src|
    next if not uddd.versions.include?(src)
    next if not uddd.versions[src].include?('debian')
    dv = uddd.versions[src]['debian']
    puts "<tr><td>#{src}</td>"

    puts "<td>"
    puts dv['squeeze'][:version] if dv['squeeze']
    puts "<br>sec: #{dv['squeeze-security'][:version]}" if dv['squeeze-security']
    puts "<br>pu: #{dv['squeeze-proposed-updates'][:version]}" if dv['squeeze-proposed-updates']
    puts "<br>bpo: #{dv['squeeze-backports'][:version]}" if dv['squeeze-backports']
    puts "</td>"

    puts "<td>"
    puts dv['wheezy'][:version] if dv['wheezy']
    puts "<br>sec: #{dv['wheezy-security'][:version]}" if dv['wheezy-security']
    puts "<br>pu: #{dv['wheezy-proposed-updates'][:version]}" if dv['wheezy-proposed-updates']
    puts "</td>"

    puts "<td>"
    puts dv['sid'][:version] if dv['sid']
    puts "</td>"

    puts "<td>"
    puts dv['experimental'][:version] if dv['experimental']
    puts "</td>"

    du = uddd.versions[src]['ubuntu']
    if du.nil?
      puts "<td></td><td></td>"
    else
      puts "<td>"
      puts du['precise'][:version] if du['precise']
      puts "</td>"

      puts "<td>"
      puts du['quantal'][:version] if du['quantal']
      puts "</td>"
    end

    up = uddd.versions[src]['upstream']
    puts "<td>"
    puts "#{up[:version]} (#{up[:status]})" if up
    puts "</td>"

    vcs = uddd.versions[src]['vcs']
    puts "<td>"
    # FIXME show status
    puts "#{vcs[:version]}" if vcs
    puts "</td>"


    puts "</tr>"
  end
  puts "</table>"

  puts "<h1>Bugs</h1>"
  puts <<-EOF
<table class="buglist">
<tr>
<th>source</th><th>all</th><th>RC</th><th>with patch</th><th>pending</th>
</tr>
  EOF
  bc = uddd.bugs_count
  bc.keys.sort.each do |src|
    b = bc[src]
    next if b[:all] == 0
    puts "<tr><td>#{src}</td><td>#{b[:all]}</td><td>#{b[:rc]}</td><td>#{b[:patch]}</td><td>#{b[:pending]}</td></tr>"
  end
  puts "</table>"

  puts "<p><b>Generated in #{Time::now - tstart} seconds.</b></p>"

end

puts <<-EOF
<div class="footer">
<small>Suggestions / comments / patches to lucas@debian.org. <a href="http://anonscm.debian.org/gitweb/?p=collab-qa/udd.git;a=history;f=web/dmd.cgi">source code</a>.</small>
</div>
EOF

puts "</body></html>"
