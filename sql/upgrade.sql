-- 2008-09-22: Change severity from text to bugs_severity enum:
CREATE TYPE bugs_severity AS ENUM ('fixed', 'wishlist', 'minor', 'normal', 'important', 'serious', 'grave', 'critical');
ALTER TABLE bugs add severity2 bugs_severity;
UPDATE bugs set severity2 = severity::bugs_severity;
ALTER TABLE bugs drop severity;
ALTER TABLE bugs rename severity2 to severity;
ALTER TABLE archived_bugs add severity2 bugs_severity;
UPDATE archived_bugs set severity2 = severity::bugs_severity;
ALTER TABLE archived_bugs drop severity;
ALTER TABLE archived_bugs rename severity2 to severity;

-- 2008-09-22: Add a affects_experimental to bugs and archived_bugs
ALTER TABLE bugs add affects_experimental boolean;
ALTER TABLE archived_bugs add affects_experimental boolean;

-- 2008-09-22: Properly name affects_stable and affects_unstable
ALTER TABLE archived_bugs rename affects_sarchived_table to affects_stable;
ALTER TABLE archived_bugs rename affects_unsarchived_table to affects_unstable;
-- 2008-09-26: add maintainer_name and maintainer_email to sources.
ALTER TABLE sources add maintainer_name text;
ALTER TABLE sources add maintainer_email text;
ALTER TABLE ubuntu_sources add maintainer_name text;
ALTER TABLE ubuntu_sources add maintainer_email text;
-- 2008-10-05: add fingerprint column in upload_history
ALTER TABLE upload_history add fingerprint text;
-- 2008-12-19: add breaks column in packages
ALTER TABLE packages add breaks text;
ALTER TABLE ubuntu_packages add breaks text;
-- 2009-01-07: add long_description column
ALTER TABLE packages add long_description text;
ALTER TABLE ubuntu_packages add long_description text;
CREATE VIEW all_sources AS
SELECT * FROM sources
UNION ALL SELECT * FROM ubuntu_sources;
CREATE VIEW all_packages AS
SELECT * FROM packages
UNION ALL SELECT * FROM ubuntu_packages;
GRANT SELECT ON all_sources TO PUBLIC;
GRANT SELECT ON all_packages TO PUBLIC;

CREATE TABLE all_packages_distrelcomparch (distribution text, release text,
component text, architecture text);
GRANT SELECT ON all_packages_distrelcomparch TO PUBLIC;

-- 2009-01-10
CREATE INDEX debtags_package_idx ON debtags(package);

-- 2009-01-26
ALTER TABLE bugs ADD forwarded text;
ALTER TABLE archived_bugs ADD forwarded text;

-- 2009-02-04
ALTER TABLE bugs ADD done text;
ALTER TABLE archived_bugs ADD done text;
CREATE VIEW all_bugs AS
SELECT * FROM bugs
UNION ALL SELECT * FROM archived_bugs;
GRANT SELECT ON all_bugs TO PUBLIC;

-- 2009-03-08
ALTER TABLE sources ALTER COLUMN version TYPE debversion;
ALTER TABLE ubuntu_sources ALTER COLUMN version TYPE debversion;
ALTER TABLE packages_summary ALTER COLUMN version TYPE debversion;
ALTER TABLE packages_summary ALTER COLUMN source_version TYPE debversion;
ALTER TABLE packages ALTER COLUMN version TYPE debversion;
ALTER TABLE packages ALTER COLUMN source_version TYPE debversion;
ALTER TABLE ubuntu_packages ALTER COLUMN version TYPE debversion;
ALTER TABLE ubuntu_packages ALTER COLUMN source_version TYPE debversion;
ALTER TABLE ubuntu_packages_summary ALTER COLUMN version TYPE debversion;
ALTER TABLE ubuntu_packages_summary ALTER COLUMN source_version TYPE debversion;
ALTER TABLE uploaders ALTER COLUMN version TYPE debversion;
ALTER TABLE ubuntu_uploaders ALTER COLUMN version TYPE debversion;
ALTER TABLE migrations ALTER COLUMN testing_version TYPE debversion;
ALTER TABLE migrations ALTER COLUMN unstable_version TYPE debversion;
ALTER TABLE migrations ALTER COLUMN sync_version TYPE debversion;
ALTER TABLE upload_history ALTER COLUMN version TYPE debversion;
-- 2009-03-18
CREATE TABLE ddtp (
       package      text,
       distribution text,
       release      text,
       component    text,   -- == 'main' for the moment
       version      text,   -- different versions for a package might exist because some archs
                            -- might have problems with newer versions if a new version comes
                            -- with a new description we might have different translations for
                            -- a (package, distribution, release, component, language) key so
                            -- we also need to store the version number of a package translation
                            -- In case there are different versions with an identical description
                            -- this field will hold the highest version number according to
                            -- dpkg --compare-versions
       language     text,
       description  text,
       long_description text,
       md5sum       text,   -- md5 sum of the original English description as it is used
                            -- in DDTP.  This is obtained via
                            --   md5(description || E'\n' || long_description || E'\n')
                            -- from packages table
    PRIMARY KEY (package, distribution, release, component, version, language)
);

