-- 2012-07-01 addition of upstream gatherer

CREATE TABLE upstream (
   source text,
   version debversion,
   distribution text,
   release text,
   component text,
   watch_file text,
   debian_uversion text,
   debian_mangled_uversion text,
   upstream_version text,
   upstream_url text,
   errors text,
   warnings text,
   status text,
   last_check timestamp,
   primary key (source, version, distribution, release, component)
);

GRANT SELECT ON upstream TO PUBLIC;

CREATE TABLE vcs (
source text,
team text,
version debversion,
distribution text,
primary key(source)
);

GRANT SELECT ON vcs TO PUBLIC;

-- content of array_accum.sql
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
     ( SELECT architecture, version FROM packages
          WHERE package = 'gcc' GROUP BY architecture, version ORDER BY architecture
     ) AS av
     GROUP BY version ORDER BY version DESC;
 *                                                                           *
 *****************************************************************************/


-- content of releases.sql
/****************************************************************************************
 * This table enables sorting of releases according to their release date.  To define   *
 * a reasonable order also for releases which are not or never will be released an      *
 * additional column sort is defined.                                                   *
 * The relevant discussion can be found here:                                           *
 *   http://lists.debian.org/debian-qa/2010/02/msg00001.html                            *
 ****************************************************************************************/

CREATE TABLE releases (
       release     text,  /* keep name column as in other tables */
       releasedate date,
       sort        int,
       PRIMARY KEY (release)
);

INSERT INTO releases VALUES ( 'etch',                     '2007-04-08', 400 );
INSERT INTO releases VALUES ( 'etch-security',            '2007-04-08', 401 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'etch-proposed-updates',    '2007-04-08', 402 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'lenny',                    '2009-02-14', 500 );
INSERT INTO releases VALUES ( 'lenny-security',           '2009-02-14', 501 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'lenny-proposed-updates',   '2009-02-14', 502 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'squeeze',                  NULL,         600 );
INSERT INTO releases VALUES ( 'squeeze-security',         NULL,         601 );
INSERT INTO releases VALUES ( 'squeeze-proposed-updates', NULL,         602 );
INSERT INTO releases VALUES ( 'wheezy',                  NULL,         700 );
INSERT INTO releases VALUES ( 'wheezy-security',         NULL,         701 );
INSERT INTO releases VALUES ( 'wheezy-proposed-updates', NULL,         702 );
INSERT INTO releases VALUES ( 'sid',                      NULL,      100000 );
INSERT INTO releases VALUES ( 'experimental',             NULL,           0 ); /* this pseudo releases does not fit any order and it is not higher than unstable */

GRANT SELECT ON releases TO PUBLIC ;

-- content of array_sort.sql
/*****************************************************************************
 * Sorting an array.  See                                                    * 
 * http://www.postgres.cz/index.php/PostgreSQL_SQL_Tricks#General_array_sort *
 *****************************************************************************/
CREATE OR REPLACE FUNCTION array_sort (ANYARRAY)
RETURNS ANYARRAY LANGUAGE SQL
AS $$
SELECT ARRAY(
    SELECT $1[s.i] AS "foo"
    FROM
        generate_series(array_lower($1,1), array_upper($1,1)) AS s(i)
    ORDER BY foo
);
$$;

-- content of versions_archs_components.sql
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

-- content of screenshots.sql
-- http://screenshots.debian.net/json/screenshots

BEGIN;

DROP TABLE IF EXISTS screenshots CASCADE;

CREATE TABLE screenshots (
	package			text NOT NULL,
	version			text,
	homepage		text,
	maintainer_name		text,
	maintainer_email	text,
	description		text,
	section			text,
	screenshot_url		text NOT NULL,
	large_image_url		text NOT NULL,
	small_image_url		text NOT NULL,
    PRIMARY KEY (small_image_url)
);

GRANT SELECT ON screenshots TO PUBLIC;

COMMIT;

-- 'name'       --> 'package'
-- 'section'
-- 'maintainer' --> 'maintainer_name'
-- 'maintainer_email'
-- 'version'
-- 'homepage'
-- 'description'
-- 'url'	--> 'screenshot_url'
-- 'large_image_url'
-- 'small_image_url'

-- content of bibref.sql

/************************************************************************************
 * Storing and handling publication references maintained in debian/upstream files  *
 ************************************************************************************/

BEGIN;

DROP TABLE IF EXISTS bibref CASCADE;

