-- content of releases.sql
/****************************************************************************************
 * This table enables sorting of releases according to their release date.  To define   *
 * a reasonable order also for releases which are not or never will be released an      *
 * additional column sort is defined.                                                   *
 * The relevant discussion can be found here:                                           *
 *   http://lists.debian.org/debian-qa/2010/02/msg00001.html                            *
 ****************************************************************************************/

DROP TABLE IF EXISTS releases;

CREATE TABLE releases (
       release        text,  /* keep name column as in other tables */
       releasedate    date,
       role           text,
       releaseversion text,
       distribution   text,
       sort           int,
       PRIMARY KEY (release)
);

INSERT INTO releases VALUES ( 'etch',                     '2007-04-08', '',             '4.0', 'debian',    400 );
INSERT INTO releases VALUES ( 'etch-security',            '2007-04-08', '',             '4.0', 'debian',    401 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'etch-proposed-updates',    '2007-04-08', '',             '4.0', 'debian',    402 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'lenny',                    '2009-02-14', '',             '5.0', 'debian',    500 );
INSERT INTO releases VALUES ( 'lenny-security',           '2009-02-14', '',             '5.0', 'debian',    501 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'lenny-proposed-updates',   '2009-02-14', '',             '5.0', 'debian',    502 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'squeeze',                  '2011-02-06', 'oldstable',    '6.0', 'debian',    600 );
INSERT INTO releases VALUES ( 'squeeze-security',         '2011-02-06', '',             '6.0', 'debian',    601 );
INSERT INTO releases VALUES ( 'squeeze-proposed-updates', '2011-02-06', '',             '6.0', 'debian',    602 );
INSERT INTO releases VALUES ( 'wheezy',                   '2013-05-05', 'stable',       '7.0', 'debian',    700 );
INSERT INTO releases VALUES ( 'wheezy-security',          '2013-05-05', '',             '7.0', 'debian',    701 );
INSERT INTO releases VALUES ( 'wheezy-proposed-updates',  '2013-05-05', '',             '7.0', 'debian',    702 );
INSERT INTO releases VALUES ( 'jessie',                   NULL,         'testing',      '',    'debian',    800 );
INSERT INTO releases VALUES ( 'jessie-security',          NULL,         '',             '',    'debian',    801 );
INSERT INTO releases VALUES ( 'jessie-proposed-updates',  NULL,         '',             '',    'debian',    802 );
INSERT INTO releases VALUES ( 'sid',                      NULL,         'unstable',     '',    'debian', 100000 );
INSERT INTO releases VALUES ( 'experimental',             NULL,         'experimental', '',    'debian',      0 ); /* this pseudo releases does not fit any order and it is not higher than unstable */

GRANT SELECT ON releases TO PUBLIC ;

-- 2012-07-06
CREATE INDEX ubuntu_bugs_tasks_package_idx on ubuntu_bugs_tasks(package);
CREATE INDEX upload_history_distribution_date_idx on upload_history(distribution, date);

-- 2012-08-14
CREATE INDEX upload_history_fingerprint_idx on upload_history(fingerprint);

-- 2013-03-23
CREATE TABLE bugs_stamps (
    id integer NOT NULL,
	update_requested bigint,
	db_updated bigint
);

ALTER TABLE ONLY bugs_stamps
    ADD CONSTRAINT bugs_stamps_pkey PRIMARY KEY (id);

CREATE TABLE archived_bugs_stamps (
    id integer NOT NULL,
	update_requested bigint,
	db_updated bigint
);

ALTER TABLE ONLY archived_bugs_stamps
    ADD CONSTRAINT archived_bugs_stamps_pkey PRIMARY KEY (id);

-- 2013-03-30
ALTER TABLE bugs ADD COLUMN affected_packages text;
ALTER TABLE bugs ADD COLUMN affected_sources text;
ALTER TABLE archived_bugs ADD COLUMN affected_packages text;
ALTER TABLE archived_bugs ADD COLUMN affected_sources text;

-- 2013-03-31

CREATE TYPE ftp_autoreject_type AS ENUM('lintian');
CREATE TYPE ftp_autoreject_level AS ENUM('fatal','nonfatal');
CREATE TABLE ftp_autorejects (
tag TEXT,
autoreject_type ftp_autoreject_type,
autoreject_level ftp_autoreject_level,
PRIMARY KEY(tag)
);

GRANT SELECT ON ftp_autorejects TO PUBLIC;