GRANT SELECT ON ddtp TO PUBLIC;
ALTER TABLE ddtp ALTER COLUMN version TYPE debversion;

--- 2009-06-19
DROP DOMAIN lintian_tag_type;
CREATE DOMAIN lintian_tag_type AS TEXT
NOT NULL
CHECK(
     VALUE = 'error'
  OR VALUE = 'warning'
  OR VALUE = 'information'
  OR VALUE = 'experimental'
  OR VALUE = 'overriden'
  OR VALUE = 'pedantic'
);

-- 2009-06-24
CREATE INDEX ubuntu_bugs_tags_idx on ubuntu_bugs_tags(bug);
CREATE INDEX ubuntu_bugs_tasks_idx on ubuntu_bugs_tasks(bug);
CREATE INDEX ubuntu_bugs_duplicates_idx on ubuntu_bugs_duplicates(bug);
CREATE INDEX ubuntu_bugs_subscribers_idx on ubuntu_bugs_subscribers(bug);

-- 2009-07-16
-- turn release columns into ENUMs
-- you probably want to drop and re-create the tables here, altering
-- them won't work well
CREATE TYPE release AS ENUM ('hardy', 'intrepid', 'jaunty', 'karmic', 'etch', 'etch-security', 'etch-proposed-updates', 'lenny', 'lenny-security', 'lenny-proposed-updates', 'squeeze', 'squeeze-security', 'squeeze-proposed-updates', 'sid', 'experimental');
ALTER TABLE packages ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE sources ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE packages_summary ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE uploaders ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ubuntu_packages ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ubuntu_sources ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ubuntu_packages_summary ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ubuntu_uploaders ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ddtp ALTER COLUMN release TYPE release USING release::release;
-- replace all_packages_distrelcomparch with two tables and a view
DROP TABLE all_packages_distrelcomparch;
CREATE TABLE packages_distrelcomparch (distribution text, release release,
component text, architecture text);
CREATE TABLE ubuntu_packages_distrelcomparch (distribution text, release release,
component text, architecture text);
GRANT SELECT ON ubuntu_packages_distrelcomparch TO PUBLIC;
GRANT SELECT ON packages_distrelcomparch TO PUBLIC;
CREATE VIEW all_packages_distrelcomparch AS
SELECT * FROM packages_distrelcomparch
UNION ALL SELECT * FROM ubuntu_packages_distrelcomparch;
GRANT SELECT ON all_packages_distrelcomparch TO PUBLIC;
-- turn lintian tag_type to enum
CREATE TYPE lintian_tagtype AS ENUM('experimental', 'overriden', 'pedantic', 'information', 'warning', 'error');
ALTER TABLE lintian ALTER COLUMN tag_type TYPE lintian_tagtype USING tag_type::lintian_tagtype;
-- add indices needed for enrico's work
CREATE INDEX uploaders_distrelcompsrcver_idx on uploaders(distribution, release, component, source, version);
CREATE INDEX ubuntu_uploaders_distrelcompsrcver_idx on ubuntu_uploaders(distribution, release, component, source, version);
CREATE INDEX packages_summary_distrelcompsrcver_idx on packages_summary(distribution, release, component, source, source_version);
CREATE INDEX ubuntu_packages_summary_distrelcompsrcver_idx on ubuntu_packages_summary(distribution, release, component, source, source_version);

