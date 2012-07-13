#!/usr/bin/ruby
require 'dbi'
require 'pp'
require 'time'
require 'debian'

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
  attr_reader :sources, :versions, :all_bugs, :bugs_tags, :bugs_count, :migration, :buildd, :dmd_todos, :ubuntu_bugs

  def initialize(emails = {})
    @debug = false
    @emails = emails

    @dbh = nil
    begin
      @dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
    rescue DBI::OperationalError
      puts "Could not connect to database:<pre>"
      puts $!
      puts "</pre>"
      exit(0)
    end
    @dbh.execute("SET statement_timeout TO 5000")
  end

  def get_sources
    dbget("create temporary table mysources(source text)")

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

    srcs = {}
    upload_rows.each { |p| srcs[p[0]] = [:uploader, p[1]] }
    maint_rows.each { |p| srcs[p[0]] = [:maintainer, p[1]] }

    dbget("insert into mysources values (#{srcs.keys.map { |e| quote(e) }.join('),(')})")

    @sources = srcs
  end

  def get_sources_versions
    @versions = {}
    @ready_for_upload = {}
    return @versions if @sources.empty?
    # versions in archives
    q = "select source, version, distribution, release, component from sources_uniq where source in (select source from mysources)"
    rows = dbget(q)
    q = "select source, version, distribution, release, component from ubuntu_sources where source in (select source from mysources)"
    rows += dbget(q)

    rows.each do |r|
      @versions[r['source']] ||= {}
      @versions[r['source']][r['distribution']] ||= {}
      @versions[r['source']][r['distribution']][r['release']] = { :version => r['version'], :component => r['component'] }
    end

    # upstream versions
    q = "select source, upstream_version, status from upstream where source in (select source from mysources) and status is not null"
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
    q = "select source, team, version, distribution from vcs where source in (select source from mysources)"
    rows = dbget(q)
    rows.each do |r|
      @versions[r['source']]['vcs'] = { :team => r['team'], :version => r['version'], :distribution => r['distribution'] }
    end

    q = <<-EOF
select source, team, version from vcs
where source in (select source from mysources)
and distribution!='UNRELEASED' and version > coalesce((select version from sources_uniq where release='sid' and sources_uniq.source = vcs.source), 0::debversion)
EOF
    dbget(q).each do |r|
      @ready_for_upload[r['source']] = r.to_h
    end
  end

  def get_ubuntu_bugs
    @ubuntu_bugs = {}
    return @ubuntu_bugs if @sources.empty?
    srcs = @sources.keys.map { |e| quote(e) }.join(',')
    q=<<-EOF
SELECT tbugs.package, bugs, patches
from (select package, count(distinct bugs.bug) as bugs
from ubuntu_bugs_tasks tasks,ubuntu_bugs bugs
where tasks.bug = bugs.bug
and distro in ('Ubuntu')
and status not in ('Invalid', 'Fix Released', 'Won''t Fix', 'Opinion')
and package in (select source from mysources)
group by package) tbugs
full join
(select package, count(distinct bugs.bug) as patches
from ubuntu_bugs_tasks tasks,ubuntu_bugs bugs
where tasks.bug = bugs.bug
and distro in ('', 'Ubuntu')
and status not in ('Invalid', 'Fix Released', 'Won''t Fix', 'Opinion')
and bugs.patches is true
and package in (select source from mysources)
group by package) tpatches on tbugs.package = tpatches.package order by package asc
    EOF
    rows = dbget(q)
    rows.each do |r|
      @ubuntu_bugs[r['package']] = { :bugs => r['bugs'], :patches => r['patches'] || 0 }
    end
  end

  def get_sources_bugs
    @all_bugs = []
    @bugs_tags = {}
    @bugs_count = {}
    return if @sources.empty?
    srcs = @sources.keys
    q = "select id, package, source, severity, title, last_modified, affects_stable, affects_testing, affects_unstable, affects_experimental, status from bugs where source in (select source from mysources)"
    allbugs = dbget(q)
    @all_bugs = allbugs.map { |r| r.to_h }
    ids = @all_bugs.map { |e| e['id'] }
    @bugs_tags = {}
    if not ids.empty?
      ids.each do |id|
        @bugs_tags[id] = []
      end
      tags = dbget("select id, tag from bugs_tags where id in (#{ids.join(',')})")
      tags.each do |r|
        @bugs_tags[r['id']] << r['tag']
      end
      # get release team status for bugs
      ['stable', 'testing', 'unstable'].each do |rel|
        dbget("select id from bugs_rt_affects_#{rel} where id in (#{ids.join(',')})").each do |r|
          @bugs_tags[r['id']] << "rt_affects_#{rel}"
        end
      end
    end

    @all_bugs.group_by { |b| b['source'] }.each_pair do |src, bugs|
      openbugs = bugs.select { |b| b['status'] != 'done' }
      rc_bugs = openbugs.select { |b| ['serious', 'grave', 'critical'].include?(b['severity']) }.count
      patches = openbugs.select { |b| (@bugs_tags[b['id']] || []).include?('patch') }.count
      pending = openbugs.select { |b| (@bugs_tags[b['id']] || []).include?('pending') }.count
      @bugs_count[src] = { :rc => rc_bugs, :all => openbugs.count, :patch => patches, :pending => pending }
    end
  end
  
  def get_migration
    @migration = {}
    return if @sources.empty?
    q =<<-EOF
