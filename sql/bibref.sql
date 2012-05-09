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
            CASE WHEN bibpages.value   IS NOT NULL THEN E',\n  Pages   = {' || regexp_replace(bibpages.value, '(\d)-(\d)', '\1--\2')   || '}' ELSE '' END ||
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
