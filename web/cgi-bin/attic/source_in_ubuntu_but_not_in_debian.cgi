#!/usr/bin/python                                 
#
# Author:    Sandro Tosi <morph@debian.org>
# Date:	     2009-09-18
# Copyright: Copyright (C) 2009 Sandro Tosi <morph@debian.org>
# License:   Public Domain
#
# Extract from UDD the source packages in Ubuntu but not in Debian

# module to access PostgreSQL databases
import psycopg2

# connect to UDD database
conn = psycopg2.connect(database="udd", port=5452, host="localhost", user="guest")

# prepare a cursor                     
cur = conn.cursor()                    

# this is the query we'll be making
query = """                        
select source, max(version)
  from ubuntu_sources
 where source not in (select distinct source from sources)
 group by source
 order by 1"""

# execute the query
cur.execute(query)

# retrieve the whole result set
data = cur.fetchall()

# close cursor and connection
cur.close()
conn.close()

# print results

# CGI Content-type
print "Content-type: text/plain\n\n"

# heading
print "Source packages in Ubuntu but not in Debian\n"
print "%35s %25s" % ('Source Package Name', 'Ubuntu Version')
print "-"*61

# actual data
for row in data:
    print "%35s %25s" % row
