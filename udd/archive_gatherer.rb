#!/usr/bin/ruby -w
# encoding: utf-8
#
# FIXME add detection of unknown fields

$:.unshift  '/srv/udd.debian.org/udd/udd'

require 'yaml'
require 'pp'
require 'pg'
require 'deb822'
require 'zlib'
require 'digest'

DODESC=false

DEBUG = false
TESTMODE = false
VCS = [ 'Svn', 'Git', 'Arch', 'Bzr', 'Cvs', 'Darcs', 'Hg', 'Mtn']
SOURCES_IGNORE = VCS.map { |e| "vcs-#{e.downcase}" } + [ 'directory', 'package-list', 'apport', 'debian-vcs-browser', 'debian-vcs-bzr', 'debian-vcs-git', 'debian-vcs-hg', 'debian-vcs-svn', 'orginal-maintainer', 'origianl-maintainer', 'origin', 'originalmaintainer', 'original-mainteiner', 'original-uploaders', 'original-vcs-browser', 'original-vcs-bzr', 'original-vcs-git', 'original-vcs-svn', 'orig-maintainer', 'orig-vcs-browser', 'orig-vcs-svn', 'python3-version', 'python-standards-version', 'upstream-depends', 'upstream-vcs-browser', 'upstream-vcs-bzr', 'url', 'vcs-browse', 'vcs-upstream-bzr', 'x-vcs-browser', 'x-vcs-bzr', 'x-vcs-darcs', 'x-vcs-svn', 'comment' ]
PACKAGES_IGNORE = [ 'apport', 'built-using', 'debian-vcs-browser', 'debian-vcs-svn', 'filename', 'gstreamer-decoders', 'gstreamer-elements', 'gstreamer-encoders', 'gstreamer-uri-sinks', 'gstreamer-uri-sources', 'gstreamer-version', 'lua-versions', 'modaliases', 'npp-applications', 'npp-description', 'npp-file', 'npp-filename', 'npp-mimetype', 'npp-name', 'orginal-maintainer', 'origianl-maintainer' 'originalmaintainer', 'original-mainteiner', 'original-uploaders', 'original-vcs-browser', 'original-vcs-git', 'original-vcs-svn', 'orig-maintainer', 'python3-version', 'python-runtime', 'ruby-version', 'screenshot-url', 'supported', 'thumbnail-url', 'ubuntu-webapps-domain', 'ubuntu-webapps-includes', 'ubuntu-webapps-name', 'url', 'vdr-patchlevel', 'x-original-maintainer', 'xul-appid' 'originalmaintainer', 'origianl-maintainer', 'tads3-version', 'tads2-version', 'xul-appid', 'originalmaintainer', 'ghc-package' ]

# PG doc: http://deveiate.org/code/pg/

class ArchiveGatherer
  def initialize
    config = YAML::load(IO::read(ARGV[0]))
    gconf = config['general']

    @db = PG.connect({ :dbname => gconf['dbname'], :port => (gconf['dbport'] || 5432)})
#    @db.trace(STDOUT)
#    @db.setnonblocking(true)
    @conf = config[ARGV[2]] 
    @tabprefix = @conf['tables-prefix'] || ''
    @all_packages = {}

    @db.prepare 'source_insert', <<-EOF
       INSERT INTO #{@tabprefix}sources
          (Source, Version, Maintainer, Maintainer_name, Maintainer_email, Format, Files, Uploaders, Bin,
          Architecture, Standards_Version, Homepage, Build_Depends,
          Build_Depends_Indep, Build_Conflicts, Build_Conflicts_Indep, Priority,
          Section, Vcs_Type, Vcs_Url, Vcs_Browser, python_version, ruby_versions, checksums_sha1,
          checksums_sha256, original_maintainer, testsuite, autobuild, dm_upload_allowed, extra_source_only,
          Distribution, Release, Component)
        VALUES
          ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
          $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, '#{@conf['distribution']}', $31, $32)
    EOF
    @source_fields =
      ['package', 'version', 'maintainer', 'maintainer_name', 'maintainer_email',
       'format', 'files', 'uploaders', 'binary', 'architecture', 'standards-version',
      'homepage', 'build-depends', 'build-depends-indep', 'build-conflicts',
      'build-conflicts-indep', 'priority', 'section', 'vcs-type', 'vcs-url', 'vcs-browser',
      'python-version', 'ruby-versions', 'checksums-sha1', 'checksums-sha256',
      'original-maintainer', 'testsuite', 'autobuild', 'dm-upload-allowed', 'extra-source-only', 'release', 'component' ]

    @db.prepare 'uploader_insert', <<-EOF
       INSERT INTO #{@tabprefix}uploaders
          (Source, Version, Distribution, Release, Component, Uploader, Name, Email)
        VALUES
          ($1, $2, '#{@conf['distribution']}', $3, $4, $5, $6, $7)
