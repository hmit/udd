-- Sources and Packages
CREATE TYPE release AS ENUM ('hardy', 'intrepid', 'jaunty', 'karmic', 'etch', 'etch-security', 'etch-proposed-updates', 'lenny', 'lenny-security', 'lenny-proposed-updates', 'squeeze', 'squeeze-security', 'squeeze-proposed-updates', 'sid', 'experimental');
CREATE TABLE sources
  (source text, version debversion, maintainer text,
    maintainer_name text, maintainer_email text, format text, files text,
    uploaders text, bin text, architecture text, standards_version text,
    homepage text, build_depends text, build_depends_indep text,
    build_conflicts text, build_conflicts_indep text, priority text, section
    text, distribution text, release release, component text, vcs_type text,
    vcs_url text, vcs_browser text,
    python_version text, checksums_sha1 text, checksums_sha256 text,
    original_maintainer text, dm_upload_allowed text,
    PRIMARY KEY (source, version, distribution, release, component));

GRANT SELECT ON sources TO PUBLIC;

-- no primary key possible: duplicate rows are possible because duplicate entries
-- in Uploaders: are allowed. yes.
CREATE TABLE uploaders (source text, version debversion, distribution text,
	release release, component text, uploader text, name text, email text);
   
GRANT SELECT ON uploaders TO PUBLIC;

CREATE INDEX uploaders_distrelcompsrcver_idx on uploaders(distribution, release, component, source, version);

CREATE INDEX sources_distrelcomp_idx on sources(distribution, release, component);

CREATE TABLE packages_summary ( package text, version debversion, source text,
source_version debversion, maintainer text, maintainer_name text, maintainer_email text, distribution text, release release,
component text,
PRIMARY KEY (package, version, distribution, release, component));

CREATE INDEX packages_summary_distrelcompsrcver_idx on packages_summary(distribution, release, component, source, source_version);

CREATE TABLE packages_distrelcomparch (distribution text, release release,
component text, architecture text);

CREATE TABLE packages
  (package text, version debversion, architecture text, maintainer text, maintainer_name text, maintainer_email text, description
    text, long_description text, source text, source_version debversion, essential text, depends text,
    recommends text, suggests text, enhances text, pre_depends text, breaks text,
    installed_size int, homepage text, size int,
    build_essential text, origin text, sha1 text, replaces text, section text,
    md5sum text, bugs text, priority text, tag text, task text, python_version text,
    provides text, conflicts text, sha256 text, original_maintainer text,
    distribution text, release release, component text,
  PRIMARY KEY (package, version, architecture, distribution, release, component),
  FOREIGN KEY (package, version, distribution, release, component) REFERENCES packages_summary DEFERRABLE);

GRANT SELECT ON packages TO PUBLIC;
GRANT SELECT ON packages_summary TO PUBLIC;
GRANT SELECT ON packages_distrelcomparch TO PUBLIC;

CREATE INDEX packages_source_idx on packages(source);
CREATE INDEX packages_distrelcomp_idx on packages(distribution, release, component);

-- Ubuntu sources and packages
CREATE TABLE ubuntu_sources
  (source text, version debversion, maintainer text,
    maintainer_name text, maintainer_email text, format text, files text,
    uploaders text, bin text, architecture text, standards_version text,
    homepage text, build_depends text, build_depends_indep text,
    build_conflicts text, build_conflicts_indep text, priority text, section
    text, distribution text, release release, component text, vcs_type text,
    vcs_url text, vcs_browser text,
    python_version text, checksums_sha1 text, checksums_sha256 text,
    original_maintainer text, dm_upload_allowed text,
    PRIMARY KEY (source, version, distribution, release, component));

CREATE INDEX ubuntu_sources_distrelcomp_idx on ubuntu_sources(distribution, release, component);

-- no primary key possible: duplicate rows are possible because duplicate entries
-- in Uploaders: are allowed. yes.
CREATE TABLE ubuntu_uploaders (source text, version debversion, distribution text,
	release release, component text, uploader text, name text, email text);
   
GRANT SELECT ON ubuntu_uploaders TO PUBLIC;

CREATE INDEX ubuntu_uploaders_distrelcompsrcver_idx on ubuntu_uploaders(distribution, release, component, source, version);

CREATE TABLE ubuntu_packages_summary ( package text, version debversion, source text,
source_version debversion, maintainer text, maintainer_name text, maintainer_email text, distribution text, release release,
component text,
PRIMARY KEY (package, version, distribution, release, component));

CREATE INDEX ubuntu_packages_summary_distrelcompsrcver_idx on ubuntu_packages_summary(distribution, release, component, source, source_version);

