/************************************************************************************
 * Obtain all needed information of a package mentioned in a Blends task            *
 ************************************************************************************/

CREATE OR REPLACE FUNCTION blends_query_packages (text[]) RETURNS SETOF RECORD AS $$
  SELECT
         p.package, p.distribution, p.release, p.component, p.version,
         p.architecture, p.maintainer,
         p.source, p.section, task, p.homepage,
         src.maintainer_name, src.maintainer_email,
         src.vcs_type, src.vcs_url, src.vcs_browser,
         p.enhances,
         rva.releases, versions, rva.architectures,
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
         sv.description AS description_sv, sv.long_description AS long_description_sv,
         uk.description AS description_uk, uk.long_description AS long_description_uk,
         zh_CN.description AS description_zh_CN, zh_CN.long_description AS long_description_zh_CN,
         zh_TW.description AS description_zh_TW, zh_TW.long_description AS long_description_zh_TW
    FROM packages p
    LEFT OUTER JOIN ddtp cs ON cs.language = 'cs' AND cs.package = p.package AND cs.distribution = p.distribution AND cs.release = p.release AND cs.component = p.component
    LEFT OUTER JOIN ddtp da ON da.language = 'da' AND da.package = p.package AND da.distribution = p.distribution AND da.release = p.release AND da.component = p.component
    LEFT OUTER JOIN ddtp de ON de.language = 'de' AND de.package = p.package AND de.distribution = p.distribution AND de.release = p.release AND de.component = p.component
    LEFT OUTER JOIN ddtp es ON es.language = 'es' AND es.package = p.package AND es.distribution = p.distribution AND es.release = p.release AND es.component = p.component
    LEFT OUTER JOIN ddtp fi ON fi.language = 'fi' AND fi.package = p.package AND fi.distribution = p.distribution AND fi.release = p.release AND fi.component = p.component
    LEFT OUTER JOIN ddtp fr ON fr.language = 'fr' AND fr.package = p.package AND fr.distribution = p.distribution AND fr.release = p.release AND fr.component = p.component
    LEFT OUTER JOIN ddtp hu ON hu.language = 'hu' AND hu.package = p.package AND hu.distribution = p.distribution AND hu.release = p.release AND hu.component = p.component
    LEFT OUTER JOIN ddtp it ON it.language = 'it' AND it.package = p.package AND it.distribution = p.distribution AND it.release = p.release AND it.component = p.component
    LEFT OUTER JOIN ddtp ja ON ja.language = 'ja' AND ja.package = p.package AND ja.distribution = p.distribution AND ja.release = p.release AND ja.component = p.component
    LEFT OUTER JOIN ddtp ko ON ko.language = 'ko' AND ko.package = p.package AND ko.distribution = p.distribution AND ko.release = p.release AND ko.component = p.component
    LEFT OUTER JOIN ddtp nl ON nl.language = 'nl' AND nl.package = p.package AND nl.distribution = p.distribution AND nl.release = p.release AND nl.component = p.component
    LEFT OUTER JOIN ddtp pl ON pl.language = 'pl' AND pl.package = p.package AND pl.distribution = p.distribution AND pl.release = p.release AND pl.component = p.component
    LEFT OUTER JOIN ddtp pt_BR ON pt_BR.language = 'pt_BR' AND pt_BR.package = p.package AND pt_BR.distribution = p.distribution AND pt_BR.release = p.release AND pt_BR.component = p.component
    LEFT OUTER JOIN ddtp ru ON ru.language = 'ru' AND ru.package = p.package AND ru.distribution = p.distribution AND ru.release = p.release AND ru.component = p.component
    LEFT OUTER JOIN ddtp sk ON sk.language = 'sk' AND sk.package = p.package AND sk.distribution = p.distribution AND sk.release = p.release AND sk.component = p.component
    LEFT OUTER JOIN ddtp sv ON sv.language = 'sv' AND sv.package = p.package AND sv.distribution = p.distribution AND sv.release = p.release AND sv.component = p.component
    LEFT OUTER JOIN ddtp uk ON uk.language = 'uk' AND uk.package = p.package AND uk.distribution = p.distribution AND uk.release = p.release AND uk.component = p.component
    LEFT OUTER JOIN ddtp zh_CN ON zh_CN.language = 'zh_CN' AND zh_CN.package = p.package AND zh_CN.distribution = p.distribution AND zh_CN.release = p.release AND zh_CN.component = p.component
    LEFT OUTER JOIN ddtp zh_TW ON zh_TW.language = 'zh_TW' AND zh_TW.package = p.package AND zh_TW.distribution = p.distribution AND zh_TW.release = p.release AND zh_TW.component = p.component
    -- extract one single package with highes, version and release and any architecture
    JOIN (
       SELECT pkg.package, pkg.version, pkg.architecture, (SELECT release FROM releases WHERE sort = MAX(r.sort)) AS release
         FROM packages pkg
         JOIN (
          SELECT pv1.package, MIN(architecture) AS architecture, pv1.version
            FROM packages pv1
            JOIN (
                SELECT package, MAX(version) AS VERSION
                  FROM packages WHERE package = ANY ($1)
                  GROUP BY package
                ) mv ON pv1.version = mv.version AND pv1.package = mv.package
       	 WHERE pv1.package = ANY ($1)
                GROUP BY pv1.package, pv1.version
          ) sv1 ON pkg.version = sv1.version AND pkg.architecture = sv1.architecture
         JOIN releases r ON r.release = pkg.release
            WHERE pkg.package = ANY ($1)
         GROUP BY pkg.package, pkg.architecture, pkg.version
       ) pvar ON pvar.package = p.package AND pvar.version = p.version AND pvar.architecture = p.architecture AND pvar.release = p.release
    -- extract source
    JOIN sources src ON src.source = p.source AND src.version = p.version AND src.release = p.release
    -- join with sets of avialable versions in different releases
    JOIN (
      SELECT package, array_agg(release) AS releases,
             array_agg(CASE WHEN component = 'main' THEN version ELSE version || ' (' || component || ')' END) AS versions,
             array_agg(archs) AS architectures
          FROM (
     	    SELECT package, p.release as release, version, archs, component FROM
              ( SELECT package,
                   release || CASE WHEN char_length(substring(distribution from '-.*')) > 0
                                        THEN substring(distribution from '-.*')
                                        ELSE '' END AS release,
                            -- make *-volatile a "pseudo-release"
                        regexp_replace(version, '^[0-9]:', '') AS version,
                        array_to_string(array_sort(array_accum(architecture)),',') AS archs,
                        component
                    FROM packages
	           WHERE package = ANY ($1)
		   GROUP BY package, version, release, distribution, component
              ) p
	      JOIN releases ON releases.release = p.release
	    ) tmp GROUP BY package
         ) rva
         ON p.package = rva.package
    WHERE p.package = ANY ($1)
    ORDER BY p.package
 $$ LANGUAGE 'SQL';
