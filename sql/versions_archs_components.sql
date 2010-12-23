/***********************************************************************************
 * Obtain available versions in different releases for a given package             *
 * This function takes a package name as argument and returns a table containing   *
 * the release names in which the package is available, the version of the package *
 * in this release and a string contained an alphabethically sorted list of        *
 * architectures featuring these version.  In the last column the component is     *
 * given.                                                                          *
 * See below for an usage example.                                                 *
 ***********************************************************************************/

CREATE OR REPLACE FUNCTION versions_archs_component_sql (text) RETURNS SETOF RECORD AS $$
       SELECT p.release, version, archs, component FROM
          ( SELECT release || CASE WHEN char_length(substring(distribution from '-.*')) > 0
                                        THEN substring(distribution from '-.*')
                                        ELSE '' END AS release,
                            -- make *-volatile a "pseudo-release"
                        regexp_replace(version, '^[0-9]:', '') AS version,
                        array_to_string(array_sort(array_accum(architecture)),',') AS archs,
                        component
                    FROM packages
	           WHERE package = $1
		   GROUP BY version, release, distribution, component
          ) p
	  JOIN releases ON releases.release = p.release
	  ORDER BY releases.sort, version;
 $$ LANGUAGE 'SQL';

/***********************************************************************************
 * Example of usage: Package seaview which has versions is in different components *

   SELECT * FROM versions_archs_component_sql('seaview') AS (release text, version text, archs text, component text);
          -- you have to specify the column names because plain RECORD type is returned
    WHERE release NOT LIKE '%-%'
          -- ignore releases like *-security etc.

   SELECT * FROM versions_archs_component_sql('libc6') AS (release text, version text, archs text, component text);

 ***********************************************************************************/
