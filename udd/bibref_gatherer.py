#!/usr/bin/env python

"""
This script imports bibliographic references from upstream-metadata.debian.net.
"""

from gatherer import gatherer
from sys import stderr, exit
from os import listdir, unlink, rename, access, X_OK
from os.path import isfile
from fnmatch import fnmatch
import yaml
from psycopg2 import IntegrityError, InternalError
import re
import logging
import logging.handlers
from subprocess import Popen, PIPE

from types import *

debug=0

def get_gatherer(connection, config, source):
  return bibref_gatherer(connection, config, source)

def rm_f(file):
  try:
    unlink(file)
  except OSError:
    pass

def cleanup_tex_logs(basetexfile):
  rm_f(basetexfile+'.aux')
  rm_f(basetexfile+'.bbl')
  rm_f(basetexfile+'.blg')
  rm_f(basetexfile+'.log')

# seek for authors separated by ',' rather than by ' and '
seek_broken_authors_re = re.compile('^[^\s^,]+\s+[^\s^,]+\s*,\s*[^\s^,]+\s+[^\s^,]')

def open_tex_process(texexe, basetexfile):
  if texexe == 'pdflatex':
    ptex = Popen(['pdflatex', '-interaction=batchmode', basetexfile], shell=False, stdout=PIPE)
  elif texexe == 'bibtex':
    ptex = Popen(['bibtex', basetexfile], shell=False, stdout=PIPE)
  else:
    return(False, 'Wrong exe: '+texexe)
  errstring=""
  if ptex.wait():
    if texexe == 'pdflatex':
      for logrow in ptex.communicate()[0].splitlines():
        if logrow.startswith('!'):
          errstring += logrow
      return(False, errstring)
    else:
      for logrow in ptex.communicate()[0].splitlines():
        if logrow.startswith('This is BibTeX'):
          continue
        errstring += logrow + '\n'
      return(True, errstring)
  return(True, errstring)

other_known_keys = ('Archive',
                    'Bug-Database',
                    'Cite-As',
                    'Contact',
                    'CRAN',
                    'Donation',
                    'Download',
                    'Help',
                    'Homepage',
                    'Name',
                    'Repository',
                    'Repository-Browse',
                    'Screenshots',
                    'Watch',
                    'Webservice')