-- 2013-03-31
ALTER TABLE sources ADD COLUMN testsuite text;
ALTER TABLE sources ADD COLUMN autobuild text;
ALTER TABLE sources ADD COLUMN extra_source_only boolean;
ALTER TABLE packages ADD COLUMN multi_arch text;

ALTER TABLE ubuntu_sources ADD COLUMN testsuite text;
ALTER TABLE ubuntu_sources ADD COLUMN autobuild text;
ALTER TABLE ubuntu_sources ADD COLUMN extra_source_only boolean;
ALTER TABLE ubuntu_packages ADD COLUMN multi_arch text;

ALTER TABLE derivatives_sources ADD COLUMN testsuite text;
ALTER TABLE derivatives_sources ADD COLUMN autobuild text;
ALTER TABLE derivatives_sources ADD COLUMN extra_source_only boolean;
ALTER TABLE derivatives_packages ADD COLUMN multi_arch text;

-- 2013-03-31 archived releases
CREATE TABLE archived_sources
  (source text, version debversion, maintainer text,
    maintainer_name text, maintainer_email text, format text, files text,
    uploaders text, bin text, architecture text, standards_version text,
    homepage text, build_depends text, build_depends_indep text,
    build_conflicts text, build_conflicts_indep text, priority text, section
    text, distribution text, release text, component text, vcs_type text,
    vcs_url text, vcs_browser text,
    python_version text, ruby_versions text, checksums_sha1 text, checksums_sha256 text,
    original_maintainer text, dm_upload_allowed boolean,
    testsuite text, autobuild text, extra_source_only text,
    PRIMARY KEY (source, version, distribution, release, component));

CREATE INDEX archived_sources_distrelcomp_idx on archived_sources(distribution, release, component);

-- no primary key possible: duplicate rows are possible because duplicate entries
-- in Uploaders: are allowed. yes.
CREATE TABLE archived_uploaders (source text, version debversion, distribution text,
	release text, component text, uploader text, name text, email text);
   
GRANT SELECT ON archived_uploaders TO PUBLIC;

CREATE INDEX archived_uploaders_distrelcompsrcver_idx on archived_uploaders(distribution, release, component, source, version);

CREATE TABLE archived_packages_summary ( package text, version debversion, source text,
source_version debversion, maintainer text, maintainer_name text, maintainer_email text, distribution text, release text,
component text,
PRIMARY KEY (package, version, distribution, release, component));

CREATE INDEX archived_packages_summary_distrelcompsrcver_idx on archived_packages_summary(distribution, release, component, source, source_version);

CREATE TABLE archived_packages_distrelcomparch (distribution text, release text,
component text, architecture text);

CREATE TABLE archived_packages
  (package text, version debversion, architecture text, maintainer text, maintainer_name text, maintainer_email text, description
    text, description_md5 text, source text, source_version debversion, essential text, depends text,
    recommends text, suggests text, enhances text, pre_depends text, breaks text,
    installed_size int, homepage text, size int,
    build_essential text, origin text, sha1 text, replaces text, section text,
    md5sum text, bugs text, priority text, tag text, task text, python_version text,
    ruby_versions text, multi_arch text,
    provides text, conflicts text, sha256 text, original_maintainer text,
    distribution text, release text, component text,
  PRIMARY KEY (package, version, architecture, distribution, release, component),
  FOREIGN KEY (package, version, distribution, release, component) REFERENCES archived_packages_summary DEFERRABLE);

GRANT SELECT ON archived_sources TO PUBLIC;
GRANT SELECT ON archived_packages TO PUBLIC;
GRANT SELECT ON archived_packages_summary TO PUBLIC;
GRANT SELECT ON archived_packages_distrelcomparch TO PUBLIC;

CREATE INDEX archived_packages_source_idx on archived_packages(source);
CREATE INDEX archived_packages_distrelcomp_idx on archived_packages(distribution, release, component);

CREATE TABLE archived_descriptions (
    package          text not null,
    distribution     text not null,
    release          text not null,
    component        text not null,
    language         text not null,
    description      text not null,
    long_description text not null,
    description_md5  text not null, -- md5 sum of the original English description
    PRIMARY KEY (package, distribution, release, component, language, description, description_md5)
);
GRANT SELECT ON archived_descriptions TO PUBLIC;

-- 2013-03-31

CREATE TABLE pseudo_packages (
package TEXT,
maintainer TEXT,
maintainer_name TEXT,
maintainer_email TEXT,
description TEXT,
PRIMARY KEY(package)
);

GRANT SELECT ON pseudo_packages TO PUBLIC;

-- 2013-04-01