CREATE TABLE ubuntu_packages_distrelcomparch (distribution text, release release,
component text, architecture text);

CREATE TABLE ubuntu_packages
  (package text, version debversion, architecture text, maintainer text, maintainer_name text, maintainer_email text, description
    text, long_description text, source text, source_version debversion, essential text, depends text,
    recommends text, suggests text, enhances text, pre_depends text, breaks text,
    installed_size int, homepage text, size int,
    build_essential text, origin text, sha1 text, replaces text, section text,
    md5sum text, bugs text, priority text, tag text, task text, python_version text,
    provides text, conflicts text, sha256 text, original_maintainer text,
    distribution text, release release, component text,
  PRIMARY KEY (package, version, architecture, distribution, release, component),
  FOREIGN KEY (package, version, distribution, release, component) REFERENCES ubuntu_packages_summary DEFERRABLE);

GRANT SELECT ON ubuntu_sources TO PUBLIC;
GRANT SELECT ON ubuntu_packages TO PUBLIC;
GRANT SELECT ON ubuntu_packages_summary TO PUBLIC;
GRANT SELECT ON ubuntu_packages_distrelcomparch TO PUBLIC;

CREATE INDEX ubuntu_packages_source_idx on ubuntu_packages(source);
CREATE INDEX ubuntu_packages_distrelcomp_idx on ubuntu_packages(distribution, release, component);


-- Bugs (archived and unarchived)

CREATE TYPE bugs_severity AS ENUM ('fixed', 'wishlist', 'minor', 'normal', 'important', 'serious', 'grave', 'critical');

CREATE TABLE bugs
  (id int PRIMARY KEY, package text, source text, arrival timestamp, status text,
     severity bugs_severity, submitter text, owner text, done text, title text,
     last_modified timestamp, forwarded text, affects_stable boolean,
    affects_testing boolean, affects_unstable boolean,
    affects_experimental boolean);

CREATE TABLE bugs_packages
  (id int REFERENCES bugs, package text, source text,
	PRIMARY KEY (id, package));

CREATE TABLE bugs_merged_with
  (id int REFERENCES bugs, merged_with int,
PRIMARY KEY(id, merged_with));

CREATE TABLE bugs_found_in
  (id int REFERENCES bugs, version text,
   PRIMARY KEY(id, version));

CREATE TABLE bugs_fixed_in
  (id int REFERENCES bugs, version text,
   PRIMARY KEY(id, version));

CREATE TABLE bugs_tags
  (id int REFERENCES bugs, tag text, PRIMARY KEY (id, tag));

CREATE TABLE archived_bugs
  (id int PRIMARY KEY, package text, source text, arrival timestamp, status text,
     severity bugs_severity, submitter text, owner text, done text, title text,
     last_modified timestamp, forwarded text, affects_stable boolean,
    affects_testing boolean, affects_unstable boolean,
    affects_experimental boolean);

CREATE TABLE archived_bugs_packages
  (id int REFERENCES archived_bugs, package text, source text,
	PRIMARY KEY (id, package));

CREATE TABLE archived_bugs_merged_with
  (id int REFERENCES archived_bugs, merged_with int,
PRIMARY KEY(id, merged_with));

CREATE TABLE archived_bugs_found_in
  (id int REFERENCES archived_bugs, version text,
   PRIMARY KEY(id, version));

CREATE TABLE archived_bugs_fixed_in
  (id int REFERENCES archived_bugs, version text,
   PRIMARY KEY(id, version));

CREATE TABLE archived_bugs_tags
  (id int REFERENCES archived_bugs, tag text, PRIMARY KEY (id, tag));

-- usertags are either for archived or unarchived bugs, so we can't add a
-- foreign key here.
CREATE TABLE bugs_usertags
  (email text, tag text, id int);

CREATE VIEW bugs_rt_affects_stable AS
SELECT id, package, source FROM bugs
WHERE affects_stable
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'squeeze', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'lenny'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'lenny-ignore')
AND ( package IN (SELECT DISTINCT package FROM packages_summary p WHERE release = 'lenny')
OR source IN (SELECT DISTINCT source FROM sources WHERE release = 'lenny'));

CREATE VIEW bugs_rt_affects_testing AS
SELECT id, package, source FROM bugs
WHERE affects_testing 
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'lenny', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'squeeze'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'squeeze-ignore')
AND ( package IN (SELECT DISTINCT package FROM packages_summary p WHERE release = 'squeeze')
OR source IN (SELECT DISTINCT source FROM sources WHERE release = 'squeeze'));