class upstream_reader():
  """
  Read references from single debian/upstream file
  """

  def __init__(self, ufile, source, log):
    uf = open(ufile)
    self.source     = source
    self.references = None
    self.fields     = None
    self.log        = log
    self.ubibrefs = []
    self.ubibrefsinglelist = []

    try:
      self.fields = yaml.safe_load(uf.read())
    except yaml.scanner.ScannerError, err:
      self.log.error("Scanner error in file %s: %s" % (ufile, str(err)))
      return
    except yaml.parser.ParserError, err:
      self.log.error("Parser error in file %s: %s" % (ufile, str(err)))
      return
    except yaml.reader.ReaderError, err:
      self.log.error("Encoding problem in file %s: %s" % (ufile, str(err)))
    try:
      self.references=self.fields['Reference']
    except KeyError:
      warn_keys = []
      for key in self.fields.keys():
        if key not in other_known_keys:
          warn_keys.append(key)
        if len(warn_keys) > 0:
          log.warning("No references found for source package %s (Keys: %s)" % (self.source, str(warn_keys)))
          return
      return
    except TypeError:
      self.log.info("debian/upstream file of source package %s does not seem to be a YAML file" % (self.source))
    return

  def parse(self):
    if isinstance(self.references, list):
      # upstream file contains more than one reference
      rank={}      # record different ranks per binary package
      rank[''] = 0 # default is to have no specific Debian package which is marked by '' in the package column
      refid = 0
      for singleref in self.references:
        singleref['refid'] = refid # refid is not used currently but might make sense to identify references internally
        singleref['package'] = ''
        package_found = False
        for r in singleref.keys():
          key = r.lower()
          if key != 'debian-package':
            continue
          # self.log.warning("Source package '%s' has key 'debian-package'", self.source)
          pkg = singleref['package'] = singleref[r]
          package_found = True
          if rank.has_key(pkg):
            rank[pkg] += 1
          else:
            rank[pkg]  = 0
          singleref['rank'] = rank[pkg]
        if not package_found:
          singleref['rank'] = rank['']
          rank[''] += 1
      for singleref in self.references:
        self.setref(singleref, singleref['package'], singleref['rank'])
    elif isinstance(self.references, str):
      # upstream file has wrongly formatted reference
      self.log.error("File %s has following references: %s" % (ufile, self.references))
    else:
      # upstream file has exactly one reference
      package = ''
      for r in self.references.keys():
        key = r.lower()
        if key != 'debian-package':
          continue
        self.log.warning("Source package '%s' has key 'debian-package'", self.source)
        package = self.references[r]
      self.setref(self.references, package, 0)

    for key in self.fields.keys():
      keyl=key.lower()
      if keyl.startswith('reference-'):
        # sometimes DOI and PMID are stored separately:
        if keyl.endswith('doi'):
          if self.references.has_key('doi') or self.references.has_key('DOI'):
            self.log.warning("Extra key in source package '%s': %s - please remove from upstream file!", self.source, key)
            continue
          rdoi={}
          rdoi['rank']    = 0
          rdoi['source']  = self.source
          rdoi['key']     = 'doi'
          rdoi['value']   = self.fields[key]
          rdoi['package'] = ''          ### Hack!!! we should get rid of Reference-DOI soon to enable specifying 'debian-package' relieable
          self.ubibrefs.append(rdoi)
        elif keyl.endswith('pmid'):
          if self.references.has_key('pmid') or self.references.has_key('PMID'):
            self.log.warning("Extra key in source package '%s': %s - please remove from upstream file!", self.source, key)
            continue
          rpmid={}
          rpmid['rank']    = 0
          rpmid['source']  = self.source
          rpmid['key']     = 'pmid'
          rpmid['value']   = self.fields[key]
          rpmid['package'] = ''          ### Hack!!! we should get rid of Reference-PMID soon to enable specifying 'debian-package' relieable
          self.ubibrefs.append(rpmid)
        else:
          print "Source package %s has %s : %s" % (self.source, key, self.fields[key])

  def setref(self, references, package, rank):
    year=''
    defined_fields = { 'address'   : 0,
                       'article'   : 0,
                       'author'    : 0,
                       'booktitle' : 0,
                       'comment'   : 0,
                       'debian-package' : 0,
                       'doi'       : 0,
                       'editor'    : 0,
                       'eprint'    : 0,
                       'in'        : 0,
                       'issn'      : 0,
                       'journal'   : 0,
                       'license'   : 0,
                       'month'     : 0,
                       'number'    : 0,
                       'pages'     : 0,
                       'publisher' : 0,
                       'pmid'      : 0,
                       'title'     : 0,
                       'type'      : 0,
                       'url'       : 0,
                       'volume'    : 0,
                       'year'      : 0,
                     }
    for r in references.keys():
      # print r
      key = r.lower()
      if key == 'debian-package':
        continue
      if defined_fields.has_key(key):
        if defined_fields[key] > 0:
          self.log.error("Duplicated key in source package '%s': %s", self.source, key)
          continue
        else:
          defined_fields[key] = 1
      else:
          if key not in ('rank', 'package', 'refid'): # ignore internal maintenance fields
            self.log.warning("Unexpected key in source package '%s': %s", self.source, key)
          defined_fields[key] = 1
      ref={}
      ref['rank']    = rank
      ref['source']  = self.source
      ref['key']     = key
      ref['package'] = package
      if isinstance(references[r], int) or isinstance(references[r], float):
        ref['value']   = str(references[r])
      else:
        try:
          ref['value']   = references[r].strip()
        except AttributeError, err:
          if str(references[r]) == 'None':
            self.log.warning("No value given for field '%s' in source package %s - the field is ignored." % (r, self.source))
            continue
          else:
            self.log.error("Cannot parse value for source %s: r = %s -> value = %s" % (self.source, r, str(references[r])))
            ref['value']   = '???'
        if key == 'author':
          # Try to catch broken author formating
          new_author = re.sub(',\s* and\s*' , ' and ', ref['value'])
          if new_author != ref['value']:
            self.log.warning("Author of source package %s does contain invalid BibTeX format: %s will be turned into %s", self.source, ref['value'], new_author)
            ref['value'] = new_author
          if ref['value'].count(',') > ref['value'].lower().count(' and ') + 1:
            self.log.warning("Suspicious authors field in source package %s with way more ',' than ' and ' strings: %s", self.source, ref['value'])
          match = seek_broken_authors_re.search(ref['value'])
          if match:
            self.log.warning("Suspicious authors field in source package %s - seems to have comma separated authors: %s", self.source, ref['value'])
      self.ubibrefs.append(ref)
      if r.lower() == 'year':
        year = ref['value']
    # Create unique BibTeX key
    bibtexkey = self.source
    if bibtexkey in self.ubibrefsinglelist and year != '':
      bibtexkey = self.source+year
    if bibtexkey in self.ubibrefsinglelist:
      # if there are more than one reference per source package and even in
      # the same year append the rank as letter
      bibtexkey += 'abcdefghijklmnopqrstuvwxyz'[rank]
    ref={}
    ref['rank']    = rank
    ref['source']  = self.source
    ref['key']     = 'bibtex'
    ref['value']   = re.sub('\+', '-', re.sub('\.', '-', bibtexkey)) # avoid '.' and '+' in BibTeX keys
    ref['package'] = package
    self.ubibrefsinglelist.append(bibtexkey)
    self.ubibrefs.append(ref)
    return ref

  def get_bibrefs(self):
    return self.ubibrefs

