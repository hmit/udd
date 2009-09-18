#!/usr/bin/python                                 
#
# Author:    Sandro Tosi <morph@debian.org>
# Date:	     2009-09-18
# Copyright: Copyright (C) 2009 Sandro Tosi <morph@debian.org>
# License:   Public Domain
#
# Extract from UDD the source packages both in Debian and Ubuntu with higher
# version in Ubuntu than in Debian

# module to access PostgreSQL databases
import psycopg2

# connect to UDD database
conn = psycopg2.connect(database="udd", port=5441, host="localhost", user="guest")

# prepare a cursor                     
cur = conn.cursor()                    

# this is the query we'll be making
query = """                        
select debian.source, debian.version, ubuntu.version
  from (select source, max(version) as version from sources group by 1) debian,
       (select source, max(version) as version from ubuntu_sources group by 1) ubuntu
 where debian.source = ubuntu.source
   and debian.version < ubuntu.version
 order by 1"""

# execute the query
cur.execute(query)

# retrieve the whole result set
data = cur.fetchall()

# close cursor and connection
cur.close()
conn.close()

# print results

# heading
print "Source packages with a higher version in Ubuntu than in Debian\n"
print "%30s %25s %25s" % ('Source Package Name', 'Debian Version', 'Ubuntu Version')
print "-"*82

# actual data
for row in data:
    print "%30s %25s %25s" % row
