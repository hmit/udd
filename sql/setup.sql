-- Sources and Packages
CREATE TABLE sources
  (source text, version text, maintainer text, format text, files text,
    uploaders text, bin text, architecture text, standards_version text,
    homepage text, build_depends text, build_depends_indep text,
    build_conflicts text, build_conflicts_indep text, priority text, section
    text, distribution text, release text, component text, vcs_type text,
    vcs_url text, vcs_browser text,
    python_version text, checksums_sha1 text, checksums_sha256 text,
    original_maintainer text, dm_upload_allowed text,
    PRIMARY KEY (source, version, distribution, release, component));

GRANT SELECT ON sources TO PUBLIC;

CREATE INDEX sources_distrelcomp_idx on sources(distribution, release, component);

CREATE TABLE packages_summary ( package text, version text, source text,
source_version text, maintainer text, distribution text, release text,
component text,
PRIMARY KEY (package, version, distribution, release, component));

CREATE TABLE packages
  (package text, version text, architecture text, maintainer text, description
    text, source text, source_version text, essential text, depends text,
    recommends text, suggests text, enhances text, pre_depends text,
    installed_size int, homepage text, size int,
    build_essential text, origin text, sha1 text, replaces text, section text,
    md5sum text, bugs text, priority text, tag text, task text, python_version text,
    provides text, conflicts text, sha256 text, original_maintainer text,
    distribution text, release text, component text,
  PRIMARY KEY (package, version, architecture, distribution, release, component),
  FOREIGN KEY (package, version, distribution, release, component) REFERENCES packages_summary DEFERRABLE);

GRANT SELECT ON packages TO PUBLIC;
GRANT SELECT ON packages_summary TO PUBLIC;

CREATE INDEX packages_source_idx on packages(source);
CREATE INDEX packages_distrelcomp_idx on packages(distribution, release, component);

-- Ubuntu sources and packages

CREATE TABLE ubuntu_sources
  (source text, version text, maintainer text, format text, files text,
    uploaders text, bin text, architecture text, standards_version text,
    homepage text, build_depends text, build_depends_indep text,
    build_conflicts text, build_conflicts_indep text, priority text, section
    text, distribution text, release text, component text, vcs_type text,
    vcs_url text, vcs_browser text,
    python_version text, checksums_sha1 text, checksums_sha256 text,
    original_maintainer text, dm_upload_allowed text,
    PRIMARY KEY (source, version, distribution, release, component));

CREATE INDEX ubuntu_sources_distrelcomp_idx on ubuntu_sources(distribution, release, component);

CREATE TABLE ubuntu_packages_summary ( package text, version text, source text,
source_version text, maintainer text, distribution text, release text,
component text,
PRIMARY KEY (package, version, distribution, release, component));

CREATE TABLE ubuntu_packages
  (package text, version text, architecture text, maintainer text, description
    text, source text, source_version text, essential text, depends text,
    recommends text, suggests text, enhances text, pre_depends text,
    installed_size int, homepage text, size int,
    build_essential text, origin text, sha1 text, replaces text, section text,
    md5sum text, bugs text, priority text, tag text, task text, python_version text,
    provides text, conflicts text, sha256 text, original_maintainer text,
    distribution text, release text, component text,
  PRIMARY KEY (package, version, architecture, distribution, release, component),
  FOREIGN KEY (package, version, distribution, release, component) REFERENCES ubuntu_packages_summary DEFERRABLE);

GRANT SELECT ON ubuntu_sources TO PUBLIC;
GRANT SELECT ON ubuntu_packages TO PUBLIC;
GRANT SELECT ON ubuntu_packages_summary TO PUBLIC;

CREATE INDEX ubuntu_packages_source_idx on ubuntu_packages(source);
CREATE INDEX ubuntu_packages_distrelcomp_idx on ubuntu_packages(distribution, release, component);


-- Bugs (archived and unarchived)