-- 2009-07-17
ALTER TABLE uploaders add uploader text;
ALTER TABLE ubuntu_uploaders add uploader text;
ALTER TABLE packages ADD maintainer_name text;
ALTER TABLE packages ADD maintainer_email text;
ALTER TABLE packages_summary ADD maintainer_name text;
ALTER TABLE packages_summary ADD maintainer_email text;
ALTER TABLE ubuntu_packages ADD maintainer_name text;
ALTER TABLE ubuntu_packages ADD maintainer_email text;
ALTER TABLE ubuntu_packages_summary ADD maintainer_name text;
ALTER TABLE ubuntu_packages_summary ADD maintainer_email text;

ALTER TABLE upload_history ADD changed_by_name text;
ALTER TABLE upload_history ADD changed_by_email text;
ALTER TABLE upload_history ADD maintainer_name text;
ALTER TABLE upload_history ADD maintainer_email text;
ALTER TABLE upload_history ADD signed_by_name text;
ALTER TABLE upload_history ADD signed_by_email text;

-- 2009-07-23
-- active_dds view
CREATE VIEW active_dds AS
SELECT DISTINCT carnivore_login.id, login
FROM carnivore_login, carnivore_keys
WHERE carnivore_keys.id = carnivore_login.id
AND key_type = 'keyring';

GRANT SELECT ON active_dds TO PUBLIC;

-- 2009-07-24
ALTER TABLE lintian ADD information text;

-- DEHS
CREATE TYPE dehs_status AS ENUM('error', 'uptodate', 'outdated');
CREATE TABLE dehs (
  source TEXT NOT NULL,
  unstable_version debversion,
  unstable_upstream text,
  unstable_parsed_version text,
  unstable_status dehs_status,
  experimental_version debversion,
  experimental_upstream text,
  experimental_parsed_version text,
  experimental_status dehs_status,
  PRIMARY KEY (source)
);
GRANT SELECT ON dehs TO PUBLIC;

-- split emails in bugs
ALTER TABLE bugs add submitter_name TEXT;
ALTER TABLE bugs add submitter_email TEXT;
ALTER TABLE bugs add owner_name TEXT;
ALTER TABLE bugs add owner_email TEXT;
ALTER TABLE bugs add done_name TEXT;
ALTER TABLE bugs add done_email TEXT;
ALTER TABLE archived_bugs add submitter_name TEXT;
ALTER TABLE archived_bugs add submitter_email TEXT;
ALTER TABLE archived_bugs add owner_name TEXT;
ALTER TABLE archived_bugs add owner_email TEXT;
ALTER TABLE archived_bugs add done_name TEXT;
ALTER TABLE archived_bugs add done_email TEXT;

-- LDAP
CREATE TABLE ldap ( uid numeric, login text, cn text, sn text, expire boolean, location text, country text, activity_from timestamp with time zone, activity_from_info text, activity_pgp timestamp with time zone, activity_pgp_info text, gecos text, birthdate date, gender numeric, PRIMARY KEY (uid));
GRANT SELECT ON ldap TO guestdd;

-- New layout for upload_history
DROP TABLE upload_history CASCADE;
CREATE TABLE upload_history
 (source text, version debversion, date timestamp with time zone,
 changed_by text, changed_by_name text, changed_by_email text, maintainer text, maintainer_name text, maintainer_email text, nmu boolean, signed_by text, signed_by_name text, signed_by_email text, key_id text,
 fingerprint text,
 PRIMARY KEY (source, version));

CREATE TABLE upload_history_architecture
 (source text, version debversion, architecture text,
 PRIMARY KEY (source, version, architecture),
FOREIGN KEY (source, version) REFERENCES upload_history DEFERRABLE);
  
CREATE TABLE upload_history_closes
 (source text, version debversion, bug int,
 PRIMARY KEY (source, version, bug),
FOREIGN KEY (source, version) REFERENCES upload_history DEFERRABLE);

GRANT SELECT ON upload_history TO PUBLIC;
GRANT SELECT ON upload_history_architecture TO PUBLIC;
GRANT SELECT ON upload_history_closes TO PUBLIC;

CREATE VIEW upload_history_nmus AS
select uh1.source, count(*) AS nmus
from upload_history uh1, (select source, max(date) as date from upload_history where nmu = false group by source) uh2
where uh1.nmu = true
and uh1.source = uh2.source
and uh1.date > uh2.date
group by uh1.source;
GRANT SELECT ON upload_history_nmus TO PUBLIC;

ALTER TABLE dehs ADD unstable_last_uptodate timestamp;
ALTER TABLE dehs ADD experimental_last_uptodate timestamp;