CREATE TABLE debian_maintainers (
maintainer TEXT,
maintainer_name TEXT,
maintainer_email TEXT,
fingerprint TEXT,
package TEXT,
granted_by_fingerprint TEXT
);

GRANT SELECT ON debian_maintainers TO PUBLIC;

-- wnpp view
CREATE VIEW wnpp AS
SELECT id, SUBSTRING(title from '^([A-Z]{1,3}): .*') as type, SUBSTRING(title from '^[A-Z]{1,3}: ([^ ]+)(?: -- .*)') as source, title FROM bugs WHERE package='wnpp' AND status!='done';

GRANT SELECT ON wnpp TO PUBLIC;

-- 2013-05-05 wheezy release

DROP VIEW bugs_rt_affects_oldstable;

CREATE VIEW bugs_rt_affects_oldstable AS
SELECT id, package, source FROM bugs
WHERE affects_oldstable
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'lenny', 'wheezy', 'jessie', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'squeeze'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'squeeze-ignore')
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='squeeze')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='squeeze'));


DROP VIEW bugs_rt_affects_stable;

CREATE VIEW bugs_rt_affects_stable AS
SELECT id, package, source FROM bugs
WHERE affects_stable
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'lenny', 'squeeze', 'jessie', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'wheezy'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'wheezy-ignore')
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='wheezy')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='wheezy'));


DROP VIEW bugs_rt_affects_testing;

CREATE VIEW bugs_rt_affects_testing AS
SELECT id, package, source FROM bugs
WHERE affects_testing 
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'lenny', 'squeeze', 'wheezy', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'jessie'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'jessie-ignore')
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='jessie')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='jessie'));


DROP VIEW bugs_rt_affects_unstable;

CREATE VIEW bugs_rt_affects_unstable AS
SELECT id, package, source FROM bugs
WHERE affects_unstable 
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('lenny', 'sarge', 'etch', 'squeeze', 'wheezy', 'jessie', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'sid'))
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='sid')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='sid'));


DROP VIEW bugs_rt_affects_testing_and_unstable;

CREATE VIEW bugs_rt_affects_testing_and_unstable AS
SELECT id, package, source FROM bugs
WHERE affects_unstable AND affects_testing
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sarge', 'etch', 'lenny', 'squeeze', 'wheezy', 'experimental'))
OR (id IN (SELECT id FROM bugs_tags WHERE tag = 'sid') AND id IN (SELECT id FROM bugs_tags WHERE tag = 'jessie')))
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='jessie')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='jessie'))
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='sid')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='sid'));

GRANT SELECT ON bugs_rt_affects_oldstable TO PUBLIC;
GRANT SELECT ON bugs_rt_affects_stable TO PUBLIC;
GRANT SELECT ON bugs_rt_affects_testing_and_unstable TO PUBLIC;
GRANT SELECT ON bugs_rt_affects_unstable TO PUBLIC;
GRANT SELECT ON bugs_rt_affects_testing TO PUBLIC;

-- 2013-08-25 bugs closed by packages in ftpnew
-- (and potentially other sources like mentors)
CREATE TABLE potential_bug_closures
  (id int,
   source text,
   distribution text,
   origin text
   );

GRANT SELECT ON potential_bug_closures TO PUBLIC;

CREATE INDEX potential_bug_closures_id_idx ON potential_bug_closures (id);
CREATE INDEX potential_bug_closures_source_idx ON potential_bug_closures (source);

-- 2013-08-27 piuparts_status

CREATE TABLE piuparts_status
  (section text,
   source text,
   version text,
   status text
   );

GRANT SELECT ON piuparts_status TO PUBLIC;

CREATE INDEX piuparts_status_section_idx ON piuparts_status (section);
CREATE INDEX piuparts_status_source_idx ON piuparts_status (source);
CREATE INDEX piuparts_status_status_idx ON piuparts_status (status);

-- 2013-08-29 testing autoremovals

CREATE TABLE testing_autoremovals
  (source text,
   version text,
   bugs text,
   first_seen bigint,
   last_checked bigint
   );

GRANT SELECT ON testing_autoremovals TO PUBLIC;

CREATE INDEX testing_autoremovals_source_idx ON testing_autoremovals (source);

-- 2013-10-05 reason for key packages

ALTER TABLE key_packages ADD COLUMN reason text;

-- 2013-10-06 these tables were not public

GRANT SELECT ON bugs_stamps TO PUBLIC;
GRANT SELECT ON archived_bugs_stamps TO PUBLIC;

