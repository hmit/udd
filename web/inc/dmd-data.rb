#!/usr/bin/ruby
require 'dbi'
require 'pp'
require 'time'

# testing migration checks
MIN_AGE_IN_DEBIAN = 11
MIN_SYNC_INTERVAL = 11

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

    if File::exists?('/srv/udd.debian.org/guestdd-password') # we are on udd
      pw = IO::read('/srv/udd.debian.org/guestdd-password').chomp
      @dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guestdd', pw)
    else
      @dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=udd.debian.org', 'guest')
    end
    @dbh.execute("SET statement_timeout TO 5000")
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
        when 'up to date' then :up_to_date
        when 'Debian version newer than remote site' then :newer_in_debian
        when 'Newer version available' then :out_of_date
        when 'error' then :error
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
      sth = @dbh.prepare(q)
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
