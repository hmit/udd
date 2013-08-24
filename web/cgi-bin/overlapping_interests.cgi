#!/usr/bin/env python
"""
Takes two arguments deva and devb which are the maintainers emails 
and returns a list of package names. This list consists of the packages 
of devb that are a dependency to some package maintained by deva.
"""

import cgi, re, sys
import pprint

import psycopg2

DATABASE = {'database': 'udd',
            'port': 5452,
            'host': 'localhost',
            'user': 'guest',
           }


def execute_query(query):
    conn = psycopg2.connect(**DATABASE)
    cursor = conn.cursor()
    cursor.execute(query)

    row = cursor.fetchone()
    while not row is None:
        yield row
        row = cursor.fetchone()

    cursor.close()
    conn.close()

def qet_maintainer_depends(maintainer):
    query="""SELECT DISTINCT depends 
                FROM all_packages 
            WHERE maintainer_email='{0}' AND depends is not NULL """.format(maintainer)

    depends = set()
    for row in execute_query(query):
        dep_line = row[0]
        dep_line = dep_line.replace(',', ' ').replace('|', ' ')
        # Remove versions from versioned depends
        dep_line = re.sub('\(.*\)', '', dep_line)
        
        for x in dep_line.split(' '):
            stripped = x.strip()

            if stripped :
                #add ' character so they can be imported 
                #into a where clause of another query
                depends.add("'"+stripped+"'")
        
    return list(depends)

def get_overlapping_pks(depends, maintainer):
    query = """SELECT DISTINCT package FROM all_packages 
            WHERE package in ({0}) AND maintainer_email='{1}'""".format(','.join(depends), maintainer)

    for row in execute_query(query):        
        yield row[0]

def main():
    print "Content-type: text/html\n\n"

    arguments = cgi.FieldStorage()
    
    if not "deva" in arguments or not "devb" in arguments:
        print "Not deva or devb argument was provided."
        sys.exit(-1)
     
    depends = qet_maintainer_depends(arguments["deva"].value)  
    pkgs = get_overlapping_pks(depends, arguments["devb"].value)
    
    for pkg in pkgs:
        print pkg

if __name__ == '__main__':
    main()
