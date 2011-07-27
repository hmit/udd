#!/usr/bin/env python

"""
This script imports information from ftp new queue into the database
See http://ftp-master.debian.org/new.822 and
    http://ftp-master.debian.org/new.html
"""

try:
    from debian import deb822
except:
    from debian_bundle import deb822
from os import access, mkdir, unlink, W_OK
from sys import stderr
import aux
from aux import quote
from gatherer import gatherer
import email.Utils
import re
from time import ctime
from psycopg2 import IntegrityError, ProgrammingError

def get_gatherer(connection, config, source):
  return ftpnew_gatherer(connection, config, source)

DEBUG=0
def to_unicode(value, encoding='utf-8'):
    if isinstance(value, str):
	return value.decode(encoding)
    else:
        return unicode(value)

# When parsing src html pages we have to get rid of certain html strings
def de_html(string):
  string= re.sub("</?span[^>]*>", '',  string)
  string= re.sub("&quot;",        '"', string)
  string= re.sub("&amp;",         '&', string)
  string= re.sub("&lt;",          '<', string)
  string= re.sub("&gt;",          '>', string)
  string= re.sub("</?pre>",       '',  string)
  return string

# These fields are not forewarded to UDD tables for the moment
fields_to_pass   = ('Format',
                    'Date',
                    'Changed-By',
                    'Files',
                    'Uploaders',
                    'Standards-Version',
                    'Priority',
                    'Urgency',
                    'Dm-Upload-Allowed',
                    'Autobuild',
                    'Build-Depends',
                    'Build-Depends-Indep',
                    'Build-Conflicts',
                    'Python-Version')
                    # + startswith('Npp-')

# These fields are not documented (to my knowledge) but just occure from
# time to time in control files
# Just suppress warnings about these
if DEBUG == 0:
    IGNORED_UNKNOWN_FIELDS = ('Original-Maintainer',
	                      'Multi-Arch',
	                      'Python3-Version',
        	              'Gstreamer-Elements',
            	              'Gstreamer-Version',
            	              'Built-Using',
            	              'Package-Type',
            	              'Ruby-Versions'
                	     )
else:
    IGNORED_UNKNOWN_FIELDS = ()

dependencies_to_accept = ( 'Depends', 'Recommends', 'Suggests', 'Enhances', 'Pre-Depends',
                           'Breaks',  'Replaces', 'Provides', 'Conflicts')

class src_pkg():
  def __init__(self, source):
    self.s = {}
    self.s['Source']       = source
    self.has_several_versions = 0
    # self.bin              = () # comma separated list of binaries created from the source
    self.s['Bin']          = () # comma separated list of binaries created from the source
    self.s['Architecture'] = () # architecture(s separated by blanks)
    # Just define Vcs fields in case it is not provided in the control
    self.s['Vcs-Type']     = None
    self.s['Vcs-Url']      = None
    # preset WNPP bug
    self.s['Closes']       = 0

  def check_dict(self):
    "Make sure that non-mandatory fields at least get a '' value"
    for field in ftpnew_gatherer.s_non_mandatory:
      if not self.s.has_key(field):
        self.s[field] = ''

  def __str__(self):
    str  = "Source %(Source)s: %(Version)s, (%(Architecture)s), %(Last_modified)s, %(Queue)s, %(Distribution)s" % \
        (self.s)
    if self.s.has_key('maintainer_name') and self.s.has_key('maintainer_email') and \
          self.s.has_key('Closes'):
       str += "   %(maintainer_name)s <%(maintainer_email)s>, %(Closes)i" % (self.s)
    return str

class bin_pkg():
  def __init__(self, package, source):
    self.b = {}
    self.b['Package']        = package
    self.b['Source']         = source
    self.b['Installed-Size'] = 0
    self.b['License']        = ''

  def check_dict(self):
    "Make sure that non-mandatory fields at least get a '' value"
    for field in ftpnew_gatherer.b_non_mandatory:
      if not self.b.has_key(field):
        self.b[field] = ''

  def __str__(self):
    return "Package %s: %s, %s, %s, %s, %s" % \
        (self.b['Package'], self.b['Version'], self.b['Architecture'], self.b['Maintainer'],
         self.b['Description'], self.b['Long_Description'])