CREATE TABLE bibref (
	source	text NOT NULL,
	key	text NOT NULL,
	value	text NOT NULL,
	package text DEFAULT '',
	rank    int  NOT NULL,
	PRIMARY KEY (source,key,package,rank) -- this helps preventing more than one times the same key for a single package
);

GRANT SELECT ON bibref TO PUBLIC;


/************************************************************************************
 * Create a BibTex file from references                                             *
 ************************************************************************************/

CREATE OR REPLACE FUNCTION bibtex ()
RETURNS SETOF TEXT LANGUAGE SQL
AS $$
  SELECT DISTINCT
         CASE WHEN bibjournal.value IS NULL AND bibin.value IS NOT NULL AND bibpublisher.value IS NOT NULL THEN '@Book{' || bibkey.value
              ELSE CASE WHEN bibauthor.value IS NULL OR bibjournal.value IS NULL THEN '@Misc{'|| bibkey.value ||
                   CASE WHEN bibauthor.value IS NULL THEN E',\n  Key     = "' || bibkey.value || '"' ELSE '' END -- without author we need a sorting key
              ELSE '@Article{' || bibkey.value END END  ||
            CASE WHEN bibauthor.value  IS NOT NULL THEN E',\n  Author  = {' || bibauthor.value  || '}' ELSE '' END ||
            CASE WHEN bibtitle.value   IS NOT NULL THEN E',\n  Title   = "{' || 
                  replace(replace(replace(bibtitle.value,
                        '_', E'\\_'),            --
                        '%', E'\\%'),            --
                        E'\xe2\x80\x89', E'\\,') -- TeX syntax for '_' and UTF-8 "thin space"
                                               -- see http://www.utf8-chartable.de/unicode-utf8-table.pl?start=8192&number=128&utf8=string-literal
                   || '}"'
                 ELSE '' END ||
            CASE WHEN bibbooktitle.value IS NOT NULL THEN E',\n  Booktitle = "{' || bibbooktitle.value || '}"' ELSE '' END ||
            CASE WHEN bibyear.value    IS NOT NULL THEN E',\n  Year    = {' || bibyear.value    || '}' ELSE '' END ||
            CASE WHEN bibmonth.value   IS NOT NULL THEN E',\n  Month   = {' || bibmonth.value   || '}' ELSE '' END ||
            CASE WHEN bibjournal.value IS NOT NULL THEN E',\n  Journal = {' || bibjournal.value || '}' ELSE '' END ||
            CASE WHEN bibaddress.value IS NOT NULL THEN E',\n  Address = {' || bibaddress.value || '}' ELSE '' END ||
            CASE WHEN bibpublisher.value IS NOT NULL THEN E',\n  Publisher = {' || bibpublisher.value || '}' ELSE '' END ||
            CASE WHEN bibvolume.value  IS NOT NULL THEN E',\n  Volume  = {' || bibvolume.value  || '}' ELSE '' END ||
            CASE WHEN bibnumber.value  IS NOT NULL THEN E',\n  Number  = {' || bibnumber.value  || '}' ELSE '' END ||
            CASE WHEN bibpages.value   IS NOT NULL THEN E',\n  Pages   = {' || regexp_replace(bibpages.value, E'(\\d)-([\\d])', E'\\1--\\2')   || '}' ELSE '' END ||
            CASE WHEN biburl.value     IS NOT NULL THEN E',\n  URL     = {' ||
                  replace(replace(replace(replace(biburl.value,
                        '_', E'\\_'),           --
                        '%', E'\\%'),           --
                        '&', E'\\&'),           --
                        '~', E'\\~{}')          --
                   || '}'
                 ELSE '' END ||
            CASE WHEN bibdoi.value     IS NOT NULL THEN E',\n  DOI     = {' ||
                  replace(replace(bibdoi.value,
                        '_', E'\\_'),           --
                        '&', E'\\&')            --
                   || '}'
                 ELSE '' END ||
            CASE WHEN bibpmid.value    IS NOT NULL THEN E',\n  PMID    = {' || bibpmid.value    || '}' ELSE '' END ||
            CASE WHEN bibeprint.value  IS NOT NULL THEN E',\n  EPrint  = {' ||
                  replace(replace(replace(replace(bibeprint.value,
                        '_', E'\\_'),           --
                        '%', E'\\%'),           --
                        '&', E'\\&'),           --
                        '~', E'\\~{}')          --
                   || '}'
                 ELSE '' END ||
            CASE WHEN bibin.value      IS NOT NULL THEN E',\n  In      = {' || bibin.value      || '}' ELSE '' END ||
            CASE WHEN bibissn.value    IS NOT NULL THEN E',\n  ISSN    = {' || bibissn.value    || '}' ELSE '' END ||
            E',\n}\n'
            AS bibentry