EOF
    @uploader_fields =
      ['package', 'version', 'release', 'component', 'uploader',
       'name', 'email']

	  @db.prepare 'package_insert', <<-EOF
      INSERT INTO #{@tabprefix}packages
	    (Package, Version, Architecture, Maintainer, maintainer_name, maintainer_email, Description,
       description_md5, Source, Source_Version, Essential, Depends, Recommends, Suggests, Enhances,
	     Pre_Depends, Breaks, Installed_Size, Homepage, Size, build_essential, origin, sha1, replaces,
       section, md5sum, bugs, priority, tag, task, python_version, ruby_versions, provides, conflicts,
       sha256, original_maintainer, multi_arch, Distribution, Release, Component)
	  VALUES
	    ( $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
	      $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28,
	      $29, $30, $31, $32, $33, $34, $35, $36, $37, '#{@conf['distribution']}', $38, $39)
    EOF
    @package_fields = 
      ['package', 'version', 'architecture', 'maintainer', 'maintainer_name', 'maintainer_email',
       'description', 'description-md5', 'source', 'source_version', 'essential',
       'depends', 'recommends', 'suggests', 'enhances',
       'pre-depends', 'breaks', 'installed-size', 'homepage', 'size',
       'build-essential', 'origin', 'sha1',
       'replaces', 'section', 'md5sum', 'bugs', 'priority',
       'tag', 'task', 'python-version', 'ruby-versions', 'provides',
       'conflicts', 'sha256', 'original-maintainer', 'multi-arch', 'release', 'component']

    @db.prepare 'description_insert', <<-EOF
      INSERT INTO #{@tabprefix}descriptions
        (package, distribution, release, component, language, description, long_description, description_md5)
        (SELECT $1 AS package, '#{@conf['distribution']}' AS distribution, $6 AS release, $7 AS component, $2 AS language,
         $3 AS description, $4 AS long_description, $5 AS description_md5
           WHERE NOT EXISTS
           (SELECT 1 FROM #{@tabprefix}descriptions WHERE package=$1 AND release=$6 AND component=$7 AND language=$2 AND
            description=$3 AND long_description=$4 AND description_md5=$5))
    EOF
    @description_fields = [ 'package', 'language', 'description', 'long_description',
                            'description-md5', 'release', 'component' ]

  @sources_unknown = {}
  @packages_unknown = {}
  end

  def report_unknown_sources(l)
    l2 = l - @source_fields - SOURCES_IGNORE
    l2.each do |f|
      @sources_unknown[f] ||= 0
      @sources_unknown[f] += 1
    end
  end

  def report_unknown_packages(l)
    l2 = l - @package_fields - PACKAGES_IGNORE
    l2.each do |f|
      @packages_unknown[f] ||= 0
      @packages_unknown[f] += 1
    end
  end

  def summarize_unknown
    if not @sources_unknown.empty?
      puts "Unknown fields in Sources:"
      pp @sources_unknown
    end
    if not @packages_unknown.empty?
      puts "Unknown fields in Packages:"
      pp @packages_unknown
    end
  end

  def process_sources(f, release, component)
    fd = Zlib::GzipReader::open(f)
    s = fd.read
    fd.close

    @db.exec("DELETE FROM #{@tabprefix}sources WHERE distribution=$1 AND release=$2 AND component=$3",
                    [ @conf['distribution'], release, component])
    @db.exec("DELETE FROM #{@tabprefix}uploaders WHERE distribution=$1 AND release=$2 AND component=$3",
                    [ @conf['distribution'], release, component])
    
    ds = Deb822::parse(s, {:downcase => true})
    ds.each do |d|
      report_unknown_sources(d.keys)

      # split maintainer
      if d['maintainer'] =~ /^(.*) <(.*)>$/
        d['maintainer_email'] = $2
        d['maintainer_name'] = $1.gsub('"', '')
      end
      # vcs
      VCS.each do |vcs|
        if d.has_key?("vcs-#{vcs.downcase}")
          d['vcs-type'] = vcs
          d['vcs-url'] = d["vcs-#{vcs.downcase}"]
          break
        end
        if d.has_key?("x-vcs-#{vcs.downcase}")
          d['vcs-type'] = vcs
          d['vcs-url'] = d["x-vcs-#{vcs.downcase}"]
          break
        end
      end
      d['vcs-browser'] = d['x-vcs-browser'] if d['x-vcs-browser']

      d['release'] = release
      d['component'] = component
      d['dm-upload-allowed'] = ( (d['dm-upload-allowed'] || '').downcase == 'yes' ) ? true : nil
      d['extra-source-only'] = ( (d['extra-source-only'] || '').downcase == 'yes' ) ? true : nil
     
      # uploaders
      if d['uploaders']
      #  p d['uploaders']
        u = {}
        u['package'] = d['package']
        u['version'] = d['version']
        u['component'] = d['component']
        u['release'] = d['release']
        if d['uploaders'] =~ />,/
          d['uploaders'].split(/>,\s*/).each do |upl|
            upl =~ /^\s*(.*) <([^>]*)(>)?$/ or raise
            u['email'] = $2
            u['name'] = $1.gsub('"', '')
            u['uploader'] = upl
            u['uploader'] += '>' if not upl =~ />$/
            @db.exec_prepared('uploader_insert', @uploader_fields.map { |e| u[e] })
          end
        else
          if d['uploaders'] =~ /^(.*) <(.*)>$/
            u['uploader'] = d['uploaders']
            u['email'] = $2
            u['name'] = $1.gsub('"', '')
          else
            u['uploader'] = d['uploaders']
          end
          @db.exec_prepared('uploader_insert', @uploader_fields.map { |e| u[e] })
        end
      end
      @db.exec_prepared('source_insert', @source_fields.map { |e| d[e] })
    end
  end

  def process_packages(f, release, component, architecture)
    fd = Zlib::GzipReader::open(f)
    s = fd.read
    fd.close

    ds = Deb822::parse(s, {:downcase => true})
    ds.each do |d|
      report_unknown_packages(d.keys)

      # check if package has already been imported
      if d['architecture'] == 'all'
        n = [d['package'], d['version'], release, component]
        next if @all_packages.has_key?(n)
        @all_packages[n] = true
      end

      # split maintainer
      if d['maintainer'] =~ /^(.*) <(.*)>$/
        d['maintainer_email'] = $2
        d['maintainer_name'] = $1.gsub('"', '')
      end

      # Source is non-mandatory, but we don't want it to be NULL
      if d['source'].nil?
        d['source'] = d['package']
        d['source_version'] = d['version']
      else
        if d['source'] =~ /(.*) \((.*)\)/
          d['source'] = $1
          d['source_version'] = $2
        else
          d['source_version'] = d['version']
        end
      end
   
      d['release'] = release
      d['component'] = component

      # descriptions
      if d['description']
        if not d['description-md5']
          d['description-md5'] = Digest::MD5.hexdigest(d['description']+"\n")
        end
        d['language'] = 'en'
        sp = d['description'].split(/\n/, 2)
        if sp.length > 1
          d['long_description'] = sp[1]
          d['description'] = sp[0]
        else
          d['long_description'] = ''
        end
        if DODESC
          @db.exec_prepared('description_insert', @description_fields.map { |e| d[e] })
        end
      end
     
      @db.exec_prepared('package_insert', @package_fields.map { |e| d[e] })
    end
  end

  def run
    @db.exec("BEGIN")
    @db.exec("SET CONSTRAINTS ALL DEFERRED")

    if @conf['path'].kind_of? String
      run_path(@conf['path'])
    else
      @conf['path'].each do |path|
        run_path(path)
      end
    end

    @db.exec("DELETE FROM #{@tabprefix}packages_summary")
    @db.exec("INSERT INTO #{@tabprefix}packages_summary (package, version, source, source_version,
        maintainer, maintainer_name, maintainer_email, distribution, release, component)
      SELECT DISTINCT ON (package, version, distribution, release, component)
        package, version, source, source_version, maintainer, maintainer_name, maintainer_email,
        distribution, release, component FROM #{@tabprefix}packages")
    @db.exec("DELETE FROM #{@tabprefix}packages_distrelcomparch")
    @db.exec("INSERT INTO #{@tabprefix}packages_distrelcomparch
      (distribution, release, component, architecture)
      SELECT DISTINCT distribution, release, component, architecture
      FROM #{@tabprefix}packages_distrelcomparch")

    @db.exec("COMMIT")
    @db.exec("ANALYZE #{@tabprefix}sources")
    @db.exec("ANALYZE #{@tabprefix}uploaders")
    @db.exec("ANALYZE #{@tabprefix}packages")
    if DODESC
      @db.exec("ANALYZE #{@tabprefix}descriptions")
    end
    @db.exec("ANALYZE #{@tabprefix}packages_summary")
    @db.exec("ANALYZE #{@tabprefix}packages_distrelcomparch")

    summarize_unknown
  end

  def run_path(path)
    sources = Dir::glob("#{path}/dists/**/source/Sources.gz")
    sources.each do |source|
      next if TESTMODE
      source =~ /#{path}\/dists\/(.*)\/(.*)\/source\/Sources.gz/
      component = $2
      release = $1
      # this is a hack. there's squeeze-updates on ftp.debian.org, and squeeze/updates
      # on security.debian.org. so we rename the latter to squeeze-security.
      if path =~ /debian-security/ and release =~ /(.*)\/updates/
        release = $1 + '-security'
      else
        release = release.gsub('/', '-')
      end

      puts "Processing #{source} rel=#{release} comp=#{component}" if DEBUG
      process_sources(source, release, component)
    end

    todo = []
    todelete = []
    packages = Dir::glob("#{path}/dists/**/binary-*/Packages.gz")
    packages.each do |package|
      next if TESTMODE and not package =~ /rdy-updates\/main\/binary-i386/
      # those releases used a slightly different Packages format
      next if package =~ /\/srv\/mirrors\/debian-archive\/debian\/\/dists\/(bo|buzz|rex)\//
      if package =~ /debian-installer/
        package =~ /#{path}\/dists\/(.*)\/(.*)\/debian-installer\/binary-(.*)\/Packages.gz/
        architecture = $3
        component = $2 + "/debian-installer"
        release = $1
      else
        package =~ /#{path}\/dists\/(.*)\/(.*)\/binary-(.*)\/Packages.gz/
        architecture = $3
        component = $2
        release = $1
      end
      # this is a hack. there's squeeze-updates on ftp.debian.org, and squeeze/updates
      # on security.debian.org. so we rename the latter to squeeze-security.
      if path =~ /debian-security/ and release =~ /(.*)\/updates/
        release = $1 + '-security'
      else
        release = release.gsub('/', '-')
      end

      todo << { :package => package, :rel => release, :comp => component, :arch => architecture }
      todelete << {:rel => release, :comp => component}
    end
    todelete.uniq.each do |td|
      @db.exec("DELETE FROM #{@tabprefix}packages WHERE distribution=$1 AND release=$2 AND component=$3",
                    [ @conf['distribution'], td[:rel], td[:comp]])
      if DODESC
        @db.exec("DELETE FROM #{@tabprefix}descriptions WHERE distribution=$1 AND release=$2 AND component=$3 AND language='en'",
                 [ @conf['distribution'], td[:rel], td[:comp]])
      end
    end

    todo.each do |td|
      puts "Processing #{td[:package]} rel=#{td[:rel]} comp=#{td[:comp]} arch=#{td[:arch]}" if DEBUG
      process_packages(td[:package], td[:rel], td[:comp], td[:arch])
    end
  end
end


if(ARGV.length != 3)
  puts "Usage: #{$0} <config> <command> <source>"
  exit(1)
end
ArchiveGatherer::new.run
