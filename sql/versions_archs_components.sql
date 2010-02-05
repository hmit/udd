/***********************************************************************************
 * Obtain available versions in different releases for a given package             *
 * This function takes a package name as argument and returns a table containing   *
 * the release names in which the package is available, the version of the package *
 * in this release and a string contained an alphabethically sorted list of        *
 * architectures featuring these version.  In the last column the component is     *
 * given.                                                                          *
 * See below for an usage example.                                                 *
 ***********************************************************************************/

CREATE OR REPLACE FUNCTION versions_archs_component (text) RETURNS SETOF RECORD AS $$
    Declare
        package     ALIAS FOR $1 ;

 	r           RECORD;
	q           RECORD;
	query       text;
        query1      text;
    BEGIN
	-- make sure we have the components in reasonable order
        query = 'SELECT component FROM (SELECT component, version FROM packages WHERE package = '''
	         || package || ''' GROUP BY component, version ORDER BY version) AS cv GROUP BY component;';

	FOR r IN EXECUTE query LOOP
	    query1      = /* -- DROP TABLE IF EXISTS tmpReleaseVersionArch ; */
                 'CREATE TEMPORARY TABLE tmpReleaseVersionArch AS
	         SELECT release || CASE WHEN char_length(substring(distribution from ''-.*'')) > 0
                                        THEN substring(distribution from ''-.*'')
                                        ELSE '''' END AS release,
                            -- make *-volatile a "pseudo-release"
                        regexp_replace(version, ''^[0-9]:'', '''') AS version,
                        architecture AS arch, component
                    FROM packages
	           WHERE package = ''' || package || ''' AND component = ''' || r.component || '''
		   GROUP BY architecture, version, release, distribution, component
	         ;' ;
	    EXECUTE query1;
	    query1 = 'SELECT release, version, array_to_string(array_sort(array_accum(arch)),'',''), CAST(''' 
                 || r.component || ''' AS text) AS component FROM tmpReleaseVersionArch
                 GROUP BY release, version ORDER BY version;' ;
	    FOR q IN EXECUTE query1 LOOP
	        RETURN NEXT q;
	    END LOOP;
	    DROP TABLE tmpReleaseVersionArch ;
        END LOOP;
    END; $$ LANGUAGE 'plpgsql';

/***********************************************************************************
 * Example of usage: Package seaview which has versions is in different components *

   SELECT r as release, version, archs, component
     FROM versions_archs_component('seaview') AS (r text, version text, archs text, component text)
          -- you have to specify the column names because plain RECORD type is returned
     JOIN releases ON releases.release = r
          -- JOIN with release table to enable reasonable sorting
    WHERE r NOT LIKE '%-%'
          -- ignore releases like *-security etc.
    ORDER BY releases.sort;

 ***********************************************************************************/

