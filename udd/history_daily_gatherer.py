#!/usr/bin/env python

"""
This script imports some historical data on a daily basis into UDD
"""

from aux import quote
from gatherer import gatherer
import re

def get_gatherer(connection, config, source):
  return history_daily_gatherer(connection, config, source)

class history_daily_gatherer(gatherer):

  def __init__(self, connection, config, source):
    gatherer.__init__(self, connection, config, source)
    self.assert_my_config()

  def run(self):
    #start harassing the DB, preparing the final inserts and making place
    #for the new data:
    cur = self.cursor()
    cur2 = self.cursor()

    # source format
    data = {}
    cur.execute("""SELECT format, COUNT(DISTINCT source) AS cnt FROM sources
    WHERE distribution='debian' and release='sid' GROUP BY format""")
    rows = {}
    for r in cur.fetchall():
        rows[r[0]] = r[1]
    data['format_3native'] = rows['3.0 (native)']
    data['format_3quilt'] = rows['3.0 (quilt)']
    cur.execute("""SELECT vcs_type, COUNT(DISTINCT source) AS cnt FROM sources
    WHERE distribution='debian' and release='sid' GROUP BY vcs_type""")
    rows = {}
    for r in cur.fetchall():
        rows[r[0]] = r[1]
    data['vcstype_arch'] = rows.get('Arch',0)
    data['vcstype_bzr'] = rows.get('Bzr',0)
    data['vcstype_cvs'] = rows.get('Cvs',0)
    data['vcstype_darcs'] = rows.get('Darcs',0)
    data['vcstype_git'] = rows.get('Git',0)
    data['vcstype_hg'] = rows.get('Hg',0)
    data['vcstype_mtn'] = rows.get('Mtn',0)
    data['vcstype_svn'] = rows.get('Svn',0)

    cur2.execute("""INSERT INTO history.sources_count (ts, 
        format_3native, format_3quilt,
        vcstype_arch, vcstype_bzr, vcstype_cvs, vcstype_darcs, vcstype_git, vcstype_hg, vcstype_mtn, vcstype_svn
        ) VALUES (NOW(),
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (data['format_3native'], data['format_3quilt'],
             data['vcstype_arch'], data['vcstype_bzr'], data['vcstype_cvs'], data['vcstype_darcs'], data['vcstype_git'], data['vcstype_hg'], data['vcstype_mtn'], data['vcstype_svn']))

if __name__ == '__main__':
  main()

# vim:set et tabstop=2:
