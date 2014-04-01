#!/usr/bin/ruby
require 'dbi'
require 'pp'
require 'time'
require 'debian'
require 'digest/md5'

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
  attr_reader :sources, :versions, :all_bugs, :bugs_tags, :bugs_count, :migration, :buildd, :dmd_todos, :ubuntu_bugs, :autoremovals

  def initialize(emails = {}, addsources = "", bin2src = false, ignsources = "", ignbin2src = false)
    @debug = false
    @emails = emails
    @addsources = addsources
    @bin2src = bin2src
    @ignsources = ignsources
    @ignbin2src = ignbin2src

    @dbh = nil
    begin
      @dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
    rescue DBI::OperationalError
      puts "Could not connect to database:<pre>"
      puts $!
      puts "</pre>"
      exit(0)
    end
  end

  def get_sources
    dbget("create temporary table mysources(source text)")

    dbget <<-EOF
CREATE TEMPORARY VIEW sources_most_recent AS
select distinct source, version, maintainer_email from sources s1
where release in ('squeeze', 'wheezy', 'jessie', 'sid')
and not exists (select * from sources s2
where s1.source = s2.source
and release in ('squeeze', 'wheezy', 'jessie', 'sid')
and s2.version > s1.version);
    EOF

    maint_emails = @emails.reject { |k, v| not v.include?(:maintainer) }.keys
    if not maint_emails.empty?
      q = <<-EOF
    select distinct source, maintainer_email from sources_most_recent
    where maintainer_email in (#{maint_emails.map { |e| quote(e) }.join(',')})
    union
    select distinct source, maintainer_email from sources_uniq where release='experimental'
    and maintainer_email in (#{maint_emails.map { |e| quote(e) }.join(',')})
      EOF
      maint_rows = dbget(q)
    else
      maint_rows = []
    end

    dbget <<-EOF
CREATE TEMPORARY VIEW uploaders_most_recent AS
select distinct source, version, email from uploaders s1
where release in ('squeeze', 'wheezy', 'jessie', 'sid')
and not exists (select * from uploaders s2
where s1.source = s2.source
and release in ('squeeze', 'wheezy', 'jessie', 'sid')
and s2.version > s1.version);
    EOF

    upload_emails = @emails.reject { |k, v| not v.include?(:uploader) }.keys
    if not upload_emails.empty?
      q = <<-EOF
    select distinct source, email from uploaders_most_recent where email in (#{upload_emails.map { |e| quote(e) }.join(',')})
    union
    select distinct source, email from uploaders where release='experimental'
    and email in (#{upload_emails.map { |e| quote(e) }.join(',')})
      EOF
      upload_rows = dbget(q)
    else
      upload_rows = []
    end

    sponsor_emails = @emails.reject { |k, v| not v.include?(:sponsor) }.keys
    if not sponsor_emails.empty?
      q = <<-EOF
      select distinct source, key_id from upload_history uh, carnivore_emails ce, carnivore_keys ck
      where (source, version) in (
         select source, version from sources_most_recent
         union
         select source, version from sources_uniq where release='experimental'
      )
      and ce.email in (#{sponsor_emails.map { |e| quote(e) }.join(',')})
      and ce.id = ck.id
      and uh.fingerprint = ck.key
      EOF
      sponsor_rows = dbget(q)
    else
      sponsor_rows = []
    end

    srcs = {}
    sponsor_rows.each { |p| srcs[p[0]] = [:sponsor, p[1]] }
    upload_rows.each { |p| srcs[p[0]] = [:uploader, p[1]] }
    maint_rows.each { |p| srcs[p[0]] = [:maintainer, p[1]] }

    if @bin2src and @addsources != ''
      q = <<-EOF
      select distinct source from packages
         where package in (#{@addsources.split(/\s/).map { |e| quote(e) }.join(',')})
      EOF
      @addsources = dbget(q).map { |e| e[0] }
    else
      @addsources = @addsources.split(/\s/)
    end
    @addsources.each do |p|
      p.chomp!
      srcs[p] = [:manually_listed]
    end

    if @ignbin2src and @ignsources != ''
      q = <<-EOF
      select distinct source from packages
         where package in (#{@ignsources.split(/\s/).map { |e| quote(e) }.join(',')})
      EOF
      @ignsources = dbget(q).map { |e| e[0] }
    else
      @ignsources = @ignsources.split(/\s/)
    end
    @ignsources.each do |p|
      p.chomp!
      srcs.delete(p)
    end

    if not srcs.empty?
      dbget("insert into mysources values (#{srcs.keys.map { |e| quote(e) }.join('),(')})")
    end

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
    q = "select source, distribution, release, upstream_version, status from upstream where source in (select source from mysources) and status is not null"
    rows = dbget(q)
    rows.group_by { |r| r['source'] }.each_pair do |k, v|
      unst = v.select { |l| l['release'] == 'sid' }.first
      exp = v.select { |l| l['release'] == 'experimental' }.first
      if unst != nil and exp != nil
        us = unst['status']
        es = exp['status']
        if us == 'error' or es == 'error'
          st = :error
        elsif us == 'Debian version newer than remote site' or es == 'Debian version newer than remote site'
          st = :newer_in_debian
        elsif us == 'up to date'
          st = :up_to_date
        elsif es == 'up to date'
          st = :out_of_date_in_unstable
        else
          st = :out_of_date
        end
        @versions[unst['source']]['upstream'] = { :status => st, :version => unst['upstream_version'] }
      elsif unst.nil? and exp != nil
        r = exp
        st = case r['status']
             when 'up to date' then :up_to_date
             when 'Debian version newer than remote site' then :newer_in_debian
             when 'Newer version available' then :out_of_date_in_unstable
             when 'error' then :error
             else nil
             end
        @versions[r['source']]['upstream'] = { :status => st, :version => r['upstream_version'] }
      elsif unst != nil and exp == nil
        r = unst
        st = case r['status']
             when 'up to date' then :up_to_date
             when 'Debian version newer than remote site' then :newer_in_debian
             when 'Newer version available' then :out_of_date
             when 'error' then :error
             else nil
             end
        @versions[r['source']]['upstream'] = { :status => st, :version => r['upstream_version'] }
      else
        puts "ERROR"
        p v
        exit(1)
      end
    end

    rows.each do |r|
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
and source in (select source from sources_uniq where release in ('sid', 'experimental'))
and distribution!='UNRELEASED' and version > coalesce((select max(version) from sources_uniq where release in ('sid','experimental') and sources_uniq.source = vcs.source), 0::debversion)
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
select source, unstable_version, in_testing, current_date - in_testing as in_testing_age, sync, current_date - sync as sync_age,
current_date - first_seen as debian_age
from migrations where current_date - in_unstable < 2 and (sync is null or current_date - sync > 1)
and source in (select source from mysources)
and source not in (select source from upload_history where date > (current_date - interval '10 days') and distribution='unstable')
    EOF
    rows = dbget(q)
    rows.each do |r|
      @migration[r['source']] = {}
      @migration[r['source']]['unstable_version'] = r['unstable_version']
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

  def get_autoremovals
    @autoremovals = {}
    return if @sources.empty?
    q = "select source, version, bugs, removal_time from testing_autoremovals where source in (select source from mysources)"
    rows = dbget(q)
    rows.each do |r|
      @autoremovals[r['source']] = r.to_h
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
    testing_rc_bugs = []
    stable_rc_bugs = []
    rc_bugs.each do |bug|
      id = bug['id']
      h = Digest::MD5.hexdigest("#{bug['source']}_#{id}")
      if bug['status'] == 'done' and @bugs_tags[id].include?('rt_affects_unstable')
        @dmd_todos << { :shortname => "rc_done_#{h}",
                        :type => 'RC bug',
                        :source => bug['source'],
                        :link => "http://bugs.debian.org/#{id}",
                        :description => "RC bug marked as done but still affects unstable",
                        :details =>" ##{id}: #{bug['title']}" }
      elsif (not @bugs_tags[id].include?('rt_affects_unstable')) and @bugs_tags[id].include?('rt_affects_testing')
        testing_rc_bugs << { :shortname => "rc_testing_#{h}",
                             :type => 'RC bug',
                             :source => bug['source'],
                             :link => "http://bugs.debian.org/#{id}",
                             :description => "RC bug affecting testing only (ensure the package migrates)",
                             :details => "##{id}: #{bug['title']}" }
      elsif @bugs_tags[id].include?('rt_affects_unstable') or @bugs_tags[id].include?('rt_affects_testing')
        @dmd_todos << { :shortname => "rc_std_#{h}",
                        :type => 'RC bug',
                        :source => bug['source'],
                        :link => "http://bugs.debian.org/#{id}",
                        :description => "RC bug needs fixing",
                        :details => "##{id}: #{bug['title']}" }
      elsif @bugs_tags[id].include?('rt_affects_stable')
        stable_rc_bugs << { :shortname => "rc_stable_#{h}",
                            :type => 'RC bug (stable)',
                            :source => bug['source'],
                            :link => "http://bugs.debian.org/#{id}",
                            :description => "RC bug affecting stable",
                            :details => "##{id}: #{bug['title']}" }
      end
    end
    @dmd_todos.concat(testing_rc_bugs)
    @dmd_todos.concat(stable_rc_bugs)

    @buildd.each_pair do |src, archs|
      archs.each do |arch|
        h = Digest::MD5.hexdigest("#{src}_#{arch.sort.to_s}")
        @dmd_todos << { :shortname => "missingbuild_#{h}",
                        :type => 'missing build',
                        :source => src,
                        :link => "https://buildd.debian.org/status/package.php?p=#{src}",
                        :description => "Missing build on #{arch['architecture']}",
                        :details => " state <i>#{arch['state']}</i> since #{arch['state_change'].to_date.to_s}" }
      end
    end

    @migration.each_pair do |src, v|
      h = Digest::MD5.hexdigest("#{src}_#{v['unstable_version']}")
      sn = "migration_#{h}"
      if v['in_testing_age'].nil?
        if v['debian_age'] > MIN_AGE_IN_DEBIAN
        @dmd_todos << { :shortname => sn,
                        :type => 'testing migration',
                        :source => src,
                        :link => "http://qa.debian.org/excuses.php?package=#{src}",
                        :description => "Migration",
                        :details => "Has been in Debian for #{v['debian_age']} days, but never migrated to testing" }
        end
      elsif v['in_testing_age'] > 1 # in case there's some incoherency in udd
        @dmd_todos << { :shortname => sn,
                        :type => 'testing migration',
                        :source => src,
                        :link => "http://qa.debian.org/excuses.php?package=#{src}",
                        :description => "Migration",
                        :details => "Not in testing for #{v['in_testing_age']} days" }
      else
        if v['sync_age'].nil?
          #        puts "Interesting buggy case with #{pkg}. Ignore."
        elsif v['sync_age'] > MIN_SYNC_INTERVAL
        @dmd_todos << { :shortname => sn,
                        :type => 'testing migration',
                        :source => src,
                        :link => "http://qa.debian.org/excuses.php?package=#{src}",
                        :description => "Migration",
                        :details => "Has been trying to migrate for #{v['sync_age']} days" }
        end
      end
    end

    @ready_for_upload.each_pair do |src, v|
      h = Digest::MD5.hexdigest("#{src}_#{v['version']}_#{v['distribution']}")
      @dmd_todos << { :shortname => "vcs_#{h}",
                      :type => 'vcs',
                      :source => src,
                      :link => "http://pet.debian.net/#{v['team']}/pet.cgi",
                      :description => "New version",
                      :details => "#{v['version']} ready for upload" }
    end

    @versions.each_pair do |src, v|
      next if not v.has_key?('upstream')
      if v['upstream'][:status] == :out_of_date
        h = Digest::MD5.hexdigest("#{src}_#{v['upstream'][:version]}")
        @dmd_todos << { :shortname => "newupstream_#{h}",
                        :type => 'new upstream',
                        :source => src,
                        :link => nil,
                        :description => "New version available",
                        :details => "#{v['upstream'][:version]}" }
      elsif v['upstream'][:status] == :out_of_date_in_unstable
        h = Digest::MD5.hexdigest("#{src}_#{v['upstream'][:version]}")
        @dmd_todos << { :shortname => "newupstreamunstable_#{h}",
                        :type => 'new upstream',
                        :source => src,
                        :link => nil,
                        :description => "New upstream version available",
                        :details => "#{v['upstream'][:version]} (already in experimental, but not in unstable)" }
      end
    end

    @autoremovals.each_pair do |src, v|
      if v['bugs'] != nil
        bugs = v['bugs'].split(',').map { |b| "##{b}" }
        if bugs.count > 1
          bugs = " (bugs: #{bugs.join(', ')})"
        else
          bugs = " (bug: #{bugs[0]})"
        end
      else
        bugs = ""
      end

      @dmd_todos << {
        :shortname => "autoremoval_#{src}_#{v['version']}_#{v['removal_time']}",
        :type => 'testing auto-removal',
        :source => src,
        :link => nil,
        :description => "Testing auto-removal",
        :details => "on #{Time.at(v['removal_time']).to_date.to_s}#{bugs}"
      }
    end

    @dmd_todos
  end

  def complete_email(email)
    q = <<-EOF
SELECT DISTINCT value, label
FROM 
(SELECT maintainer_email AS value, maintainer AS label
from sources
where release in ('sid', 'experimental', 'jessie')
union
select email as value, uploader as label
from uploaders
where release in ('sid', 'experimental', 'jessie')
) emails
WHERE label ~* ?
    EOF
    r = dbget(q, ".*#{email}.*")
    return r.map { |r| r.to_h }
  end

  def UDDData.compare_versions(v1, v2)
    if not v1 or not v2
      return 0
    end
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
    sth = @dbh.prepare(q)
    sth.execute(*args)
    rows = sth.fetch_all
    if @debug
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