class ftpnew_gatherer(gatherer):
  "This class imports the data from New queue into the database"
  s_mandatory = {'Source': 0, 'Format': 0, 'Maintainer': 0, 'Package': 0, 'Version': 0, 'Files': 0,
                 'Queue': 0, 'Last_modified': 0}
  s_non_mandatory = {'Uploaders': 0, 'Bin': 0, 'Architecture': 0,
                     'Homepage': 0, 'Build-Depends': 0, 'Vcs-Arch': 0, 'Vcs-Bzr': 0,
                     'Vcs-Cvs': 0, 'Vcs-Darcs': 0, 'Vcs-Git': 0, 'Vcs-Hg': 0, 'Vcs-Svn': 0,
                     'Vcs-Mtn':0, 'Vcs-Browser': 0, 'License': 0, 'Section': 0
                    }
  s_ignorable = {'X-Vcs-Browser': 0, 'X-Vcs-Bzr': 0, 'X-Vcs-Darcs': 0, 'X-Vcs-Svn': 0, 'X-Vcs-Hg':0, 'X-Vcs-Git':0,
                 'Directory':0, 'Comment':0, 'Origin':0, 'Url':0, 'X-Collab-Maint':0, 'Autobuild':0, 'Vcs-Cvs:':0,
                 'Python-Standards-Version':0, 'url':0, 'originalmaintainer':0, 'Originalmaintainer':0,
                 'Build-Recommends':0,
                 'Build-Depends-Indep': 0, 'Build-Conflicts': 0, 'Build-Conflicts-Indep': 0,
                 'Priority': 0, 'Python-Version': 0, 'Checksums-Sha1':0,
                 'Checksums-Sha256':0, 'Original-Maintainer':0, 'Dm-Upload-Allowed':0,
                 'Standards-Version': 0, 
                }

  b_non_mandatory = {'Source': 0, 'Essential': 0, 'Depends': 0, 'Recommends': 0,
                     'Suggests': 0, 'Enhances': 0, 'Pre-Depends': 0, 'Breaks':0, 'Installed-Size': 0,
                     'Homepage': 0, 'Size': 0, 'Build-Essential':0, 'Origin':0,
                     'SHA1':0, 'Replaces':0, 'Section':0, 'MD5sum':0, 'Bugs':0, 'Priority':0,
                     'Tag':0, 'Task':0, 'Python-Version':0, 'Provides':0, 'Conflicts':0,
                     'SHA256':0, 'Original-Maintainer':0}

  s_ignorable_re = re.compile("^(Original-|Origianl-|Orginal-|Debian-|X-Original-|Upstream-)")
  s_vcs = { 'Arch':0, 'Bzr':0, 'Cvs':0, 'Darcs':0, 'Git':0, 'Hg':0, 'Svn':0, 'Mtn':0}

  src_html_failed_re  = re.compile("^<p>The requested URL /new/.+\.html was not found on this server\.</p>")
  src_html_has_tag_re = re.compile('^\s*<tr><td class="key">([-\w]+):</td><td class="val">(.+)</td></tr>$')
  src_html_has_description_start_re = re.compile('^\s*<tr><td class="key">Description:</td><td class="val"><pre>(.+)')
  src_html_has_description_end_re   = re.compile('(.+)</pre></td></tr>')
  closes_is_itp_re    = re.compile('^[\s"]*(ITP|RFP|ITA)')
  vcs_type_re         = re.compile('Vcs-(Svn|Git|Bzr|Darcs|Hg|Cvs|Arch|Mtn)')

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('path', 'table_sources', 'table_packages', 'ftpmasterURL', 'releases_ignore')


  def check_existing_binaries(self, values, source, queue):
    # Sometimes the source package name has changed, but the binary package name is known in UDD
    # we are not interested in these packages

    cur = self.cursor()
    for value in values:
      # query = "SELECT count(*) FROM packages WHERE package = '%s'" % (value)
      query = "EXECUTE ftpnew_check_existing_package ('%s', '%s')" % (value, source)
      cur.execute(query)
      in_udd = cur.fetchone()[0]
      if in_udd:
        if DEBUG != 0:
    	  print >>stderr, "Binary package %s is shipped in source %s %i times in UDD - no interest in just known binaries (queue = %s)" \
      	             % (value, source, int(in_udd), queue)
    	return 1
    return 0

  def run(self):
    my_config = self.my_config

    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    # if we check whether a package just exists in UDD we ignore oldstable which is currently etch but other
    # dists might have to be ignored as well
    cur.execute("PREPARE ftpnew_check_existing_package AS SELECT COUNT(*) FROM packages WHERE package = $1 AND source = $2 AND release NOT IN (%s)" \
                  % self.my_config["releases_ignore"])
    # For some reason the code tries to add binary packages twice - just verify whether the package is
    # just included to make sure we do not trigger conflicting primary keys
    cur.execute("PREPARE ftpnew_check_just_added_package AS SELECT COUNT(*) FROM new_packages WHERE package = $1 AND version = $2 AND architecture = $3")

    cur.execute("DELETE FROM %s" % my_config["table_sources"])
    cur.execute("DELETE FROM %s" % my_config["table_packages"])

    query = """PREPARE ftpnew_insert_source
      AS INSERT INTO %s (source, version, maintainer, maintainer_name, maintainer_email, binaries, 
                         changed_by, architecture, homepage,
                         vcs_type, vcs_url, vcs_browser,
                         section, distribution, component, closes, license, last_modified, queue)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)""" % (my_config['table_sources'])
    cur.execute(query)
    query = """PREPARE ftpnew_insert_package
      AS INSERT INTO %s (package, version, architecture, maintainer, description, source,
         depends, recommends, suggests, enhances, pre_depends, breaks, replaces, provides, conflicts,
                         installed_size, homepage, section, long_description, distribution, component, license)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)""" \
            % (my_config['table_packages'])
    cur.execute(query)

    ftpnew822file    = my_config['path']+'/new.822'
    ftpnew_data      = open(ftpnew822file)

    # seems there will be no change to set the section field ... getting bored about daily mail about this
    # has_warned_about_missing_section_key = 0
    has_warned_about_missing_section_key = 1
    try:
      for stanza in deb822.Sources.iter_paragraphs(ftpnew_data, shared_storage=False):
        try:
          if stanza['queue'] == 'accepted' or stanza['queue'] == 'proposedupdates' :
            continue
        except KeyError, err:
          print >>stderr, "No key queue found (%s), %s" % (err, str(stanza))
          continue
        srcpkg               = src_pkg(stanza['source'])
        versions             = stanza['version'].split(' ')        # the page lists more than one version
        srcpkg.has_several_versions = len(versions)-1              # some tests below fail if more than one version in in queue
        srcpkg.s['Version']       = versions[srcpkg.has_several_versions]
        srcpkg.s['Architecture']  = stanza['architectures']
        srcpkg.s['Queue']         = stanza['queue']
        srcpkg.s['Last_modified'] = ctime(int(stanza['last-modified'])) # We want a real time object instead of an epoch
        srcpkg.s['Distribution']  = stanza['distribution']
        srcpkg.s['Changed-By']    = to_unicode(stanza['changed-by'])
        # remove comma between binaries which are inserted in *.dsc information
        srcpkg.s['Bin']           = re.sub(", +", " ", stanza['binary'])
        try:
          srcpkg.s['Section']       = stanza['section']
          if stanza['section'].startswith('non-free'):
            srcpkg.s['Component'] = 'non-free'
          elif stanza['section'].startswith('contrib'):
            srcpkg.s['Component'] = 'contrib'
          else:
            srcpkg.s['Component'] = 'main'
        except KeyError:
          srcpkg.s['Section']     = ''
          srcpkg.s['Component']   = ''
          if has_warned_about_missing_section_key == 0:
            has_warned_about_missing_section_key = 1
            print >>stderr, "Warning: Because of a bug in DAK code the Section field is currently missing."

        # Check UDD for existing source packages of this name
        query = "SELECT count(*) FROM sources WHERE source = '%s'" % (srcpkg.s['Source'])
        cur.execute(query)
        in_udd = cur.fetchone()[0]
        if in_udd:
          if DEBUG != 0:
            print >>stderr, "%s is %i times in UDD - no interest in just known sources (queue = %s)" \
                            % (srcpkg.s['Source'], int(in_udd), srcpkg.s['Queue'])
          continue

        src_info_base = srcpkg.s['Source'] + '_' + srcpkg.s['Version']
        src_info_html = my_config['path'] + '/' + src_info_base + '.html'
        src_info_822  = my_config['path'] + '/' + src_info_base + '.822'

        try:
          srci = open(src_info_html, 'r')
        except IOError, err:
          print >>stderr, "No html info for package %s in queue %s (%s)." % (srcpkg.s['Source'], stanza['queue'], err) 
          continue
        srco = open(src_info_822, 'w')
        in_description     = 0
        in_source          = 1
        binpkgs = []
        binpkg = None
        binpkg_changes = None # In case we have only information about changes file which sometimes might happen
        for line in srci.readlines():
          if ftpnew_gatherer.src_html_failed_re.match(line):
            print >>stderr, "File %s not found." % (src_info_html)
            src_info_not_found = 1
            break
          match = ftpnew_gatherer.src_html_has_tag_re.match(line)
          if match:
            field = match.groups()[0]
            value = de_html(match.groups()[1])
            if field == 'Package':
              # Here begins a new binary package
              if self.check_existing_binaries((value,), srcpkg.s['Source'], srcpkg.s['Queue']):
                srcpkg.s['Queue'] = 'ignore'
                break
              if in_source:
                in_source = 0
                # we need to initialise some fields in the binary package
                binpkg_changes = bin_pkg(value.split(' ')[0], srcpkg.s['Source'])
                for key in ['Architecture', 'Component', 'Distribution', 'Version', 'Maintainer']:
                  binpkg_changes.b[key]     = srcpkg.s[key]
                binpkg_changes.b['Description']      = 'binary package information is missing in new queue'
                binpkg_changes.b['Long_Description'] = '' # no long description available in *.changes file
              if binpkg:
                binpkgs.append(binpkg)
              binpkg = bin_pkg(value, srcpkg.s['Source'])
              print >>srco, "\nPackage: %s" % (value)
              binpkg.b['Distribution'] = srcpkg.s['Distribution']
            elif field == 'Maintainer':
              if in_source:
                srcpkg.s[field]   = to_unicode(value)
                srcpkg.s['maintainer_name'], srcpkg.s['maintainer_email'] = email.Utils.parseaddr(srcpkg.s[field])
              else:
                binpkg.b[field]   = value
              print >>srco, "%s: %s" % (field, value)
            elif field == 'Description':
              # This does not seem to be executed because description is parsed when src_html_has_description_start_re matches (see below)
              if in_source:
                srcpkg.s[field]  = de_html(value)
              else:
                binpkg.b[field]  = de_html(value)
              print >>srco, "%s: %s" % (field, value)
            elif field == 'Architecture':
              if in_source:
                srcpkg.s[field] = value
              else:
                binpkg.b[field] = value
              print >>srco, "%s: %s" % (field, value)
            elif field == 'Source':
              if in_source:
                if value != srcpkg.s['Source']:
                  print >>stderr, "Incompatible source names between new.822(%s) and %s.html (%s)" % \
                      (srcpkg.s['Source'], src_info_base, value)
                  srcpkg.s['Source']    = value
                print >>srco, "%s: %s" % (field, value)
            elif field == 'Version':
              if in_source:
                if srcpkg.has_several_versions == 0 and value != srcpkg.s[field]:
                  print >>stderr, "Incompatible version numbers between new.822(%s) and %s.html (%s)" % \
                      (srcpkg.s[field], src_info_base, value)
                srcpkg.s[field]         = value
              else:
                binpkg.b[field]   = value
              print >>srco, "%s: %s" % (field, value)
            elif field == 'Closes':
              values = value.split(' ')
              found_itp = 0
              for val in values:
                ival = int(val)
                query = "SELECT title from bugs where id = %i and package = 'wnpp' and source = 'wnpp'" % (ival)
                cur.execute(query)
                wnpp_title = ''
                try:
                  wnpp_title = cur.fetchone()[0]
                except TypeError, err:
                  query = "SELECT id, package, source, title FROM bugs WHERE id = %i" % (ival)
                  cur.execute(query)
                  bug_info = cur.fetchone()
                  if DEBUG != 0:
                    if not bug_info:
                      print >>stderr, "Bug %i which source package %s claims to close does not exist." % (ival, srcpkg.s['Source'])
                    else:
                      print >>stderr, "Bug #%i of package %s and source %s is not against pseudopackage 'wnpp' and hast title '%s'" % bug_info
                if not ftpnew_gatherer.closes_is_itp_re.match(wnpp_title):
                  # print >>stderr, "Bug %i closed by source package %s seems to be not ITPed" % (ival, srcpkg.s['Source'])
                  pass # avoid useless warnings
                else:
                  if found_itp:
                    if DEBUG != 0:
                      print >>stderr, "Warning: Package %s seems to have more than one ITP bugs (%i, %i). Only %i is stored in UDD (title = %s)" % \
                          (srcpkg.s['Source'], srcpkg.s['Closes'], ival, srcpkg.s['Closes'], wnpp_title)
                      query = "SELECT count(*) FROM bugs_merged_with WHERE id = %i OR id = %i" % (srcpkg.s['Closes'], ival)
                      cur.execute(query)
                      is_merged = cur.fetchone()[0]
                      if is_merged != 2:
                        print >>stderr, "  --> Please verify whether bugs should could be merged in BTS!"
                  else: # stay with the ITP found first 
                    srcpkg.s[field] = int(ival)
                  found_itp = 1
              if not found_itp and DEBUG != 0:
                print >>stderr, "Most probably %s is not new." % (srcpkg.s['Source'])
              print >>srco, "%s: %s\n" % (field, value)
            elif field == 'Distribution':
              if in_source:
                if srcpkg.has_several_versions == 0 and value.strip() != srcpkg.s['Distribution']:
                  print >>stderr, "Incompatible distributions between new.822(%s) and %s.html (%s)" % \
                      (srcpkg.s['Distribution'], src_info_base, value)
                srcpkg.s[field] = value
                print >>srco, "%s: %s" % (field, value)
              else:
                print >>stderr, "Binary should not mention distribution field in %s.html (%s)" % \
                    (src_info_base, value)
            elif field == 'Binary':
              if in_source:
                # Remove ',' in *.dsc information (not needed in *.changes)
                value = re.sub(", +", " ", value)   # !!!!
              if self.check_existing_binaries(value.split(' '), srcpkg.s['Source'], srcpkg.s['Queue']):
                srcpkg.s['Queue'] = 'ignore'
                break
              if in_source:
                # if srcpkg.s['Bin'] != () and value != srcpkg.s['Bin']:
                # Sometimes the order of multi binary packages is different - it is sufficient
                # to assume that the package names are the same if the strings are equally long
                if srcpkg.s['Bin'] != () and len(value) != len(srcpkg.s['Bin']):
                  print >>stderr, "Incompatible binaries between new.822(%s) and %s.html (%s)" % \
                      (srcpkg.s['Bin'], src_info_base, value)
                srcpkg.s['Bin'] = value
                print >>srco, "%s: %s" % (field, value)
              else:
                print >>stderr, "Binary should not mention Binary field in %s.html (%s)" % \
                    (src_info_base, value)
            elif field == 'Installed-Size':
              if not in_source:
                binpkg.b[field] = int(value)
            elif field == 'Homepage':
              if not in_source:
                binpkg.b[field] = value
            elif field == 'Section':
              if not in_source:
                if not binpkg:
                  print >>stderr, "This should not happen", srcpkg, field, value
                  exit(-1)
                else:
                  binpkg.b[field] = value
                  binpkg.b['Component'] = srcpkg.s['Component']
            elif field == 'Vcs-Browser':
              srcpkg.s[field] = value
            elif binpkg != None and field in dependencies_to_accept:
              binpkg.b[field] = value
              print >>srco, "%s: %s" % (field, value)
            elif field in fields_to_pass or field.startswith('Npp-'):
              print >>srco, "%s: %s" % (field, value)
            else:
              matchvcs = ftpnew_gatherer.vcs_type_re.match(field)
              if matchvcs:            
                srcpkg.s['Vcs-Type'] = matchvcs.groups()[0]
                srcpkg.s['Vcs-Url']  = value
                print >>srco, "%s: %s" % (field, value)
              else:
                # Don't warn about Original-Maintainer field
                if not field in IGNORED_UNKNOWN_FIELDS:
                  print >>stderr, "Unknown field in %s: %s" % (srcpkg.s['Source'], field)
                print >>srco, "*%s: %s" % (field, value)
            continue
          if in_description:
            match = ftpnew_gatherer.src_html_has_description_end_re.match(line)
            if match:
              if match.groups()[0][0] != ' ':
                description += ' '
              description += de_html(match.groups()[0])
              in_description = 0
              if not in_source: # binpkg and binpkg.b:
                (binpkg.b['Description'], binpkg.b['Long_Description']) = description.split("\n",1)
                print >>srco, "Description: %s\n%s" % (binpkg.b['Description'], binpkg.b['Long_Description'])
            else:
              if line[0] != ' ':
                description += ' '
              description += de_html(line)
          else:
            match = ftpnew_gatherer.src_html_has_description_start_re.match(line)
            if match:
              in_description = 1
              description = de_html(match.groups()[0]) + "\n"
        srci.close()
        srco.close()
        # Append last read binary package to list of binary packages
        if binpkg != None:
          binpkgs.append(binpkg)
        else: # ... if only .changes information available (for whatever reason other information might be missing in new queue
          if srcpkg.s['Queue'] != 'ignore':
            # fall back to some basic information
            binpkgs.append(binpkg_changes)
            if binpkg_changes:
              print >>stderr, "Package %s is missing information for binary packages" % (binpkg_changes.b['Package'])
        if srcpkg.s['Queue'] != 'ignore':
          # print srcpkg
          srcpkg.check_dict()
          query = """EXECUTE ftpnew_insert_source (%(Source)s, %(Version)s,
                    %(Maintainer)s, %(maintainer_name)s, %(maintainer_email)s,
                    %(Bin)s, %(Changed-By)s, %(Architecture)s, %(Homepage)s,
                    %(Vcs-Type)s, %(Vcs-Url)s, %(Vcs-Browser)s,
                    %(Section)s, %(Distribution)s, %(Component)s, %(Closes)s, %(License)s,
                    %(Last_modified)s, %(Queue)s)"""
          try:
            cur.execute(query, srcpkg.s)
          except ProgrammingError, err:
            print "ProgrammingError", err, "\n", query, "\n", srcpkg.s
          except UnicodeEncodeError, err:
            print "UnicodeEncodeError probably in 'Maintainer' or 'Changed-By' field, but should be prevented by to_unicode()\n", err, "\n", srcpkg.s
          for binpkg in binpkgs:
            # print binpkg
            if not binpkg:
              print >>stderr, "Undefined binpkg.  This is the info from changes:", str(binpkg_changes)
              continue
            binpkg.check_dict()
            query = """EXECUTE ftpnew_insert_package (%(Package)s, %(Version)s,
                       %(Architecture)s, %(Maintainer)s, %(Description)s, %(Source)s,
                       %(Depends)s, %(Recommends)s, %(Suggests)s, %(Enhances)s,
                       %(Pre-Depends)s, %(Breaks)s, %(Replaces)s, %(Provides)s, %(Conflicts)s,
                       %(Installed-Size)s, %(Homepage)s, %(Section)s,
                       %(Long_Description)s, %(Distribution)s, %(Component)s, %(License)s)"""
            try:
              cur.execute(query, binpkg.b)
            except IntegrityError, err:
              print >>stderr, err, src_info_html
              print >>stderr, binpkg
              print >>stderr, binpkg.b
              continue
            except KeyError, err:
              print >>stderr, "Missing information field for binary package %s: %s" % (binpkg.b['Package'], err)
              continue
    except KeyError, err:
      print >>stderr, "Unable to finish parsing %s because of unknown key %s" % (ftpnew822file, err)

    cur.execute("DEALLOCATE ftpnew_insert_source")
    cur.execute("DEALLOCATE ftpnew_insert_package")
    cur.execute("DEALLOCATE ftpnew_check_existing_package")
    cur.execute("VACUUM ANALYZE %s" % my_config["table_sources"])
    cur.execute("VACUUM ANALYZE %s" % my_config["table_packages"])

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