CREATE TYPE bugs_severity AS ENUM ('fixed', 'wishlist', 'minor', 'normal', 'important', 'serious', 'grave', 'critical');

CREATE TABLE bugs
  (id int PRIMARY KEY, package text, source text, arrival timestamp, status text,
     severity bugs_severity, submitter text, owner text, title text,
     last_modified timestamp, affects_stable boolean,
    affects_testing boolean, affects_unstable boolean,
    affects_experimental boolean);

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
     severity bugs_severity, submitter text, owner text, title text,
     last_modified timestamp, affects_stable boolean,
    affects_testing boolean, affects_unstable boolean,
    affects_experimental boolean);

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
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'lenny', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'etch'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'etch-ignore')
AND ( package IN (SELECT DISTINCT package FROM packages_summary p WHERE release = 'etch')
OR source IN (SELECT DISTINCT source FROM sources WHERE release = 'etch'));

CREATE VIEW bugs_rt_affects_testing AS
SELECT id, package, source FROM bugs
WHERE affects_testing 
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'lenny'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'lenny-ignore')
AND ( package IN (SELECT DISTINCT package FROM packages_summary p WHERE release = 'lenny')
OR source IN (SELECT DISTINCT source FROM sources WHERE release = 'lenny'));

CREATE VIEW bugs_rt_affects_unstable AS
SELECT id, package, source FROM bugs
WHERE affects_unstable 
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('lenny', 'sarge', 'etch', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'sid'))
AND ( package IN (SELECT DISTINCT package FROM packages_summary p WHERE release = 'sid')
OR source IN (SELECT DISTINCT source FROM sources WHERE release = 'sid'));

CREATE VIEW bugs_rt_affects_testing_and_unstable AS
SELECT id, package, source FROM bugs
WHERE affects_unstable AND affects_testing
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sarge', 'etch', 'experimental'))
OR (id IN (SELECT id FROM bugs_tags WHERE tag = 'sid') AND id IN (SELECT id FROM bugs_tags WHERE tag = 'lenny')))
AND ( package IN (SELECT DISTINCT source FROM packages p WHERE release = 'sid')
OR source IN (SELECT DISTINCT source FROM sources WHERE release = 'sid'))
AND ( package IN (SELECT DISTINCT source FROM packages p WHERE release = 'lenny')
OR source IN (SELECT DISTINCT source FROM sources WHERE release = 'lenny'));

GRANT SELECT ON bugs TO PUBLIC;
GRANT SELECT ON bugs_merged_with TO PUBLIC;
GRANT SELECT ON bugs_found_in TO PUBLIC;
GRANT SELECT ON bugs_fixed_in TO PUBLIC;
GRANT SELECT ON bugs_tags TO PUBLIC;
GRANT SELECT ON archived_bugs TO PUBLIC;
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

CREATE DOMAIN lintian_tag_type AS TEXT
NOT NULL
CHECK(
     VALUE = 'error'
  OR VALUE = 'warning'
  OR VALUE = 'information'
  OR VALUE = 'experimental'
  OR VALUE = 'overriden'
);

CREATE TABLE lintian (
  package TEXT NOT NULL,
  tag_type lintian_tag_type,
  package_type TEXT,
  tag TEXT NOT NULL
);

GRANT SELECT ON lintian TO PUBLIC;

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
  (source text PRIMARY KEY, in_testing date, testing_version text, in_unstable date, unstable_version text, sync date, sync_version text, first_seen date);

GRANT SELECT ON migrations TO PUBLIC;

-- Upload history

CREATE TABLE upload_history
 (id serial, package text, version text, date timestamp with time zone,
 changed_by text, maintainer text, nmu boolean, signed_by text, key_id text,
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
watch text,
reporter_login text,
reporter_name text,
assignee_login text,
assignee_name text,
PRIMARY KEY (bug, package, distro));

GRANT SELECT ON ubuntu_bugs TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_duplicates TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_subscribers TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_tags TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_tasks TO PUBLIC;