class bibref_gatherer(gatherer):
  """
  Bibliographic references from debian/upstream files
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


    self.bibtexfile = 'debian.bib'
    self.bibtex_example_tex = 'debian.tex'

  def run(self):
    my_config = self.my_config
    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()

    u_dirs = listdir(my_config['path'])

    bibrefs = []

    for u in u_dirs:
      upath=my_config['path']+'/'+u
      sources = []
      for file in listdir(upath):
        if fnmatch(file, '*.upstream'):
          sources.append(re.sub("\.upstream", "", file))
      for source in sources:
        # print source
        ufile = upath+'/'+source+'.upstream'

        upstream = upstream_reader(ufile, source, self.log)
        if not upstream.references:
          continue

        upstream.parse()
        
        for ref in upstream.get_bibrefs():
          bibrefs.append(ref)

    # only truncate table if there are really some references found
    if len(bibrefs) == 0:
      self.log.error("No references found in any upstream file.")
      exit(1)

    cur.execute("TRUNCATE %s" % (my_config['table']))
    query = """PREPARE bibref_insert (text, text, text, text, int) AS
                   INSERT INTO %s
                   (source, key, value, package, rank)
                    VALUES ($1, $2, $3, $4, $5)""" % (my_config['table'])
    cur.execute(query)

    query = "EXECUTE bibref_insert (%(source)s, %(key)s, %(value)s, %(package)s, %(rank)s)"
    for ref in bibrefs:
      try:
        cur.execute(query, ref)
      except UnicodeEncodeError, err:
        self.log.error("Unable to inject data: %s\n%s" % (str(ref),str(err)))
        exit(1)
      except IntegrityError, err:
        self.log.error("Unable to inject data: %s\n%s" % (str(ref),str(err)))
        exit(1)
      except InternalError, err:
        self.log.error("Unable to inject data: %s\n%s" % (str(ref),str(err)))
        exit(1)
      except KeyError, err:
        self.log.error("Unable to inject data: %s\n%s" % (str(ref),str(err)))
        exit(1)
    cur.execute("DEALLOCATE bibref_insert")
    cur.execute("ANALYZE %s" % my_config['table'])

    # commit before check to make sure the table is not locked in case LaTeX run will fail for whatever reason
    self.connection.commit()

    # if there is a working LaTeX installation try to build a BibTeX database and test it by creating a debian.pdf file
    if isfile('/usr/bin/pdflatex') and access('/usr/bin/pdflatex', X_OK) and \
       isfile('/usr/bin/bibtex')   and access('/usr/bin/bibtex', X_OK) and \
       ( isfile('/usr/share/texlive/texmf-dist/fonts/source/jknappen/ec/ecrm.mf') or \
         isfile('/usr/share/texmf-texlive/fonts/source/jknappen/ec/ecrm.mf') ) :
      # create BibTeX file
      bf = open(self.bibtexfile, 'w')
      cur.execute("SELECT * FROM bibtex()")
      for row in cur.fetchall():
	print >>bf, row[0]
      bf.close()

      # create LaTeX file to test BibTeX functionality
      bf = open(self.bibtex_example_tex, 'w')
      print >>bf, """\documentclass[10]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[left=2mm,top=2mm,right=2mm,bottom=2mm,nohead,nofoot]{geometry}
\usepackage{longtable}
\usepackage[super]{natbib}
\setlongtables
\\begin{document}
\small
\\begin{longtable}{llp{70mm}l}
\\bf package & \\bf source & \\bf description & BibTeX key \\\\ \hline"""

      cur.execute("SELECT * FROM bibtex_example_data() AS (package text, source text, bibkey text, description text)")
      for row in cur.fetchall():
	print >>bf, row[0], '&', row[1], '&', row[3] , '&', row[2]+'\cite{'+row[2]+'} \\\\'

      print >>bf, """\end{longtable}

% \\bibliographystyle{plain}
% Try a bit harder by also including URL+DOI
\\bibliographystyle{plainnat}
\\bibliography{debian}

\end{document}
"""
      bf.close()

      # try to build debian.pdf file to test aboc LaTeX file
      basetexfile = self.bibtex_example_tex.replace('.tex','')
      cleanup_tex_logs(basetexfile)
      try:
        rename(basetexfile+'.pdf', basetexfile+'.pdf~')
      except OSError:
        pass

      (retcode,errstring) = open_tex_process('pdflatex', basetexfile)
      if not retcode:
        self.log.error("Problem in 1. PdfLaTeX run of %s.tex: `%s` --> please inspect %s.log" % (basetexfile, errstring, basetexfile))
        exit(1)
      (retcode,errstring) = open_tex_process('bibtex', basetexfile)
      if errstring != "":
        if not retcode:
          self.log.error("Problem in BibTeX run of %s.bib: `%s`" % (basetexfile, errstring))
          exit(1)
        self.log.error("Ignore the following problems in BibTeX run of %s.bib: `%s`" % (basetexfile, errstring))
      (retcode,errstring) = open_tex_process('pdflatex', basetexfile)
      if not retcode:
        self.log.error("Problem in 2. PdfLaTeX run of %s.tex: `%s` --> please inspect %s.log" % (basetexfile, errstring, basetexfile))
        exit(1)
      (retcode,errstring) = open_tex_process('pdflatex', basetexfile)
      if not retcode:
        self.log.error("Problem in 3. PdfLaTeX run of %s.tex: `%s` --> please inspect %s.log" % (basetexfile, errstring, basetexfile))
        exit(1)

      cleanup_tex_logs(basetexfile)

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