--         p.source         AS source,
--         p.rank           AS rank,
    FROM (SELECT DISTINCT source, package, rank FROM bibref) p
    LEFT OUTER JOIN bibref bibkey     ON p.source = bibkey.source     AND bibkey.rank     = p.rank AND bibkey.package     = p.package AND bibkey.key     = 'bibtex'
    LEFT OUTER JOIN bibref bibyear    ON p.source = bibyear.source    AND bibyear.rank    = p.rank AND bibyear.package    = p.package AND bibyear.key    = 'year'  
    LEFT OUTER JOIN bibref bibmonth   ON p.source = bibmonth.source   AND bibmonth.rank   = p.rank AND bibmonth.package   = p.package AND bibmonth.key   = 'month'  
    LEFT OUTER JOIN bibref bibtitle   ON p.source = bibtitle.source   AND bibtitle.rank   = p.rank AND bibtitle.package   = p.package AND bibtitle.key   = 'title'  
    LEFT OUTER JOIN bibref bibbooktitle ON p.source = bibbooktitle.source AND bibbooktitle.rank = p.rank AND bibbooktitle.package = p.package AND bibbooktitle.key = 'booktitle'  
    LEFT OUTER JOIN bibref bibauthor  ON p.source = bibauthor.source  AND bibauthor.rank  = p.rank AND bibauthor.package  = p.package AND bibauthor.key  = 'author'
    LEFT OUTER JOIN bibref bibjournal ON p.source = bibjournal.source AND bibjournal.rank = p.rank AND bibjournal.package = p.package AND bibjournal.key = 'journal'
    LEFT OUTER JOIN bibref bibaddress ON p.source = bibaddress.source AND bibaddress.rank = p.rank AND bibaddress.package = p.package AND bibaddress.key = 'address'
    LEFT OUTER JOIN bibref bibpublisher ON p.source = bibpublisher.source AND bibpublisher.rank = p.rank AND bibpublisher.package = p.package AND bibpublisher.key = 'publisher'
    LEFT OUTER JOIN bibref bibvolume  ON p.source = bibvolume.source  AND bibvolume.rank  = p.rank AND bibvolume.package  = p.package AND bibvolume.key  = 'volume'
    LEFT OUTER JOIN bibref bibdoi     ON p.source = bibdoi.source     AND bibdoi.rank     = p.rank AND bibdoi.package     = p.package AND bibdoi.key     = 'doi'
    LEFT OUTER JOIN bibref bibpmid    ON p.source = bibpmid.source    AND bibpmid.rank    = p.rank AND bibpmid.package    = p.package AND bibpmid.key    = 'pmid'
    LEFT OUTER JOIN bibref biburl     ON p.source = biburl.source     AND biburl.rank     = p.rank AND biburl.package     = p.package AND biburl.key     = 'url'
    LEFT OUTER JOIN bibref bibnumber  ON p.source = bibnumber.source  AND bibnumber.rank  = p.rank AND bibnumber.package  = p.package AND bibnumber.key  = 'number'
    LEFT OUTER JOIN bibref bibpages   ON p.source = bibpages.source   AND bibpages.rank   = p.rank AND bibpages.package   = p.package AND bibpages.key   = 'pages'
    LEFT OUTER JOIN bibref bibeprint  ON p.source = bibeprint.source  AND bibeprint.rank  = p.rank AND bibeprint.package  = p.package AND bibeprint.key  = 'eprint'
    LEFT OUTER JOIN bibref bibin      ON p.source = bibin.source      AND bibin.rank      = p.rank AND bibin.package      = p.package AND bibin.key      = 'in'
    LEFT OUTER JOIN bibref bibissn    ON p.source = bibissn.source    AND bibissn.rank    = p.rank AND bibissn.package    = p.package AND bibissn.key    = 'issn'
    ORDER BY bibentry -- p.source
;
$$;

/************************************************************************************
 * Example data for above BibTeX data                                               *
 ************************************************************************************/

