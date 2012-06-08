#!/usr/bin/env python

"""
This script imports data about not yet uploaded packages prepared by Blends teams.
"""

from aux import parse_email
from gatherer import gatherer
from sys import stderr, exit
from os import listdir
from os.path import exists
from fnmatch import fnmatch
from psycopg2 import IntegrityError, InternalError, ProgrammingError
import re
import logging
import logging.handlers
from subprocess import Popen, PIPE
from debian import deb822
import email.Utils

from bibref_gatherer import upstream_reader

debug=0

def get_gatherer(connection, config, source):
  return blends_prospective_gatherer(connection, config, source)

def RowDictionaries(cursor):
    """Return a list of dictionaries which specify the values by their column names"""

    description = cursor.description
    if not description:
        # even if there are no data sets to return the description should contain the table structure.  If not something went
        # wrong and we return NULL as to represent a problem
        return NULL
    if cursor.rowcount <= 0:
        # if there are no rows in the cursor we return an empty list
        return []

    data = cursor.fetchall()
    result = []
                                                                                          
    for row in data:
        resultrow = {}
        i = 0
        for dd in description:
            resultrow[dd[0]] = row[i]
            i += 1
        result.append(resultrow)
    return result


class blends_prospective_gatherer(gatherer):
  """
  Not yet uploaded packages prepared by Blends teams in Vcs
  """

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config('table')

    self.log = logging.getLogger(self.__class__.__name__)
    if debug==1:
        self.log.setLevel(logging.DEBUG)
    else:
        self.log.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(filename=self.__class__.__name__+'.log',mode='w')
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - (%(lineno)d): %(message)s")
    handler.setFormatter(formatter)
    self.log.addHandler(handler)

    self.prospective = []

  def run(self):
    my_config = self.my_config
    cur = self.cursor()

    # find_itp_re = re.compile('\s+\*\s+.*(initial|ITP).+closes:\s+(Bug|)#(\d+)', flags=re.IGNORECASE|re.MULTILINE)
    # just check for the term "initial|ITP"
    find_itp_re = re.compile('(initial|ITP)', flags=re.IGNORECASE|re.MULTILINE)
    # might need enhancement (see http://www.debian.org/doc/manuals/developers-reference/pkgs.html#upload-bugfix)
    # --> /closes:\s*(?:bug)?\#\s*\d+(?:,\s*(?:bug)?\#\s*\d+)*/ig
    parse_itp_re = re.compile('^([A-Z]+): ([^\s]+) -- (.+)$')
    vcs_type_re = re.compile('Vcs-(Svn|Git|Bzr|Darcs|Hg|Cvs|Arch|Mtn)')
    
    cur.execute('TRUNCATE %s' % my_config['table'])
    cur.execute("PREPARE check_source (text) AS SELECT COUNT(*) FROM sources WHERE source = $1")
    cur.execute("PREPARE check_reference (text) AS SELECT COUNT(*) FROM bibref WHERE source = $1")

    cur.execute("""PREPARE check_itp (int) AS
                  SELECT id, arrival, submitter, owner, title, last_modified, submitter_name, submitter_email, owner_name, owner_email
                    FROM bugs
                    WHERE id = $1 AND package = 'wnpp' and source = 'wnpp' """)

    u_dirs = listdir(my_config['path'])

    pkgs = []
    bibrefs = []

    for u in u_dirs:
      upath=my_config['path']+'/'+u
      sources = []
      for file in listdir(upath):
        if fnmatch(file, '*.changelog'):
          sources.append(re.sub("\.changelog", "", file))
      for source in sources:
        cur.execute("EXECUTE check_source (%s)", (source,))
        if cur.fetchone()[0] > 0:
    	  # print "Source %s is in DB.  Ignore for prospective packages" % source
    	  ufile=upath+'/'+source+'.upstream'
    	  if not exists(ufile):
            continue
          cur.execute("EXECUTE check_reference (%s)", (source,))
          if cur.fetchone()[0] > 0:
            # UDD seems to contain the references specified in source.upstream file
            continue
          upstream = upstream_reader(ufile, source, self.log)
          if not upstream.references:
            # There are no valid references found in this upstream file or it is no valid YAML
            continue
          self.log.warning("%s has upstream file but no references in UDD" % (source, ))
          upstream.parse()
          for ref in upstream.get_bibrefs():
            bibrefs.append(ref)
          continue

        sprosp = {}
    	# Read Vcs fields
        vcsfile = upath+'/'+source+'.vcs'
    	try:
    	  vcs = open(vcsfile,'r')
    	except:
    	  self.log.warning("Unable to open Vcs file for source '%s' (%s)" % (source, vcsfile))
    	for line in vcs.readlines():
    	  (field,value) = line.split(': ')
    	  field = field.strip()
    	  value = value.strip()
    	  if field == 'Blend':
    	    sprosp['blend'] = value
    	  elif field == 'Vcs-Browser':
    	    sprosp['vcs_browser'] = value
    	  else:
            matchvcs = vcs_type_re.match(field)
            if matchvcs:
              sprosp['vcs_type'] = matchvcs.groups()[0]
    	      sprosp['vcs_url'] = value
    	vcs.close()

        # Read output of dpkg-parsechangelog
        p = Popen("LC_ALL=C dpkg-parsechangelog -l"+upath+'/'+source+'.changelog', shell=True, bufsize=4096,
          stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        errstring = p.stderr.read()
        if errstring != '':
          self.log.warning("Error parsing changelog of '%s' of %s\n %s:" % (source, sprosp['blend'], errstring))
        for stanza in deb822.Sources.iter_paragraphs(p.stdout):
          if source != stanza['source']:
            print >>stderr, "Something is wrong with changelog data of package '%s' of %s.  Changelog says source = '%s'." % (source, sprosp['blend'], stanza['source'])
          for prop in ('source', 'distribution'):
            if stanza.has_key(prop):
              sprosp[prop] = stanza[prop]
            else:
             self.log.warning("Missing property %s in changelog of '%s' of %s" % (prop, source, sprosp['blend']))
          sprosp['chlog_version']    = stanza['version']
          if stanza.has_key('maintainer'):
            sprosp['changed_by']       = stanza['maintainer']
            (name, email) = parse_email(stanza['maintainer'])
            sprosp['changed_by_name']  = name
            sprosp['changed_by_email'] = email
          else:
            sprosp['changed_by']       = ''
            sprosp['changed_by_name']  = ''
            sprosp['changed_by_email'] = ''
            self.log.warning("Can not obtain maintainer e-mail from changelog of '%s' of %s" % (source, sprosp['blend']))
          if stanza.has_key('date'):
            sprosp['chlog_date']       = stanza['date']
          else:
            sprosp['chlog_date']       = ''
            self.log.warning("Can not obtain changed data from changelog of '%s' of %s" % (source, sprosp['blend']))
          sprosp['closes'] = []
          if stanza.has_key('closes'):
            for bug in stanza['closes'].split(' '):
              sprosp['closes'].append(int(bug))
          changes                      = stanza['changes']
          sprosp['wnpp'] = 0
          sprosp['wnpp_type'] = ''
          sprosp['wnpp_desc'] = ''
#          if match: # try to make sure we are really dealing with ITPs
          for iwnpp in sprosp['closes']:
            if iwnpp == 12345: # that seems to be a fake ITP
              self.log.debug("Fake WNPP no. 12345 in changelog of '%s' of %s" % (source, sprosp['blend']))
              continue
            elif iwnpp > 0:
              sprosp['wnpp'] = iwnpp
              cur.execute("EXECUTE check_itp (%s)", (iwnpp,))
              if cur.rowcount > 0:
                wnppbug = RowDictionaries(cur)[0]
                itpmatch = parse_itp_re.search(wnppbug['title'])
                if itpmatch:
                  sprosp['wnpp_type'] = itpmatch.groups()[0]
                  sprosp['wnpp_desc'] = itpmatch.groups()[2]
                  if source != itpmatch.groups()[1]:
                    self.log.info("Source name of '%s' of %s differs from name in %s bug: package name = %s, short description = %s" % (source, sprosp['blend'], itpmatch.groups()[0], itpmatch.groups()[1], itpmatch.groups()[2]))
                else:
                  self.log.warning("Cannot parse ITP bug %i for package '%s' of %s: `%s`" % (iwnpp, source, sprosp['blend'], wnppbug['title']))
              else:
                self.log.debug("ITP bug %i for package '%s' of %s is not open any more or can otherwise not be found" % (iwnpp, source, sprosp['blend']))
                continue # Try other bug number if exists
              break
          match = find_itp_re.search(changes)
          if not match and sprosp['wnpp_type'] == '' and len(sprosp['closes']) > 0 and sprosp['wnpp'] > 0:
            sprosp['wnpp'] = 0
            self.log.warning("Bug %s closed in changelog of package '%s' of %s does not seem to be an ITP" % (str(sprosp['closes']), source, sprosp['blend']))
    	
    	# Read Copyright file if specifying Format in the first line
        cprfile = upath+'/'+source+'.copyright'
    	try:
    	  cpr = open(cprfile,'r')
    	except:
    	  self.log.debug("Unable to open Copyright file for source '%s' of %s (%s)" % (source, sprosp['blend'], cprfile))
    	  cpr = None
    	linenr = 0
    	found_files = False
    	sprosp['license'] = ''
    	if cpr:
    	  for line in cpr.readlines():
    	    line = line.strip()
    	    if line == '':
    	      if found_files:
    	        found_files = False
    	        break # We might leave the 'Files: *' paragraph again
    	      continue
    	    try:
    	      (field,value) = line.split(': ')
    	    except ValueError:
    	      # either no DEP5 file or no line we want to read here
    	      continue
    	    if linenr == 0:
    	      if field != 'Format':
    	        self.log.debug("Copyright file for source '%s' of %s does not seem to regard DEP5.  Found line `%s`" % (source, sprosp['blend'], line.strip()))
    	        found_files = True # one flag is enough to control this - we do not need another warning in the logs
    	        break
    	    linenr += 1
    	    field = field.strip()
    	    value = value.strip()
    	    if field == 'Files' and value == '*':
    	      found_files = True
    	    if field == 'License' and found_files:
    	      sprosp['license'] = value
    	      break
    	  if not found_files:
            self.log.debug("No 'Files: *' specification found in copyright file for source '%s' of %s" % (source, sprosp['blend']))

    	# Try to read debian/control
    	ctrl = None
    	ctrlfile = upath+'/'+source+'.control'
    	try:
    	  ctrl = open(ctrlfile,'r')
    	except:
    	  self.log.warning("Unable to open control file for source '%s' of %s (%s)" % (source, sprosp['blend'], ctrlfile))
    	# FIXME: This part is deactivated via 1==0 due to the fact that iter_paragraphs does not seem to work for debian/control files
    	if ctrl:
	    ictrl = deb822.Deb822.iter_paragraphs(ctrl)
	    src = ictrl.next()
	    # print 'SOURCE:', src      # print Source stanza
            if src.has_key('source'):
              if source != src['source']:
                self.log.error("Something is wrong with control data of package '%s' of %s.  Changelog says source = '%s'." % (source, sprosp['blend'], src['Source']))
            else:
    	      self.log.warning("Control file for source '%s' of %s is lacking source field" % (source, sprosp['blend']))
    	    if src.has_key('vcs-browser'):
    	      if sprosp['vcs_browser'] != src['vcs-browser']:
    	        tmp_prosp = re.sub('/$', '', sprosp['vcs_browser']) # ignore forgotten '/' at end of Vcs-Browser
                tmp_src = re.sub('/$', '', src['vcs-browser'])     # same with string in debian/control to enable comparison after further changes below
                tmp_src = re.sub('\.git;a=summary$', '.git', tmp_src)
                tmp_src = re.sub('/viewsvn/', '/wsvn/', tmp_src) # machine-readable gatherer implies /wsvn/ but specifying /viewsvn/ does no harm
                tmp_src = re.sub('/anonscm.debian.org/gitweb/\?p=', '/git.debian.org/?p=', tmp_src)
                tmp_src = re.sub('/anonscm.debian.org/git/([^?])', '/git.debian.org/?p=\\1', tmp_src) # Add missing '?p='
                tmp_src = re.sub('/anonscm\.debian\.org/viewvc', '/svn.debian.org/wsvn', tmp_src) # FIXME: is it correct to assume SVN here??? - probably not
                tmp_src = re.sub('\.debian\.org/viewvc', '.debian.org/wsvn', tmp_src) # somehow there seem some viewvc calls to remain
                tmp_src = re.sub('/\?op=log', '', tmp_src) # Some SVN URLs specify this parameter which should not be regarded here
    	        if tmp_prosp != tmp_src:
    	          tmp_src = re.sub('^git:', 'http:', tmp_src) # check for usual error in specifying Vcs-Browser by just leaving 'git:' as protocol
    	          if tmp_src == sprosp['vcs_browser']:
    	            self.log.error("%s of %s - Wrong Vcs-Browser: Use 'http:' instead of 'git:' in '%s' ('%s')." % (source, sprosp['blend'], src['Vcs-Browser'], sprosp['vcs_browser']))
    	          else:
                    tmp_prosp = re.sub('/trunk/?$', '', tmp_prosp) # sometimes the trailing trunk/ is forgotten which is no real problem
                    tmp_src   = re.sub('/trunk/?$', '', tmp_src)   # also in tmp_src there is sometimes a remaining /trunk
    	            if tmp_prosp != tmp_src:
                      self.log.warning("%s of %s - Differing Vcs-Browser:  Obtained from Vcs-Browser='%s' <-> control has '%s'." % (source, sprosp['blend'], sprosp['vcs_browser'], src['Vcs-Browser']))
            else:
    	      self.log.debug("Control file for source '%s' of %s is lacking Vcs-Browser field" % (source, sprosp['blend']))

    	    if src.has_key('Maintainer'):
              sprosp['maintainer']       = src['maintainer']
              (name, email) = parse_email(src['maintainer'])
              sprosp['maintainer_name']  = name
              sprosp['maintainer_email'] = email
            else:
    	      self.log.info("Control file for source '%s' of %s is lacking Maintainer field" % (source, sprosp['blend']))

            for prop in ('homepage', 'priority', 'section', 'uploaders', ):
              if src.has_key(prop):
                if prop == 'section':
                  if src['section'].startswith('non-free'):
                    sprosp['component'] = 'non-free'
                    (dummy,sprosp['section']) = src['section'].split('/')
                    if sprosp['license'] == '':
                      sprosp['license'] = 'non-free'
                  elif src['section'].startswith('contrib'):
                    sprosp['component'] = 'contrib'
                    (dummy,sprosp['section']) = src['section'].split('/')
                    if sprosp['license'] == '':
                      sprosp['license'] = 'free'
                  else:
                    sprosp['component'] = 'main'
                    sprosp['section']   = src['section']
                    if sprosp['license'] == '':
                      sprosp['license'] = 'free'
                else:
                  sprosp[prop] = src[prop]
              else:
                sprosp[prop] = ''
                if prop != 'uploaders':
                  self.log.warning("Control file for source '%s' of %s is lacking %s field" % (source, sprosp['blend'], prop))
                else:
                  self.log.debug("Control file for source '%s' of %s is lacking %s field" % (source, sprosp['blend'], prop))

            pkg = ictrl.next()
            valid_pkg_info = True
            while pkg:
              pprosp = {}
              for sprop in sprosp.keys():
                pprosp[sprop] = sprosp[sprop]

              if pkg.has_key('package'):
                  pprosp['package'] = pkg['package']
              else:
                  self.log.warning("Control file for source '%s' od %s is lacking Package field" % (source, sprosp['blend']))
              if pkg.has_key('description'):
                  if len(pkg['description'].split("\n",1)) > 1:
                    pprosp['long_description'] = pkg['description'].split("\n",1)[1]
                  else:
                    pprosp['long_description'] = ''
                  pprosp['description'] = pkg['description'].split("\n",1)[0].strip()
              else:
                  if pprosp.has_key('package'):
                    self.log.warning("Control file for source '%s' of %s has no desription for Package %s" % (source, sprosp['blend'], pprosp['package']))
                  else:
                    # self.log.error("Control file for source '%s' of %s seems to miss package information" % (source, sprosp['blend']))
                    self.log.info("Control file for source '%s' of %s seems to contain some comments which can not be parsed/ignored with this python-debian version" % (source, sprosp['blend']))
                    valid_pkg_info = False
              if valid_pkg_info:
                pkgs.append(pprosp)
              try:
                pkg = ictrl.next()
                valid_pkg_info = True
              except:
                break
    	# Try to read debian/control
    	upstream = None
    	ufile = upath+'/'+source+'.upstream'
    	if exists(ufile):
          cur.execute("EXECUTE check_reference (%s)", (source,))
          if cur.fetchone()[0] == 0:
             upstream = upstream_reader(ufile, source, self.log)
             if upstream.references:
               upstream.parse()
               for ref in upstream.get_bibrefs():
                 bibrefs.append(ref)

    cur.execute("""PREPARE package_insert AS INSERT INTO %s
        (blend, package, source,
         maintainer, maintainer_name, maintainer_email,
         changed_by, changed_by_name, changed_by_email,
         uploaders,
         description, long_description,
         homepage, component, section, priority,
         vcs_type, vcs_url, vcs_browser,
         wnpp, wnpp_type, wnpp_desc,
         license, chlog_date, chlog_version)
        VALUES
        ( $1, $2, $3,
          $4, $5, $6,
          $7, $8, $9,
          $10,
          $11, $12,
          $13, $14, $15, $16,
          $17, $18, $19,
          $20, $21, $22,
          $23, $24, $25)
        """ %  (my_config['table']))
    pkgquery = """EXECUTE package_insert
      (%(blend)s, %(package)s, %(source)s,
       %(maintainer)s, %(maintainer_name)s, %(maintainer_email)s,
       %(changed_by)s, %(changed_by_name)s, %(changed_by_email)s,
       %(uploaders)s,
       %(description)s, %(long_description)s,
       %(homepage)s, %(component)s, %(section)s, %(priority)s,
       %(vcs_type)s, %(vcs_url)s, %(vcs_browser)s,
       %(wnpp)s, %(wnpp_type)s, %(wnpp_desc)s,
       %(license)s, %(chlog_date)s, %(chlog_version)s)"""
    try:
      cur.executemany(pkgquery, pkgs)
    except ProgrammingError:
      print "Error while inserting packages"
      raise

    cur.execute("DEALLOCATE package_insert")
    
    # Inserting references should be save because above we are testing for existant table entries
    query = """PREPARE bibref_insert (text, text, text, text, int) AS INSERT INTO bibref
                   (source, key, value, package, rank)
                    VALUES ($1, $2, $3, $4, $5)"""
    cur.execute(query)
    bibquery = "EXECUTE bibref_insert (%(source)s, %(key)s, %(value)s, %(package)s, %(rank)s)"
    try:
      cur.executemany(bibquery, bibrefs)
    except ProgrammingError:
      print "Error while inserting references"
      raise
    cur.execute("DEALLOCATE bibref_insert")

    cur.execute("ANALYZE %s" % my_config['table'])

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
