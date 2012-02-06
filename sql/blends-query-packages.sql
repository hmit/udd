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
         bibyear.value   AS "Published-Year",
         bibtitle.value  AS "Published-Title",
         bibauthor.value AS "Published-Authors",
         bibdoi.value    AS "Published-DOI",
         bibpmid.value   AS "Published-PubMed",
         p.description  AS description_en, p.long_description  AS long_description_en,
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
             maintainer, source, section, task, homepage, description, long_description, description_md5
        FROM packages
       WHERE package = ANY ($1)
    ) p
    --                                                                                                                                                                   ---+  Ensure we get no old stuff from non-free
    --                                                                                                                                                                      v  packages with different architectures
    LEFT OUTER JOIN ddtp cs ON cs.language = 'cs' AND cs.package = p.package AND cs.release = p.release  AND cs.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp da ON da.language = 'da' AND da.package = p.package AND da.release = p.release  AND da.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp de ON de.language = 'de' AND de.package = p.package AND de.release = p.release  AND de.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp es ON es.language = 'es' AND es.package = p.package AND es.release = p.release  AND es.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp fi ON fi.language = 'fi' AND fi.package = p.package AND fi.release = p.release  AND fi.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp fr ON fr.language = 'fr' AND fr.package = p.package AND fr.release = p.release  AND fr.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp hu ON hu.language = 'hu' AND hu.package = p.package AND hu.release = p.release  AND hu.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp it ON it.language = 'it' AND it.package = p.package AND it.release = p.release  AND it.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp ja ON ja.language = 'ja' AND ja.package = p.package AND ja.release = p.release  AND ja.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp ko ON ko.language = 'ko' AND ko.package = p.package AND ko.release = p.release  AND ko.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp nl ON nl.language = 'nl' AND nl.package = p.package AND nl.release = p.release  AND nl.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp pl ON pl.language = 'pl' AND pl.package = p.package AND pl.release = p.release  AND pl.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp pt_BR ON pt_BR.language = 'pt_BR' AND pt_BR.package = p.package AND pt_BR.release = p.release AND pt_BR.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp ru ON ru.language = 'ru' AND ru.package = p.package AND ru.release = p.release  AND ru.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp sk ON sk.language = 'sk' AND sk.package = p.package AND sk.release = p.release  AND sk.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp sr ON sr.language = 'sr' AND sr.package = p.package AND sr.release = p.release  AND sr.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp sv ON sv.language = 'sv' AND sv.package = p.package AND sv.release = p.release  AND sv.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp uk ON uk.language = 'uk' AND uk.package = p.package AND uk.release = p.release  AND uk.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp zh_CN ON zh_CN.language = 'zh_CN' AND zh_CN.package = p.package AND zh_CN.release = p.release AND zh_CN.description_md5 = p.description_md5
    LEFT OUTER JOIN ddtp zh_TW ON zh_TW.language = 'zh_TW' AND zh_TW.package = p.package AND zh_TW.release = p.release AND zh_TW.description_md5 = p.description_md5
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
    LEFT OUTER JOIN bibref bibyear   ON p.package = bibyear.package   AND bibyear.key   = 'Reference-Year'
    LEFT OUTER JOIN bibref bibtitle  ON p.package = bibtitle.package  AND bibtitle.key  = 'Reference-Title'
    LEFT OUTER JOIN bibref bibauthor ON p.package = bibauthor.package AND bibauthor.key = 'Reference-Author'
    LEFT OUTER JOIN bibref bibdoi    ON p.package = bibdoi.package    AND bibdoi.key    = 'DOI'
    LEFT OUTER JOIN bibref bibpmid   ON p.package = bibpmid.package   AND bibpmid.key   = 'PMID'
    ORDER BY p.package
 $$ LANGUAGE 'SQL';

-- drop the old unperformat function which returns a much larger set than needed
DROP FUNCTION IF EXISTS ddtp_unique(text);

-- Select unique DDTP translation for highest package version for a given language
-- ATTENTION: The execution of this query is quite slow and should be optimized
CREATE OR REPLACE FUNCTION ddtp_unique(text, text[]) RETURNS SETOF RECORD AS $$
  SELECT DISTINCT d.package, d.description, d.long_description FROM ddtp d
    JOIN (
      SELECT dr.package, (SELECT release FROM releases WHERE sort = MAX(r.sort)) AS release FROM ddtp dr
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