CREATE OR REPLACE FUNCTION bibtex_example_data ()
RETURNS SETOF RECORD LANGUAGE SQL
AS $$
SELECT package, source, bibkey, description FROM (
  SELECT -- DISTINCT
         p.package        AS package,
         p.source         AS source,
         b.package        AS bpackage,
         b.value          AS bibkey,
         replace(p.description, E'\xc2\xa0', E'\\ ') AS description -- replace non-breaking spaces to TeX syntax
    FROM ( -- Make sure we have only one (package,source,description) record fitting the latest release with highest version
       SELECT package, source, description FROM
         (SELECT *, rank() OVER (PARTITION BY package ORDER BY rsort DESC, version DESC) FROM
           (SELECT DISTINCT package, source, description, sort as rsort, version FROM packages p
              JOIN releases r ON p.release = r. release
           ) tmp
         ) tmp WHERE rank = 1
    ) p
    JOIN (SELECT DISTINCT source, package, value FROM bibref WHERE key = 'bibtex') b ON b.source = p.source
 ) tmp
 WHERE package = bpackage OR bpackage = ''
 ORDER BY package, bibkey
;
$$;

COMMIT;

-- content of ftpnew.sql
-- http://ftp-master.debian.org/new.822

BEGIN;

DROP TABLE IF EXISTS new_sources CASCADE;
DROP TABLE IF EXISTS new_packages CASCADE;

DROP VIEW IF EXISTS new_sources_madison;
DROP VIEW IF EXISTS new_packages_madison;

-- Sources
CREATE TABLE new_sources (
       source text,
       version text,
       maintainer text,
       maintainer_name text,
       maintainer_email text,
       format text,
       files text,
       uploaders text,
       binaries text,             -- by parsing http://ftp-master.debian.org/new/<src>_<version>.html#dsc field "Binary:"
       changed_by text,           -- Uploader?
       architecture text,
       homepage text,             -- by parsing http://ftp-master.debian.org/new/<src>_<version>.html#dsc field "Homepage:"
       vcs_type text,             -- by parsing http://ftp-master.debian.org/new/<src>_<version>.html#dsc field "Vcs-*:"
       vcs_url text,              -- by parsing http://ftp-master.debian.org/new/<src>_<version>.html#dsc field "Vcs-*:"
       vcs_browser text,          -- by parsing http://ftp-master.debian.org/new/<src>_<version>.html#dsc field "Vcs-Browser:"
       section text,
       component text,
       distribution text,
       closes int,                -- WNPP bug #
       license text,              -- trying to parse http://ftp-master.debian.org/new/<bin1>_<version>.html#binary-<bin1>-copyright field "License:"
       last_modified timestamp,
       queue text,
    PRIMARY KEY (source, version, distribution)
);


-- Packages
CREATE TABLE new_packages (
       package text,
       version text,
       architecture text,
       maintainer text,
       description text,          -- by parsing http://ftp-master.debian.org/new/<bin>_<version>.html#control field "Description:"
       source text,
       depends text,
       recommends text,
       suggests text,
       enhances text,
       pre_depends text,
       breaks text,
       replaces text,
       provides text,
       conflicts text,
       installed_size integer,
       homepage text,
       long_description text,
       section text,
       component text,
       distribution text,
       license text,              -- trying to parse http://ftp-master.debian.org/new/<package>_<version>.html#binary-<package>-copyright field "License:"
    PRIMARY KEY (package, version, architecture)
);

GRANT SELECT ON new_packages TO PUBLIC;
GRANT SELECT ON new_sources TO PUBLIC;

-- These are required to avoid too much duplication in madison.cgi
CREATE VIEW new_sources_madison AS SELECT source, version, component,
distribution AS release, TEXT 'debian' AS distribution FROM new_sources;

CREATE VIEW new_packages_madison AS SELECT package, version, distribution AS
release, architecture, component, TEXT 'debian' AS distribution from
new_packages;

GRANT SELECT ON new_sources_madison TO PUBLIC;
GRANT SELECT ON new_packages_madison TO PUBLIC;

COMMIT;


-- content of blends-query-packages.sql
/************************************************************************************
 * Obtain all needed information of a package mentioned in a Blends task            *
 ************************************************************************************/

-- strip '+bX' for binary only uploads which is not interesting in the Blends scope
CREATE OR REPLACE FUNCTION strip_binary_upload(text) RETURNS debversion AS $$
       SELECT CAST(regexp_replace(regexp_replace($1, E'\\+b[0-9]+$', ''), E'^[0-9]+:', '') AS debversion) ;
$$  LANGUAGE 'SQL';