-- 2009-10-07
ALTER TABLE sources DROP dm_upload_allowed;
ALTER TABLE sources ADD dm_upload_allowed boolean;
ALTER TABLE ubuntu_sources DROP dm_upload_allowed;
ALTER TABLE ubuntu_sources ADD dm_upload_allowed boolean;

-- 2009-11-04 lucid released
ALTER TABLE packages ALTER COLUMN release TYPE text USING release::text;
ALTER TABLE sources ALTER COLUMN release TYPE text USING release::text;
ALTER TABLE packages_summary ALTER COLUMN release TYPE text USING release::text;
ALTER TABLE uploaders ALTER COLUMN release TYPE text USING release::text;
ALTER TABLE ubuntu_packages ALTER COLUMN release TYPE text USING release::text;
ALTER TABLE ubuntu_sources ALTER COLUMN release TYPE text USING release::text;
ALTER TABLE ubuntu_packages_summary ALTER COLUMN release TYPE text USING release::text;
ALTER TABLE ubuntu_uploaders ALTER COLUMN release TYPE text USING release::text;
ALTER TABLE ddtp ALTER COLUMN release TYPE text USING release::text;
ALTER TABLE packages_distrelcomparch ALTER COLUMN release TYPE text USING release::text;
ALTER TABLE ubuntu_packages_distrelcomparch ALTER COLUMN release TYPE text USING release::text;
DROP TYPE release;
CREATE TYPE release AS ENUM ('hardy', 'intrepid', 'jaunty', 'karmic', 'lucid', 'etch', 'etch-security', 'etch-proposed-updates', 'lenny', 'lenny-security', 'lenny-proposed-updates', 'squeeze', 'squeeze-security', 'squeeze-proposed-updates', 'sid', 'experimental');
ALTER TABLE packages ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE sources ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE packages_summary ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE uploaders ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ubuntu_packages ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ubuntu_sources ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ubuntu_packages_summary ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ubuntu_uploaders ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ddtp ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE packages_distrelcomparch ALTER COLUMN release TYPE release USING release::release;
ALTER TABLE ubuntu_packages_distrelcomparch ALTER COLUMN release TYPE release USING release::release;

CREATE TABLE bugs_blocks
  (id int REFERENCES bugs, blocked int,
PRIMARY KEY(id, blocked));

CREATE TABLE bugs_blockedby
  (id int REFERENCES bugs, blocker int,
PRIMARY KEY(id, blocker));

CREATE TABLE archived_bugs_blocks
  (id int REFERENCES archived_bugs, blocked int,
PRIMARY KEY(id, blocked));

CREATE TABLE archived_bugs_blockedby
  (id int REFERENCES archived_bugs, blocker int,
PRIMARY KEY(id, blocker));


GRANT SELECT ON bugs_blocks TO PUBLIC;
GRANT SELECT ON bugs_blockedby TO PUBLIC;

GRANT SELECT ON archived_bugs_blocks TO PUBLIC;
GRANT SELECT ON archived_bugs_blockedby TO PUBLIC;

-- 2010-02-28
-- PTS
CREATE TABLE pts (
  source text,
  email text,
  PRIMARY KEY(source, email)
);
GRANT SELECT ON pts TO guestdd;

-- 2010-09-20
-- upload_history rewrite
ALTER TABLE upload_history ADD distribution text;
ALTER TABLE upload_history ADD file text;
ALTER TABLE upload_history_architecture ADD file text;
ALTER TABLE upload_history_closes ADD file text;

-- 2010-09-25
CREATE INDEX sources_release_idx ON sources(release);
CREATE INDEX bugs_tags_tag_idx ON bugs_tags(tag);

-- 2011-02-08
ALTER TABLE bugs add affects_oldstable boolean;
ALTER TABLE archived_bugs add affects_oldstable boolean;

-- 2011-04-09
ALTER TABLE sources add ruby_versions text;
ALTER TABLE packages add ruby_versions text;
ALTER TABLE ubuntu_sources add ruby_versions text;
ALTER TABLE ubuntu_packages add ruby_versions text;
ALTER TABLE derivatives_sources add ruby_versions text;
ALTER TABLE derivatives_packages add ruby_versions text;
-- 2011-05-31
ALTER TABLE bugs add done_date timestamp;
ALTER TABLE archived_bugs add done_date timestamp;

-- 2012-01-23
-- description-less packages files
ALTER TABLE packages add description_md5 text;
ALTER TABLE ubuntu_packages add description_md5 text;
ALTER TABLE derivatives_packages add description_md5 text;