select source, in_testing, current_date - in_testing as in_testing_age, sync, current_date - sync as sync_age,
current_date - first_seen as debian_age
from migrations where current_date - in_unstable < 2 and (sync is null or current_date - sync > 1)
and source in (select source from mysources)
and source not in (select source from upload_history where date > (current_date - interval '10 days') and distribution='unstable')
    EOF
    rows = dbget(q)
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
    @buildd = {}
    return if @sources.empty?
    q = "select source, architecture, state, state_change from wannabuild where distribution='sid' and state not in ('Installed', 'Needs-Build', 'Dep-Wait', 'Not-For-Us', 'Auto-Not-For-Us') and (state not in ('Built', 'Uploaded') or now() - state_change > interval '2 days') and architecture not in ('hurd-i386') and notes <> 'uncompiled' and source in (select source from mysources)"
    rows = dbget(q)
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
    stable_rc_bugs = []
    rc_bugs.each do |bug|
      id = bug['id']
      if bug['status'] == 'done' and @bugs_tags[id].include?('rt_affects_unstable')
        @dmd_todos << { :type => 'RC bug', :source => bug['source'],
          :description => "RC bug marked as done but still affects unstable: <a href=\"http://bugs.debian.org/#{id}\">##{id}</a>: #{bug['title']}" }
      elsif (not @bugs_tags[id].include?('rt_affects_unstable')) and @bugs_tags[id].include?('rt_affects_testing')
        @dmd_todos << { :type => 'RC bug', :source => bug['source'],
                        :description => "RC bug affecting testing only (ensure the package migrates): <a href=\"http://bugs.debian.org/#{id}\">##{id}</a>: #{bug['title']}" }
      elsif @bugs_tags[id].include?('rt_affects_unstable') or @bugs_tags[id].include?('rt_affects_testing')
        @dmd_todos << { :type => 'RC bug', :source => bug['source'],
                        :description => "RC bug needs fixing: <a href=\"http://bugs.debian.org/#{id}\">##{id}</a>: #{bug['title']}" }
      elsif @bugs_tags[id].include?('rt_affects_stable')
        stable_rc_bugs << { :type => 'RC bug (stable)', :source => bug['source'],
                            :description => "RC bug affecting stable: <a href=\"http://bugs.debian.org/#{id}\">##{id}</a>: #{bug['title']}" }
      end
    end
    @dmd_todos.concat(stable_rc_bugs)

    @buildd.each_pair do |src, archs|
      archs.each do |arch|
        @dmd_todos << { :type => 'missing build', :source => src,
                        :description => "Missing build on #{arch['architecture']}. state <i>#{arch['state']}</i> since #{arch['state_change'].to_date.to_s} (see <a href=\"https://buildd.debian.org/status/package.php?p=#{src}\">buildd.d.o</a>)" }
      end
    end

    @migration.each_pair do |src, v|
      if v['in_testing_age'].nil?
        if v['debian_age'] > MIN_AGE_IN_DEBIAN
        @dmd_todos << { :type => 'testing migration', :source => src,
                        :description => "Has been in Debian for #{v['debian_age']} days, but never migrated to testing (see <a href=\"http://qa.debian.org/excuses.php?package=#{src}\">excuses</a>)" }
        end
      elsif v['in_testing_age'] > 1 # in case there's some incoherency in udd
        @dmd_todos << { :type => 'testing migration', :source => src,
                        :description => "Not in testing for #{v['in_testing_age']} days (see <a href=\"http://qa.debian.org/excuses.php?package=#{src}\">excuses</a>)" }
      else
        if v['sync_age'].nil?
          #        puts "Interesting buggy case with #{pkg}. Ignore."
        elsif v['sync_age'] > MIN_SYNC_INTERVAL
        @dmd_todos << { :type => 'testing migration', :source => src,
                        :description => "Has been trying to migrate for #{v['sync_age']} days (see <a href=\"http://qa.debian.org/excuses.php?package=#{src}\">excuses</a>)" }
        end
      end
    end

    @ready_for_upload.each_pair do |src, v|
        @dmd_todos << { :type => 'vcs', :source => src,
                        :description => "new version #{v['version']} ready for upload in the <a href=\"http://pet.debian.net/#{v['team']}/pet.cgi\">#{v['team']} repository</a>" }
    end

    @versions.each_pair do |src, v|
      next if not v.has_key?('upstream')
      next if v['upstream'][:status] != :out_of_date
      @dmd_todos << { :type => 'new upstream', :source => src,
                      :description => "new upstream version available: #{v['upstream'][:version]}" }
    end


    @dmd_todos
  end

  def complete_email(email)
    q = <<-EOF
SELECT DISTINCT value, label
FROM 
(SELECT maintainer_email AS value, maintainer AS label
from sources
where release in ('sid', 'experimental', 'wheezy', 'squeeze')
union
select email as value, uploader as label
from uploaders
where release in ('sid', 'experimental', 'wheezy', 'squeeze')
) emails
WHERE label LIKE ?
    EOF
    r = dbget(q, "%#{email}%")
    return r.map { |r| r.to_h }
  end

  def UDDData.compare_versions(v1, v2)
    if Debian::Dpkg::compare_versions(v1, 'lt', v2)
      return -1
    elsif Debian::Dpkg::compare_versions(v1, 'eq', v2)
      return 0
    else
      return 1
    end
  end

  def UDDData.group_values(*values)
    agg = []
    values.each do |v|
      if agg.empty? or v != agg.last[:value]
        agg << { :value => v, :count => 1 }
      else
        agg.last[:count] += 1
      end
    end
    return agg
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
