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
 	r           RECORD;
    BEGIN
        FOR r IN
            SELECT release || CASE WHEN char_length(substring(distribution from '-.*')) > 0
                                        THEN substring(distribution from '-.*')
                                        ELSE '' END AS release,
                            -- make *-volatile a "pseudo-release"
                        regexp_replace(version, '^[0-9]:', '') AS version,
                        array_to_string(array_sort(array_accum(architecture)),','),
                        component
                    FROM packages
	           WHERE package = $1
		   GROUP BY version, release, distribution, component
		   ORDER BY version
	      LOOP
	  RETURN NEXT r;
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