CREATE VIEW bugs_rt_affects_unstable AS
SELECT id, package, source FROM bugs
WHERE affects_unstable 
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('lenny', 'sarge', 'etch', 'squeeze', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'sid'))
AND ( package IN (SELECT DISTINCT package FROM packages_summary p WHERE release = 'sid')
OR source IN (SELECT DISTINCT source FROM sources WHERE release = 'sid'));

CREATE VIEW bugs_rt_affects_testing_and_unstable AS
SELECT id, package, source FROM bugs
WHERE affects_unstable AND affects_testing
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sarge', 'etch', 'lenny', 'experimental'))
OR (id IN (SELECT id FROM bugs_tags WHERE tag = 'sid') AND id IN (SELECT id FROM bugs_tags WHERE tag = 'squeeze')))
AND ( package IN (SELECT DISTINCT package FROM packages_summary p WHERE release = 'sid')
OR source IN (SELECT DISTINCT source FROM sources WHERE release = 'sid'))
AND ( package IN (SELECT DISTINCT package FROM packages_summary p WHERE release = 'squeeze')
OR source IN (SELECT DISTINCT source FROM sources WHERE release = 'squeeze'));

GRANT SELECT ON bugs TO PUBLIC;
GRANT SELECT ON bugs_packages TO PUBLIC;
GRANT SELECT ON bugs_merged_with TO PUBLIC;
GRANT SELECT ON bugs_found_in TO PUBLIC;
GRANT SELECT ON bugs_fixed_in TO PUBLIC;
GRANT SELECT ON bugs_tags TO PUBLIC;
GRANT SELECT ON archived_bugs TO PUBLIC;
GRANT SELECT ON archived_bugs_packages TO PUBLIC;
GRANT SELECT ON archived_bugs_merged_with TO PUBLIC;
GRANT SELECT ON archived_bugs_found_in TO PUBLIC;
GRANT SELECT ON archived_bugs_fixed_in TO PUBLIC;
GRANT SELECT ON archived_bugs_tags TO PUBLIC;
GRANT SELECT ON bugs_rt_affects_stable TO PUBLIC;
GRANT SELECT ON bugs_rt_affects_testing_and_unstable TO PUBLIC;
GRANT SELECT ON bugs_rt_affects_unstable TO PUBLIC;
GRANT SELECT ON bugs_rt_affects_testing TO PUBLIC;
GRANT SELECT ON bugs_usertags TO PUBLIC;

-- Carnivore

CREATE TABLE carnivore_emails
 (id int, email text,
 PRIMARY KEY (id, email));

CREATE TABLE carnivore_names
 (id int, name text,
 PRIMARY KEY (id, name));

CREATE TABLE carnivore_keys
 (id int, key text, key_type text,
 PRIMARY KEY (key, key_type));

CREATE TABLE carnivore_login
 (id int, login text,
   PRIMARY KEY(id));

CREATE INDEX carnivore_keys_id_idx ON carnivore_keys (id);

GRANT SELECT on carnivore_emails TO PUBLIC;
GRANT SELECT on carnivore_names TO PUBLIC;
GRANT SELECT on carnivore_keys TO PUBLIC;
GRANT SELECT on carnivore_login TO PUBLIC;

-- Popcon

CREATE TABLE popcon (
   package text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (package));
 
CREATE TABLE popcon_src (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));

CREATE TABLE popcon_src_average (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));

GRANT SELECT ON popcon TO PUBLIC;
GRANT SELECT ON popcon_src_average TO PUBLIC;
GRANT SELECT ON popcon_src TO PUBLIC;

CREATE TABLE ubuntu_popcon (
   package text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (package));
 
CREATE TABLE ubuntu_popcon_src (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));

CREATE TABLE ubuntu_popcon_src_average (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));

GRANT SELECT ON ubuntu_popcon TO PUBLIC;
GRANT SELECT ON ubuntu_popcon_src_average TO PUBLIC;
GRANT SELECT ON ubuntu_popcon_src TO PUBLIC;

-- Lintian
CREATE TYPE lintian_tagtype AS ENUM('experimental', 'overriden', 'pedantic', 'information', 'warning', 'error');
CREATE TABLE lintian (
  package TEXT NOT NULL,
  tag_type lintian_tagtype NOT NULL,
  package_type TEXT,
  tag TEXT NOT NULL,
  information TEXT
);

GRANT SELECT ON lintian TO PUBLIC;

-- Debtags

-- one row per <package, tag> *pair*
CREATE TABLE debtags (
  package TEXT NOT NULL,
  tag TEXT NOT NULL
);

GRANT SELECT ON debtags TO PUBLIC;

CREATE INDEX debtags_tag_idx ON debtags(tag);
CREATE INDEX debtags_package_idx ON debtags(package);

