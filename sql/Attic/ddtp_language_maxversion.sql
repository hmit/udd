-- return language, short/long description and maximum version of a ddtp translation

BEGIN ; 

DROP TYPE IF EXISTS DdtpRecordType CASCADE;

/*
CREATE TYPE DdtpRecordType AS (
    package      text,
    distribution text,
    release      text,
    component    text,
    version      text,
    language	 text,
    description  text,
    long_description text,
    md5sum       text
);

CREATE OR REPLACE FUNCTION DdtpLanguageMaxVersion(text)
   RETURNS SETOF DdtpRecordType AS $$
   DECLARE
     pkg ALIAS FOR $1 ;
     lang      RECORD ;
     max       RECORD ;
     ret       DdtpRecordType%rowtype ;
     query     text ;
     query2    text ;
     query3    text ;

   BEGIN

     query = 'SELECT language FROM ddtp WHERE package = ''' || pkg || ''' GROUP BY language ORDER BY language;' ;

     FOR lang IN EXECUTE query LOOP
     	 query2 = 'SELECT MAX(version) AS version FROM ddtp WHERE package = ''' || pkg || ''' AND language = ''' || lang.language || '''' ;
         FOR max IN EXECUTE query2 LOOP
     	    query3 = 'SELECT * FROM ddtp WHERE package = ''' || pkg || ''' AND language = ''' || lang.language || ''' AND version = ''' || CAST(max.version AS text) ||
     	             ''' LIMIT 1 '; -- make sure we really get only one result per language, even if there should not be more anyway
     	    FOR ret in EXECUTE query3 LOOP
     		RETURN NEXT ret;
	     END LOOP ;
	 END LOOP ;
     END LOOP ;

     RETURN;
END; $$ LANGUAGE 'plpgsql';

*/

COMMIT ;