-- drop the function which did not query for enhances
DROP FUNCTION IF EXISTS blends_query_packages(text[]);
CREATE OR REPLACE FUNCTION blends_query_packages(text[],text[]) RETURNS SETOF RECORD AS $$
  SELECT DISTINCT
         p.package, p.distribution, p.release, p.component, p.version,
         p.maintainer,
         p.source, p.section, p.task, p.homepage,
         src.maintainer_name, src.maintainer_email,
         src.vcs_type, src.vcs_url, src.vcs_browser,
	 src.changed_by,
         enh.enhanced,
         rva.releases, versions, rva.architectures,
	 unstable_upstream, unstable_parsed_version, unstable_status, experimental_parsed_version, experimental_status,
	 pop.vote, pop.recent,
         tags.debtags,
         screenshot_versions, large_image_urls, small_image_urls,
         bibyear.value    AS "year",
         bibtitle.value   AS "title",
         bibauthor.value  AS "authors",
         bibdoi.value     AS "doi",
         bibpmid.value    AS "pubmed",
         biburl.value     AS "url",
         bibjournal.value AS "journal",
         bibvolume.value  AS "volume",
         bibnumber.value  AS "number",
         bibpages.value   AS "pages",
         bibeprint.value  AS "eprint",
         en.description AS description_en, en.long_description AS long_description_en,
         cs.description AS description_cs, cs.long_description AS long_description_cs,
         da.description AS description_da, da.long_description AS long_description_da,
         de.description AS description_de, de.long_description AS long_description_de,
         es.description AS description_es, es.long_description AS long_description_es,
         fi.description AS description_fi, fi.long_description AS long_description_fi,
         fr.description AS description_fr, fr.long_description AS long_description_fr,
         hu.description AS description_hu, hu.long_description AS long_description_hu,
         it.description AS description_it, it.long_description AS long_description_it,
         ja.description AS description_ja, ja.long_description AS long_description_ja,
         ko.description AS description_ko, ko.long_description AS long_description_ko,
         nl.description AS description_nl, nl.long_description AS long_description_nl,
         pl.description AS description_pl, pl.long_description AS long_description_pl,
         pt_BR.description AS description_pt_BR, pt_BR.long_description AS long_description_pt_BR,
         ru.description AS description_ru, ru.long_description AS long_description_ru,
         sk.description AS description_sk, sk.long_description AS long_description_sk,
         sr.description AS description_sr, sr.long_description AS long_description_sr,
         sv.description AS description_sv, sv.long_description AS long_description_sv,
         uk.description AS description_uk, uk.long_description AS long_description_uk,
         zh_CN.description AS description_zh_CN, zh_CN.long_description AS long_description_zh_CN,
         zh_TW.description AS description_zh_TW, zh_TW.long_description AS long_description_zh_TW
    FROM (
      SELECT DISTINCT 
             package, distribution, release, component, strip_binary_upload(version) AS version,
             maintainer, source, section, task, homepage, description, description_md5
        FROM packages
       WHERE package = ANY ($1)
    ) p
    --                                                                                                                                                                   ---+  Ensure we get no old stuff from non-free
    --                                                                                                                                                                      v  packages with different architectures
    LEFT OUTER JOIN descriptions en ON en.language = 'en' AND en.package = p.package AND en.release = p.release  AND en.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions cs ON cs.language = 'cs' AND cs.package = p.package AND cs.release = p.release  AND cs.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions da ON da.language = 'da' AND da.package = p.package AND da.release = p.release  AND da.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions de ON de.language = 'de' AND de.package = p.package AND de.release = p.release  AND de.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions es ON es.language = 'es' AND es.package = p.package AND es.release = p.release  AND es.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions fi ON fi.language = 'fi' AND fi.package = p.package AND fi.release = p.release  AND fi.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions fr ON fr.language = 'fr' AND fr.package = p.package AND fr.release = p.release  AND fr.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions hu ON hu.language = 'hu' AND hu.package = p.package AND hu.release = p.release  AND hu.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions it ON it.language = 'it' AND it.package = p.package AND it.release = p.release  AND it.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions ja ON ja.language = 'ja' AND ja.package = p.package AND ja.release = p.release  AND ja.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions ko ON ko.language = 'ko' AND ko.package = p.package AND ko.release = p.release  AND ko.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions nl ON nl.language = 'nl' AND nl.package = p.package AND nl.release = p.release  AND nl.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions pl ON pl.language = 'pl' AND pl.package = p.package AND pl.release = p.release  AND pl.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions pt_BR ON pt_BR.language = 'pt_BR' AND pt_BR.package = p.package AND pt_BR.release = p.release AND pt_BR.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions ru ON ru.language = 'ru' AND ru.package = p.package AND ru.release = p.release  AND ru.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions sk ON sk.language = 'sk' AND sk.package = p.package AND sk.release = p.release  AND sk.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions sr ON sr.language = 'sr' AND sr.package = p.package AND sr.release = p.release  AND sr.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions sv ON sv.language = 'sv' AND sv.package = p.package AND sv.release = p.release  AND sv.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions uk ON uk.language = 'uk' AND uk.package = p.package AND uk.release = p.release  AND uk.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions zh_CN ON zh_CN.language = 'zh_CN' AND zh_CN.package = p.package AND zh_CN.release = p.release AND zh_CN.description_md5 = p.description_md5
    LEFT OUTER JOIN descriptions zh_TW ON zh_TW.language = 'zh_TW' AND zh_TW.package = p.package AND zh_TW.release = p.release AND zh_TW.description_md5 = p.description_md5
    -- extract one single package with highest version and release
    JOIN (
      -- select packages which have versions outside experimental
      SELECT px.package, strip_binary_upload(px.version) AS version, (SELECT release FROM releases WHERE sort = MAX(rx.sort)) AS release
        FROM (
           -- select highest version which is not in experimental
           SELECT package, MAX(version) AS version FROM packages
            WHERE package = ANY ($1)
              AND release != 'experimental'
            GROUP BY package
        ) px
        JOIN (
           -- select the release in which this version is available
           SELECT DISTINCT package, version, release FROM packages
            WHERE package = ANY ($1)
        ) py ON px.package = py.package AND px.version = py.version
        JOIN releases rx ON py.release = rx.release
        GROUP BY px.package, px.version
      UNION
      -- find out which packages only exist in experimental and nowhere else
      SELECT DISTINCT package, strip_binary_upload(version) AS version, release
        FROM packages
       WHERE package = ANY ($1)
          -- ignore packages which have other releases than experimental
         AND package NOT IN (
             SELECT DISTINCT package FROM packages 
              WHERE package = ANY ($1)
                AND release != 'experimental'
             )
       ) pvar ON pvar.package = p.package AND pvar.version = p.version AND pvar.release = p.release
    -- obtain source_version of given package which is needed in cases where this is different form binary package version
    JOIN (
       SELECT DISTINCT package, source, strip_binary_upload(version) AS version,
                       strip_binary_upload(source_version) AS source_version, release,
                       maintainer_email
         FROM packages_summary WHERE package = ANY ($1)
    ) ps ON ps.package = p.package AND ps.release = p.release
    -- extract source and join with upload_history to find out latest uploader if different from Maintainer
    JOIN (
	SELECT DISTINCT s.source, strip_binary_upload(s.version) AS version,
               s.maintainer, s.release, s.maintainer_name, s.maintainer_email, s.vcs_type, s.vcs_url, s.vcs_browser,
               CASE WHEN uh.changed_by != s.maintainer THEN uh.changed_by ELSE NULL END AS changed_by
          FROM sources s
          LEFT OUTER JOIN upload_history uh ON s.source = uh.source AND s.version = uh.version
    ) src ON src.source = p.source AND src.source = ps.source
           AND src.release = p.release
           AND ( ( ps.version = p.version AND ps.version != ps.source_version ) OR
                 ( ps.version = p.version AND src.version = p.version) )
    -- join with sets of avialable versions in different releases
    JOIN (
      SELECT package, array_agg(release) AS releases,
             array_agg(CASE WHEN component = 'main' THEN version ELSE version || ' (' || component || ')' END) AS versions,
             array_agg(archs) AS architectures
          FROM (
     	    SELECT package, ptmp.release as release, strip_binary_upload(version) AS version, archs, component FROM
              ( SELECT package, release, version, array_to_string(array_sort(array_accum(architecture)),',') AS archs, component
                  FROM (
                    SELECT package,
                           release || CASE WHEN char_length(substring(distribution from '-.*')) > 0
                                        THEN substring(distribution from '-.*')
                                        ELSE '' END AS release,
                            -- make *-volatile a "pseudo-release"
                            strip_binary_upload(regexp_replace(version, '^[0-9]:', '')) AS version,
                            architecture,
                            component
                      FROM packages
	             WHERE package = ANY ($1)
                   ) AS prvac
		   GROUP BY package, version, release, component
              ) ptmp
	      JOIN releases ON releases.release = ptmp.release
              ORDER BY version, releases.sort
	    ) tmp GROUP BY package
         ) rva
         ON p.package = rva.package
    LEFT OUTER JOIN (
      SELECT DISTINCT
        source, unstable_upstream, unstable_parsed_version, unstable_status, experimental_parsed_version, experimental_status
        FROM dehs
        WHERE unstable_status = 'outdated'
    ) d ON p.source = d.source 
    LEFT OUTER JOIN popcon pop ON p.package = pop.package
    LEFT OUTER JOIN (
       SELECT package, array_agg(tag) AS debtags
         FROM debtags 
        WHERE tag NOT LIKE 'implemented-in::%'
	  AND tag NOT LIKE 'protocol::%'
          AND tag NOT LIKE '%::TODO'
          AND tag NOT LIKE '%not-yet-tagged%'
          GROUP BY package
    ) tags ON tags.package = p.package
    LEFT OUTER JOIN (
       SELECT package, 
              array_agg(version)  AS screenshot_versions,
              array_agg(large_image_url) AS large_image_urls,
              array_agg(small_image_url) AS small_image_urls 
         FROM screenshots 
         GROUP BY package
    ) sshots ON sshots.package = p.package
    -- check whether a package is enhanced by some other package
    LEFT OUTER JOIN (
      SELECT DISTINCT regexp_replace(package_version, E'\\s*\\(.*\\)', '') AS package, array_agg(enhanced_by) AS enhanced FROM (
        SELECT DISTINCT package AS enhanced_by, regexp_split_to_table(enhances, E',\\s*') AS package_version FROM packages
         WHERE enhances LIKE ANY( $2 )
      ) AS tmpenh GROUP BY package
    ) enh ON enh.package = p.package
    -- FIXME: To get reasonable querying of publications for specific packages and also multiple citations the table structure
    --        of the bibref table most probably needs to be changed to one entry per citation
    --        for the moment the specification of package is ignored because otherwise those citations would spoil the
    --        whole query
    --        example: if `bib*.package = ''` would be left out acedb-other would get more than 500 results !!!
    LEFT OUTER JOIN bibref bibyear    ON p.source = bibyear.source    AND bibyear.rank = 0    AND bibyear.key    = 'year'    AND bibyear.package = ''
    LEFT OUTER JOIN bibref bibtitle   ON p.source = bibtitle.source   AND bibtitle.rank = 0   AND bibtitle.key   = 'title'   AND bibtitle.package = ''
    LEFT OUTER JOIN bibref bibauthor  ON p.source = bibauthor.source  AND bibauthor.rank = 0  AND bibauthor.key  = 'author'  AND bibauthor.package = ''
    LEFT OUTER JOIN bibref bibdoi     ON p.source = bibdoi.source     AND bibdoi.rank = 0     AND bibdoi.key     = 'doi'     AND bibdoi.package = ''
    LEFT OUTER JOIN bibref bibpmid    ON p.source = bibpmid.source    AND bibpmid.rank = 0    AND bibpmid.key    = 'pmid'    AND bibpmid.package = ''
    LEFT OUTER JOIN bibref biburl     ON p.source = biburl.source     AND biburl.rank = 0     AND biburl.key     = 'url'     AND biburl.package = ''
    LEFT OUTER JOIN bibref bibjournal ON p.source = bibjournal.source AND bibjournal.rank = 0 AND bibjournal.key = 'journal' AND bibjournal.package = ''
    LEFT OUTER JOIN bibref bibvolume  ON p.source = bibvolume.source  AND bibvolume.rank = 0  AND bibvolume.key  = 'volume'  AND bibvolume.package = ''
    LEFT OUTER JOIN bibref bibnumber  ON p.source = bibnumber.source  AND bibnumber.rank = 0  AND bibnumber.key  = 'number'  AND bibnumber.package = ''
    LEFT OUTER JOIN bibref bibpages   ON p.source = bibpages.source   AND bibpages.rank = 0   AND bibpages.key   = 'pages'   AND bibpages.package = ''
    LEFT OUTER JOIN bibref bibeprint  ON p.source = bibeprint.source  AND bibeprint.rank = 0  AND bibeprint.key  = 'eprint'  AND bibeprint.package = ''
    ORDER BY p.package
 $$ LANGUAGE 'SQL';