-- Orphaned packages

CREATE TABLE orphaned_packages (
  source TEXT PRIMARY KEY,
  type TEXT,
  bug INT,
  description TEXT,
  orphaned_time TIMESTAMP
);

GRANT SELECT ON orphaned_packages TO PUBLIC;

-- Testing migrations

CREATE TABLE migrations
  (source text PRIMARY KEY, in_testing date, testing_version debversion, in_unstable date, unstable_version debversion, sync date, sync_version debversion, first_seen date);

GRANT SELECT ON migrations TO PUBLIC;

-- Upload history

CREATE TABLE upload_history
 (id serial, package text, version debversion, date timestamp with time zone,
 changed_by text, changed_by_name text, changed_by_email text, maintainer text, maintainer_name text, maintainer_email text, nmu boolean, signed_by text, signed_by_name text, signed_by_email text, key_id text,
 fingerprint text,
 PRIMARY KEY (id));

CREATE TABLE upload_history_architecture
 (id int REFERENCES upload_history, architecture text,
 PRIMARY KEY (id, architecture));
  
CREATE TABLE upload_history_closes
 (id int REFERENCES upload_history, bug int,
 PRIMARY KEY (id, bug));

GRANT SELECT ON upload_history TO PUBLIC;
GRANT SELECT ON upload_history_architecture TO PUBLIC;
GRANT SELECT ON upload_history_closes TO PUBLIC;

-- Ubuntu bugs
CREATE TABLE ubuntu_bugs (
bug int,
title text,
reporter_login text,
reporter_name text,
duplicate_of int,
date_reported text,
date_updated text,
security boolean,
PRIMARY KEY (bug));

CREATE TABLE ubuntu_bugs_duplicates (
bug int REFERENCES ubuntu_bugs,
duplicate int,
PRIMARY KEY (bug, duplicate));

CREATE TABLE ubuntu_bugs_subscribers (
bug int REFERENCES ubuntu_bugs,
subscriber_login text,
subscriber_name text);

CREATE TABLE ubuntu_bugs_tags (
bug int REFERENCES ubuntu_bugs,
tag text,
PRIMARY KEY (bug, tag));

CREATE TABLE ubuntu_bugs_tasks (
bug int REFERENCES ubuntu_bugs,
package text,
distro text,
status text,
importance text,
component text,
milestone text,
date_created text,
date_assigned text,
date_closed text,
date_incomplete text,
date_confirmed text,
date_inprogress text,
date_fix_committed text,
date_fix_released text,
date_left_new text,
date_triaged text,
date_left_closed text,
watch text,
reporter_login text,
reporter_name text,
assignee_login text,
assignee_name text,
PRIMARY KEY (bug, package, distro));

CREATE INDEX ubuntu_bugs_tags_idx on ubuntu_bugs_tags(bug);
CREATE INDEX ubuntu_bugs_tasks_idx on ubuntu_bugs_tasks(bug);
CREATE INDEX ubuntu_bugs_duplicates_idx on ubuntu_bugs_duplicates(bug);
CREATE INDEX ubuntu_bugs_subscribers_idx on ubuntu_bugs_subscribers(bug);

GRANT SELECT ON ubuntu_bugs TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_duplicates TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_subscribers TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_tags TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_tasks TO PUBLIC;

CREATE VIEW all_sources AS
SELECT * FROM sources
UNION ALL SELECT * FROM ubuntu_sources;

CREATE VIEW all_packages AS
SELECT * FROM packages
UNION ALL SELECT * FROM ubuntu_packages;

CREATE VIEW all_packages_distrelcomparch AS
SELECT * FROM packages_distrelcomparch
UNION ALL SELECT * FROM ubuntu_packages_distrelcomparch;

CREATE VIEW all_bugs AS
SELECT * FROM bugs
UNION ALL SELECT * FROM archived_bugs;

GRANT SELECT ON all_sources TO PUBLIC;
GRANT SELECT ON all_packages TO PUBLIC;
GRANT SELECT ON all_packages_distrelcomparch TO PUBLIC;
GRANT SELECT ON all_bugs TO PUBLIC;

CREATE TABLE ddtp (
       package      text,
       distribution text,
       release      release,
       component    text,   -- == 'main' for the moment
       version      debversion,   -- different versions for a package might exist because some archs
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

-- active_dds view
CREATE VIEW active_dds AS
SELECT DISTINCT carnivore_login.id, login
FROM carnivore_login, carnivore_keys
WHERE carnivore_keys.id = carnivore_login.id
AND key_type = 'keyring';

GRANT SELECT ON active_dds TO PUBLIC;

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
GRANT SELECT ON lintian TO PUBLIC;


