/******************************************************************************
 * Sometimes it is practical to aggregate a collumn to a comma separated list *
 * This is described at:                                                      *
 *                                                                            *
 *  http://www.zigo.dhs.org/postgresql/#comma_aggregate                       *
 *                                                                            *
 ******************************************************************************/

CREATE AGGREGATE array_accum (anyelement) (
    sfunc = array_append,
    stype = anyarray,
    initcond = '{}'
); 

/*****************************************************************************
 * this can be used like this:                                               *
 *     array_to_string(array_accum(column),',')                              *
 * Example:                                                                  *
 *                                                                           *
   SELECT av.version, array_to_string(array_accum(architecture),',') FROM
     ( SELECT architecture AS architecture, version FROM packages
          WHERE package = 'gcc' GROUP BY architecture, version ORDER BY architecture
     ) AS av
     GROUP BY version ORDER BY version DESC;
 *                                                                           *
 *****************************************************************************/