-- drop the old unperformat function which returns a much larger set than needed
DROP FUNCTION IF EXISTS ddtp_unique(text);

-- Select unique DDTP translation for highest package version for a given language
-- ATTENTION: The execution of this query is quite slow and should be optimized
CREATE OR REPLACE FUNCTION ddtp_unique(text, text[]) RETURNS SETOF RECORD AS $$
  SELECT DISTINCT d.package, d.description, d.long_description FROM descriptions d
    JOIN (
      SELECT dr.package, (SELECT release FROM releases WHERE sort = MAX(r.sort)) AS release FROM descriptions dr
        JOIN releases r ON dr.release = r.release
        WHERE language = $1 AND dr.package = ANY ($2)
        GROUP BY dr.package
    -- sometimes there are different translations of the same package version in different releases
    -- because translators moved on working inbetween releases but we need to select only one of these
    -- (the last one)
    ) duvr ON duvr.package = d.package AND duvr.release = d.release
    WHERE language = $1 AND d.package = ANY ($2)
 $$ LANGUAGE 'SQL';

CREATE OR REPLACE FUNCTION blends_metapackage_translations (text[]) RETURNS SETOF RECORD AS $$
  SELECT
         p.package,
         p.description,     en.long_description_en,
         cs.description_cs, cs.long_description_cs,
         da.description_da, da.long_description_da,
         de.description_de, de.long_description_de,
         es.description_es, es.long_description_es,
         fi.description_fi, fi.long_description_fi,
         fr.description_fr, fr.long_description_fr,
         hu.description_hu, hu.long_description_hu,
         it.description_it, it.long_description_it,
         ja.description_ja, ja.long_description_ja,
         ko.description_ko, ko.long_description_ko,
         nl.description_nl, nl.long_description_nl,
         pl.description_pl, pl.long_description_pl,
         pt_BR.description_pt_BR, pt_BR.long_description_pt_BR,
         ru.description_ru, ru.long_description_ru,
         sk.description_sk, sk.long_description_sk,
         sr.description_sr, sr.long_description_sr,
         sv.description_sv, sv.long_description_sv,
         uk.description_uk, uk.long_description_uk,
         zh_CN.description_zh_CN, zh_CN.long_description_zh_CN,
         zh_TW.description_zh_TW, zh_TW.long_description_zh_TW
    FROM packages p
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('en', $1) AS (package text, description_en text, long_description_en text)) en ON en.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('cs', $1) AS (package text, description_cs text, long_description_cs text)) cs ON cs.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('da', $1) AS (package text, description_da text, long_description_da text)) da ON da.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('de', $1) AS (package text, description_de text, long_description_de text)) de ON de.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('es', $1) AS (package text, description_es text, long_description_es text)) es ON es.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('fi', $1) AS (package text, description_fi text, long_description_fi text)) fi ON fi.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('fr', $1) AS (package text, description_fr text, long_description_fr text)) fr ON fr.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('hu', $1) AS (package text, description_hu text, long_description_hu text)) hu ON hu.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('it', $1) AS (package text, description_it text, long_description_it text)) it ON it.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('ja', $1) AS (package text, description_ja text, long_description_ja text)) ja ON ja.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('ko', $1) AS (package text, description_ko text, long_description_ko text)) ko ON ko.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('nl', $1) AS (package text, description_nl text, long_description_nl text)) nl ON nl.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('pl', $1) AS (package text, description_pl text, long_description_pl text)) pl ON pl.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('pt_BR', $1) AS (package text, description_pt_BR text, long_description_pt_BR text)) pt_BR ON pt_BR.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('ru', $1) AS (package text, description_ru text, long_description_ru text)) ru ON ru.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('sk', $1) AS (package text, description_sk text, long_description_sk text)) sk ON sk.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('sr', $1) AS (package text, description_sr text, long_description_sr text)) sr ON sr.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('sv', $1) AS (package text, description_sv text, long_description_sv text)) sv ON sv.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('uk', $1) AS (package text, description_uk text, long_description_uk text)) uk ON uk.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('zh_CN', $1) AS (package text, description_zh_CN text, long_description_zh_CN text)) zh_CN ON zh_CN.package = p.package
    LEFT OUTER JOIN (SELECT * FROM ddtp_unique('zh_TW', $1) AS (package text, description_zh_TW text, long_description_zh_TW text)) zh_TW ON zh_TW.package = p.package
    WHERE p.package = ANY ($1)
 $$ LANGUAGE 'SQL';

-- 2012-07-06
CREATE INDEX ubuntu_bugs_tasks_package_idx on ubuntu_bugs_tasks(package);
CREATE INDEX upload_history_distribution_date_idx on upload_history(distribution, date);
