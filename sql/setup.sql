-- Sources and Packages
CREATE TABLE sources
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

GRANT SELECT ON sources TO PUBLIC;

CREATE VIEW sources_uniq AS
select * from sources s1
where not exists (select * from sources s2
where s1.source = s2.source
and s1.distribution = s2.distribution
and s1.release = s2.release
and s1.component = s2.component
and s2.version > s1.version);

GRANT SELECT ON sources_uniq TO PUBLIC;

CREATE VIEW sources_redundant AS
select * from sources s1
where exists (select * from sources s2
where s1.source = s2.source
and s1.distribution = s2.distribution
and s1.release = s2.release
and s1.component = s2.component
and s2.version > s1.version);

GRANT SELECT ON sources_redundant TO PUBLIC;


-- no primary key possible: duplicate rows are possible because duplicate entries
-- in Uploaders: are allowed. yes.
CREATE TABLE uploaders (source text, version debversion, distribution text,
	release text, component text, uploader text, name text, email text);
   
GRANT SELECT ON uploaders TO PUBLIC;

CREATE INDEX uploaders_distrelcompsrcver_idx on uploaders(distribution, release, component, source, version);

CREATE INDEX sources_distrelcomp_idx on sources(distribution, release, component);

CREATE TABLE packages_summary ( package text, version debversion, source text,
source_version debversion, maintainer text, maintainer_name text, maintainer_email text, distribution text, release text,
component text,
PRIMARY KEY (package, version, distribution, release, component));

CREATE INDEX packages_summary_distrelcompsrcver_idx on packages_summary(distribution, release, component, source, source_version);

CREATE TABLE packages_distrelcomparch (distribution text, release text,
component text, architecture text);

CREATE TABLE packages
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
  FOREIGN KEY (package, version, distribution, release, component) REFERENCES packages_summary DEFERRABLE);

GRANT SELECT ON packages TO PUBLIC;
GRANT SELECT ON packages_summary TO PUBLIC;
GRANT SELECT ON packages_distrelcomparch TO PUBLIC;

CREATE INDEX packages_source_idx on packages(source);
CREATE INDEX packages_distrelcomp_idx on packages(distribution, release, component);
CREATE INDEX packages_pkgverdescr_idx ON packages USING btree (package, version, description);

-- Ubuntu sources and packages
CREATE TABLE ubuntu_sources
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

CREATE INDEX ubuntu_sources_distrelcomp_idx on ubuntu_sources(distribution, release, component);

-- no primary key possible: duplicate rows are possible because duplicate entries
-- in Uploaders: are allowed. yes.
CREATE TABLE ubuntu_uploaders (source text, version debversion, distribution text,
	release text, component text, uploader text, name text, email text);
   
GRANT SELECT ON ubuntu_uploaders TO PUBLIC;

CREATE INDEX ubuntu_uploaders_distrelcompsrcver_idx on ubuntu_uploaders(distribution, release, component, source, version);

CREATE TABLE ubuntu_packages_summary ( package text, version debversion, source text,
source_version debversion, maintainer text, maintainer_name text, maintainer_email text, distribution text, release text,
component text,
PRIMARY KEY (package, version, distribution, release, component));

CREATE INDEX ubuntu_packages_summary_distrelcompsrcver_idx on ubuntu_packages_summary(distribution, release, component, source, source_version);

CREATE TABLE ubuntu_packages_distrelcomparch (distribution text, release text,
component text, architecture text);

CREATE TABLE ubuntu_packages
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
  FOREIGN KEY (package, version, distribution, release, component) REFERENCES ubuntu_packages_summary DEFERRABLE);

GRANT SELECT ON ubuntu_sources TO PUBLIC;
GRANT SELECT ON ubuntu_packages TO PUBLIC;
GRANT SELECT ON ubuntu_packages_summary TO PUBLIC;
GRANT SELECT ON ubuntu_packages_distrelcomparch TO PUBLIC;

CREATE INDEX ubuntu_packages_source_idx on ubuntu_packages(source);
CREATE INDEX ubuntu_packages_distrelcomp_idx on ubuntu_packages(distribution, release, component);

-- Other derivatives sources and packages
CREATE TABLE derivatives_sources
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

CREATE INDEX derivatives_sources_distrelcomp_idx on derivatives_sources(distribution, release, component);

-- no primary key possible: duplicate rows are possible because duplicate entries
-- in Uploaders: are allowed. yes.
CREATE TABLE derivatives_uploaders (source text, version debversion, distribution text,
	release text, component text, uploader text, name text, email text);
   
GRANT SELECT ON derivatives_uploaders TO PUBLIC;

CREATE INDEX derivatives_uploaders_distrelcompsrcver_idx on derivatives_uploaders(distribution, release, component, source, version);

CREATE TABLE derivatives_packages_summary ( package text, version debversion, source text,
source_version debversion, maintainer text, maintainer_name text, maintainer_email text, distribution text, release text,
component text,
PRIMARY KEY (package, version, distribution, release, component));

CREATE INDEX derivatives_packages_summary_distrelcompsrcver_idx on derivatives_packages_summary(distribution, release, component, source, source_version);

CREATE TABLE derivatives_packages_distrelcomparch (distribution text, release text,
component text, architecture text);

CREATE TABLE derivatives_packages
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
  FOREIGN KEY (package, version, distribution, release, component) REFERENCES derivatives_packages_summary DEFERRABLE);

GRANT SELECT ON derivatives_sources TO PUBLIC;
GRANT SELECT ON derivatives_packages TO PUBLIC;
GRANT SELECT ON derivatives_packages_summary TO PUBLIC;
GRANT SELECT ON derivatives_packages_distrelcomparch TO PUBLIC;

CREATE INDEX derivatives_packages_source_idx on derivatives_packages(source);
CREATE INDEX derivatives_packages_distrelcomp_idx on derivatives_packages(distribution, release, component);

-- Archived releases

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

-- Bugs (archived and unarchived)

CREATE TYPE bugs_severity AS ENUM ('fixed', 'wishlist', 'minor', 'normal', 'important', 'serious', 'grave', 'critical');

CREATE TABLE bugs
  (id int PRIMARY KEY, package text, source text, arrival timestamp, status text,
     severity bugs_severity, submitter text, submitter_name text,
     submitter_email text, owner text, owner_name text, owner_email text,
     done text, done_name text, done_email text, done_date timestamp, title text,
     last_modified timestamp, forwarded text, affects_oldstable boolean,
     affects_stable boolean,
    affects_testing boolean, affects_unstable boolean,
    affects_experimental boolean,
	affected_packages text,
	affected_sources text);

CREATE TABLE bugs_packages
  (id int REFERENCES bugs, package text, source text,
	PRIMARY KEY (id, package));

CREATE INDEX bugs_packages_source_idx ON bugs_packages (source);
CREATE INDEX bugs_packages_package_idx ON bugs_packages (package);
CREATE INDEX bugs_source_idx ON bugs (source);
CREATE INDEX bugs_package_idx ON bugs (package);
CREATE INDEX bugs_severity_idx ON bugs USING btree (severity);

CREATE INDEX sources_release_idx ON sources(release);

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
CREATE INDEX bugs_tags_tag_idx ON bugs_tags(tag);

CREATE TABLE bugs_blocks
  (id int REFERENCES bugs, blocked int,
PRIMARY KEY(id, blocked));

CREATE TABLE bugs_blockedby
  (id int REFERENCES bugs, blocker int,
PRIMARY KEY(id, blocker));

CREATE TABLE archived_bugs
  (id int PRIMARY KEY, package text, source text, arrival timestamp, status text,
     severity bugs_severity, submitter text, submitter_name text,
     submitter_email text, owner text, owner_name text, owner_email text,
     done text, done_name text, done_email text, done_date timestamp, title text,
     last_modified timestamp, forwarded text, affects_oldstable boolean,
     affects_stable boolean,
    affects_testing boolean, affects_unstable boolean,
    affects_experimental boolean,
	affected_packages text,
	affected_sources text);

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

CREATE TABLE archived_bugs_blocks
  (id int REFERENCES archived_bugs, blocked int,
PRIMARY KEY(id, blocked));

CREATE TABLE archived_bugs_blockedby
  (id int REFERENCES archived_bugs, blocker int,
PRIMARY KEY(id, blocker));

-- timestamps used to do incremental update for bugs

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

GRANT SELECT ON bugs_stamps TO PUBLIC;
GRANT SELECT ON archived_bugs_stamps TO PUBLIC;

-- usertags are either for archived or unarchived bugs, so we can't add a
-- foreign key here.
CREATE TABLE bugs_usertags
  (email text, tag text, id int);

CREATE VIEW bugs_rt_affects_oldstable AS
SELECT id, package, source FROM bugs
WHERE affects_oldstable
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'lenny', 'wheezy', 'jessie', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'squeeze'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'squeeze-ignore')
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='squeeze')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='squeeze'));

CREATE VIEW bugs_rt_affects_stable AS
SELECT id, package, source FROM bugs
WHERE affects_stable
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'lenny', 'squeeze', 'jessie', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'wheezy'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'wheezy-ignore')
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='wheezy')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='wheezy'));

CREATE VIEW bugs_rt_affects_testing AS
SELECT id, package, source FROM bugs
WHERE affects_testing 
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'lenny', 'squeeze', 'wheezy', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'jessie'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'jessie-ignore')
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='jessie')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='jessie'));

CREATE VIEW bugs_rt_affects_unstable AS
SELECT id, package, source FROM bugs
WHERE affects_unstable 
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('lenny', 'sarge', 'etch', 'squeeze', 'wheezy', 'jessie', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'sid'))
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='sid')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='sid'));

CREATE VIEW bugs_rt_affects_testing_and_unstable AS
SELECT id, package, source FROM bugs
WHERE affects_unstable AND affects_testing
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sarge', 'etch', 'lenny', 'squeeze', 'wheezy', 'experimental'))
OR (id IN (SELECT id FROM bugs_tags WHERE tag = 'sid') AND id IN (SELECT id FROM bugs_tags WHERE tag = 'jessie')))
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='jessie')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='jessie'))
AND (id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='sid')
 OR id in (select id from packages_summary, bugs_packages where packages_summary.package = bugs_packages.package and release='sid'));

GRANT SELECT ON bugs TO PUBLIC;
GRANT SELECT ON bugs_packages TO PUBLIC;
GRANT SELECT ON bugs_merged_with TO PUBLIC;
GRANT SELECT ON bugs_found_in TO PUBLIC;
GRANT SELECT ON bugs_fixed_in TO PUBLIC;
GRANT SELECT ON bugs_tags TO PUBLIC;
GRANT SELECT ON bugs_blocks TO PUBLIC;
GRANT SELECT ON bugs_blockedby TO PUBLIC;
GRANT SELECT ON archived_bugs TO PUBLIC;
GRANT SELECT ON archived_bugs_packages TO PUBLIC;
GRANT SELECT ON archived_bugs_merged_with TO PUBLIC;
GRANT SELECT ON archived_bugs_found_in TO PUBLIC;
GRANT SELECT ON archived_bugs_fixed_in TO PUBLIC;
GRANT SELECT ON archived_bugs_tags TO PUBLIC;
GRANT SELECT ON archived_bugs_blocks TO PUBLIC;
GRANT SELECT ON archived_bugs_blockedby TO PUBLIC;
GRANT SELECT ON bugs_rt_affects_oldstable TO PUBLIC;
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

-- debian maintainers

CREATE TABLE debian_maintainers (
maintainer TEXT,
maintainer_name TEXT,
maintainer_email TEXT,
fingerprint TEXT,
package TEXT,
granted_by_fingerprint TEXT
);

GRANT SELECT ON debian_maintainers TO PUBLIC;


-- Popcon

CREATE TABLE popcon (
   package text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (package));
 
CREATE TABLE popcon_src (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));
-- nicer name.
CREATE VIEW sources_popcon as select * from popcon_src;

CREATE TABLE popcon_src_average (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));

GRANT SELECT ON popcon TO PUBLIC;
GRANT SELECT ON popcon_src_average TO PUBLIC;
GRANT SELECT ON popcon_src TO PUBLIC;
GRANT SELECT ON sources_popcon TO PUBLIC;

CREATE TABLE ubuntu_popcon (
   package text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (package));
 
CREATE TABLE ubuntu_popcon_src (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));
CREATE VIEW ubuntu_sources_popcon AS SELECT * from ubuntu_popcon_src;

CREATE TABLE ubuntu_popcon_src_average (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));

GRANT SELECT ON ubuntu_popcon TO PUBLIC;
GRANT SELECT ON ubuntu_popcon_src_average TO PUBLIC;
GRANT SELECT ON ubuntu_popcon_src TO PUBLIC;
GRANT SELECT ON ubuntu_sources_popcon TO PUBLIC;

-- Lintian
CREATE TYPE lintian_tagtype AS ENUM('experimental', 'overriden', 'pedantic', 'information', 'warning', 'error');
CREATE TABLE lintian (
  package TEXT NOT NULL,
  tag_type lintian_tagtype NOT NULL,
  package_type TEXT,
  package_version debversion,
  package_arch TEXT,
  tag TEXT NOT NULL,
  information TEXT
);

GRANT SELECT ON lintian TO PUBLIC;

CREATE TABLE ubuntu_lintian (
  package TEXT NOT NULL,
  tag_type lintian_tagtype NOT NULL,
  package_type TEXT,
  package_version debversion,
  package_arch TEXT,
  tag TEXT NOT NULL,
  information TEXT
);

GRANT SELECT ON ubuntu_lintian TO PUBLIC;

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
 (source text, version debversion, date timestamp with time zone,
 changed_by text, changed_by_name text, changed_by_email text, maintainer text, maintainer_name text, maintainer_email text, nmu boolean, signed_by text, signed_by_name text, signed_by_email text, key_id text, distribution text, file text,
 fingerprint text,
 PRIMARY KEY (source, version));

CREATE INDEX upload_history_distribution_date_idx on upload_history(distribution, date);
CREATE INDEX upload_history_fingerprint_idx on upload_history(fingerprint);

CREATE TABLE upload_history_architecture
 (source text, version debversion, architecture text, file text,
 PRIMARY KEY (source, version, architecture),
FOREIGN KEY (source, version) REFERENCES upload_history DEFERRABLE);
  
CREATE TABLE upload_history_closes
 (source text, version debversion, bug int, file text,
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

CREATE TABLE ubuntu_upload_history
 (source text, version debversion, date timestamp with time zone,
 changed_by text, changed_by_name text, changed_by_email text, maintainer text, maintainer_name text, maintainer_email text, nmu boolean, signed_by text, signed_by_name text, signed_by_email text, key_id text, distribution text, component text, file text, 
 fingerprint text, original_maintainer text, original_maintainer_name text, original_maintainer_email text,
 PRIMARY KEY (source, version));
CREATE TABLE ubuntu_upload_history_launchpad_closes
 (source text, version debversion, bug int, file text,
 PRIMARY KEY (source, version, bug),
FOREIGN KEY (source, version) REFERENCES ubuntu_upload_history DEFERRABLE);

CREATE TABLE ubuntu_upload_history_closes
 (source text, version debversion, bug int, file text,
 PRIMARY KEY (source, version, bug),
FOREIGN KEY (source, version) REFERENCES ubuntu_upload_history DEFERRABLE);

GRANT SELECT ON ubuntu_upload_history TO PUBLIC;
GRANT SELECT ON ubuntu_upload_history_closes TO PUBLIC;
GRANT SELECT ON ubuntu_upload_history_launchpad_closes TO PUBLIC;

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
patches boolean,
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
CREATE INDEX ubuntu_bugs_tasks_package_idx on ubuntu_bugs_tasks(package);

GRANT SELECT ON ubuntu_bugs TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_duplicates TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_subscribers TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_tags TO PUBLIC;
GRANT SELECT ON ubuntu_bugs_tasks TO PUBLIC;

CREATE VIEW all_sources AS
SELECT * FROM sources
UNION ALL SELECT * FROM ubuntu_sources
UNION ALL SELECT * FROM derivatives_sources;

CREATE VIEW all_packages AS
SELECT * FROM packages
UNION ALL SELECT * FROM ubuntu_packages
UNION ALL SELECT * FROM derivatives_packages;

CREATE VIEW all_packages_distrelcomparch AS
SELECT * FROM packages_distrelcomparch
UNION ALL SELECT * FROM ubuntu_packages_distrelcomparch
UNION ALL SELECT * FROM derivatives_packages_distrelcomparch;

CREATE VIEW all_bugs AS
SELECT * FROM bugs
UNION ALL SELECT * FROM archived_bugs;

GRANT SELECT ON all_sources TO PUBLIC;
GRANT SELECT ON all_packages TO PUBLIC;
GRANT SELECT ON all_packages_distrelcomparch TO PUBLIC;
GRANT SELECT ON all_bugs TO PUBLIC;

CREATE TABLE descriptions (
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
GRANT SELECT ON descriptions TO PUBLIC;

CREATE TABLE ubuntu_descriptions (
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
GRANT SELECT ON ubuntu_descriptions TO PUBLIC;

CREATE TABLE derivatives_descriptions (
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
GRANT SELECT ON derivatives_descriptions TO PUBLIC;

-- Add house keeping table to enable deciding whether some translation file
-- was imported previousely and thus reducing workload on UDD host in
-- preventing doing duplicate work
CREATE TABLE description_imports (
    distribution         text not null,
    release              text not null,
    component            text not null,
    language             text not null,
    translationfile      text not null,
    translationfile_sha1 text not null,
    import_date          timestamp default now(),
    PRIMARY KEY (distribution, release, component, language)
);

CREATE TABLE ubuntu_description_imports (
    distribution         text not null,
    release              text not null,
    component            text not null,
    language             text not null,
    translationfile      text not null,
    translationfile_sha1 text not null,
    import_date          timestamp default now(),
    PRIMARY KEY (distribution, release, component, language)
);

-- active_dds view
CREATE VIEW active_dds AS
SELECT DISTINCT carnivore_login.id, login
FROM carnivore_login, carnivore_keys
WHERE carnivore_keys.id = carnivore_login.id
AND key_type = 'keyring';

GRANT SELECT ON active_dds TO PUBLIC;

-- DEHS
CREATE TYPE dehs_status AS ENUM('error', 'uptodate', 'outdated', 'newer-in-debian');
CREATE TABLE dehs (
  source TEXT NOT NULL,
  unstable_version debversion,
  unstable_upstream text,
  unstable_parsed_version text,
  unstable_status dehs_status,
  unstable_last_uptodate timestamp,
  experimental_version debversion,
  experimental_upstream text,
  experimental_parsed_version text,
  experimental_status dehs_status,
  experimental_last_uptodate timestamp,
  PRIMARY KEY (source)
);
GRANT SELECT ON dehs TO PUBLIC;

-- LDAP
CREATE TABLE ldap (
  uid numeric,
  login text,
  cn text,
  sn text,
  expire boolean,
  location text,
  country text,
  activity_from timestamp with time zone,
  activity_from_info text,
  activity_pgp timestamp with time zone,
  activity_pgp_info text,
  gecos text,
  birthdate date,
  gender numeric,
  fingerprint text,
  PRIMARY KEY (uid)
);
GRANT SELECT ON ldap TO guestdd;

-- wannabuild
CREATE TABLE wannabuild (
  source text,
  distribution text,
  architecture text,
  version debversion,
  state text,
  installed_version debversion,
  previous_state text,
  state_change timestamp,
  binary_nmu_version numeric,
  notes text,
  PRIMARY KEY (source, distribution, architecture)
);
GRANT SELECT ON wannabuild TO public;

-- package_removal_batch
CREATE TABLE package_removal_batch (
  id int,
  time timestamp,
  ftpmaster text,
  distribution text,
  requestor text,
  reasons text,
  PRIMARY KEY (id)
);
GRANT SELECT ON package_removal_batch TO public;

-- package_removal
CREATE TABLE package_removal (
  batch_id int,
  name text,
  version debversion,
  arch_array text[],
  PRIMARY KEY(batch_id, name, version),
  FOREIGN KEY(batch_id) REFERENCES package_removal_batch(id)
);
GRANT SELECT ON package_removal TO public;

-- timings of data operations
CREATE TABLE timestamps (
  id serial,
  source text,
  command text,
  start_time timestamp,
  end_time timestamp,
  PRIMARY KEY (id)
);
GRANT SELECT ON timestamps TO public;

-- views
-- bugs_count
create view bugs_count as
select coalesce(b1.source, b2.source) as source, coalesce(rc_bugs, 0) as rc_bugs, coalesce(all_bugs, 0) as all_bugs from
((select source, count(*) as rc_bugs
from bugs
where severity >= 'serious'
and status='pending'
and id not in (select id from bugs_merged_with where id > merged_with)
group by source) b1
FULL JOIN (select source, count(*) as all_bugs
from bugs
where status='pending'
and id not in (select id from bugs_merged_with where id > merged_with)
group by source) b2 ON (b1.source = b2.source));

grant select on bugs_count to public;
-- bapase
create view bapase as
select s.source, s.version, type, bug, description,
orphaned_time, (current_date - orphaned_time::date) as orphaned_age,
in_testing, (current_date - in_testing) as testing_age, testing_version,
in_unstable, (current_date - in_unstable) as unstable_age, unstable_version,
sync, (current_date - sync) as sync_age, sync_version,
first_seen, (current_date - first_seen) as first_seen_age,
uh.date as upload_date, (current_date - uh.date::date) as upload_age,
nmu, coalesce(nmus, 0) as nmus, coalesce(rc_bugs,0) as rc_bugs, coalesce(all_bugs,0) as all_bugs,
coalesce(insts,0) as insts, coalesce(vote,0) as vote, s.maintainer, bugs.last_modified, 
(current_date - bugs.last_modified::date) as last_modified_age
from sources_uniq s
left join orphaned_packages op on s.source = op.source
left join migrations tm on s.source = tm.source
left join  upload_history uh on s.source = uh.source and s.version = uh.version
left join  upload_history_nmus uhn on s.source = uhn.source
left join bugs_count b on s.source = b.source
left join popcon_src ps on s.source = ps.source
left join bugs on op.bug = bugs.id
where s.distribution='debian' and s.release='sid';
GRANT SELECT ON bapase TO PUBLIC;

-- really active dds
CREATE VIEW really_active_dds AS
    SELECT DISTINCT carnivore_login.id, carnivore_login.login FROM carnivore_login, carnivore_keys, ldap WHERE ((((carnivore_keys.id = carnivore_login.id) AND (carnivore_keys.key_type = 'keyring'::text)) AND (carnivore_login.login = ldap.login)) AND (ldap.activity_pgp > '2009-01-01 00:00:00+00'::timestamp with time zone));
GRANT SELECT ON TABLE really_active_dds TO guestdd;

-- PTS
CREATE TABLE pts (
  source text,
  email text,
  PRIMARY KEY(source, email)
);
GRANT SELECT ON pts TO guestdd;

-- HISTORICAL DATA
CREATE SCHEMA history;
GRANT USAGE ON SCHEMA history TO public;
CREATE TABLE history.sources_count (
  ts timestamp,
  total_sid_main int, total_sid_contrib int, total_sid_nonfree int,
  vcstype_arch int, vcstype_bzr int, vcstype_cvs int, vcstype_darcs int, vcstype_git int, vcstype_hg  int, vcstype_mtn int, vcstype_svn int,
format_3native int, format_3quilt int,
  PRIMARY KEY (ts)
);
GRANT SELECT ON history.sources_count TO public;

CREATE TABLE hints
 (source text, version debversion, architecture text,
    type text, argument text, file text, comment text);
CREATE INDEX hints_idx on hints(source, version);
GRANT SELECT ON hints TO public;

CREATE VIEW relevant_hints AS 
  SELECT source, version, architecture, type, argument, file, comment FROM hints
  WHERE version is NULL
  OR type = 'approve'
  OR (type IN ('unblock', 'age-days', 'hint', 'easy') AND (source, version) IN (select source, version from sources where release='sid'))
  OR (type IN ('remove') AND (source, version) IN (select source, version from sources where release='squeeze')) ;
GRANT SELECT ON relevant_hints TO public;

CREATE TABLE deferred
 (source text, version debversion, distribution text, urgency text, date timestamp with time zone, delayed_until timestamp, delay_remaining interval,
 changed_by text, changed_by_name text, changed_by_email text, maintainer text, maintainer_name text, maintainer_email text, changes text,
 PRIMARY KEY (source, version));

CREATE TABLE deferred_architecture
 (source text, version debversion, architecture text,
 PRIMARY KEY (source, version, architecture),
FOREIGN KEY (source, version) REFERENCES deferred DEFERRABLE);

CREATE TABLE deferred_binary
 (source text, version debversion, package text,
 PRIMARY KEY (source, version, package),
FOREIGN KEY (source, version) REFERENCES deferred DEFERRABLE);
   
CREATE TABLE deferred_closes
 (source text, version debversion, id int,
 PRIMARY KEY (source, version, id),
FOREIGN KEY (source, version) REFERENCES deferred DEFERRABLE);

GRANT SELECT ON deferred TO public;
GRANT SELECT ON deferred_architecture TO public;
GRANT SELECT ON deferred_binary TO public;
GRANT SELECT ON deferred_closes TO public;

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

CREATE VIEW sponsorship_requests AS
SELECT id,
SUBSTRING(title from '^RFS: ([^/]*)/') as source,
SUBSTRING(title from '/([^ ]*)( |$)') as version,
title
FROM bugs WHERE package='sponsorship-requests' AND status='pending';

GRANT SELECT ON sponsorship_requests TO PUBLIC;

-- ftp-master autorejects
CREATE TYPE ftp_autoreject_type AS ENUM('lintian');
CREATE TYPE ftp_autoreject_level AS ENUM('fatal','nonfatal');
CREATE TABLE ftp_autorejects (
tag TEXT,
autoreject_type ftp_autoreject_type,
autoreject_level ftp_autoreject_level,
PRIMARY KEY(tag)
);

GRANT SELECT ON ftp_autorejects TO PUBLIC;

-- pseudo-packages

CREATE TABLE pseudo_packages (
package TEXT,
maintainer TEXT,
maintainer_name TEXT,
maintainer_email TEXT,
description TEXT,
PRIMARY KEY(package)
);

GRANT SELECT ON pseudo_packages TO PUBLIC;


-- wnpp view
CREATE VIEW wnpp AS
SELECT id, SUBSTRING(title from '^([A-Z]{1,3}): .*') as type, SUBSTRING(title from '^[A-Z]{1,3}: ([^ ]+)(?: -- .*)') as source, title FROM bugs WHERE package='wnpp' AND status!='done';

GRANT SELECT ON wnpp TO PUBLIC;


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
            CASE WHEN bibjournal.value IS NOT NULL THEN E',\n  Journal = {' || replace(bibjournal.value, '&', E'\\&') || '}' ELSE '' END ||
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

DROP TABLE IF EXISTS blends_prospectivepackages CASCADE;

CREATE TABLE blends_prospectivepackages
  (blend text,
   package text,
   source text,
   maintainer text,
   maintainer_name text,
   maintainer_email text,
   changed_by text,
   changed_by_name text,
   changed_by_email text,
   uploaders text,
   description text,
   long_description text,
   description_md5 text,
   homepage text,
   component text,
   section text,
   priority text,
   vcs_type text,
   vcs_url text,
   vcs_browser text,
   wnpp int,
   wnpp_type text,
   wnpp_desc text,
   license text,
   chlog_date text, -- time,
   chlog_version debversion
);

GRANT SELECT ON blends_prospectivepackages TO PUBLIC;

DROP TABLE IF EXISTS blends_metadata CASCADE;
CREATE TABLE blends_metadata (
  -- fieldname   type,   --  example value
     blend       TEXT,   --  'debian-med'   (== the source package name)
     blendname   TEXT,   --  'Debian Med'   (== human readable name)
     projecturl  TEXT,   --  'http://debian-med.alioth.debian.org/'
     tasksprefix TEXT,   --  'med'
     homepage    TEXT,
     aliothurl   TEXT,
     projectlist TEXT,
     logourl     TEXT,
     outputdir   TEXT,
     datadir     TEXT,
     vcsdir      TEXT,
     css         TEXT,
     advertising TEXT,
     pkglist     TEXT,
     dehsmail    TEXT,
     distribution TEXT,
     PRIMARY KEY (blend)
);

GRANT SELECT ON blends_metadata TO PUBLIC;

DROP TABLE IF EXISTS blends_tasks;
CREATE TABLE blends_tasks (
  -- fieldname        type,    --  example value
     blend            TEXT REFERENCES blends_metadata,
     task             TEXT,    --  'bio'
     title            TEXT,    --  'Biology'
     metapackage      BOOLEAN, --  Some tasks should not end up in a metapackage
     metapackage_name TEXT,    --  name of the resulting metapackage if exists
     section          TEXT,
     enhances         TEXT,
     leaf             TEXT,
     test_always_lang TEXT,
     description      TEXT,
     long_description TEXT,
     hashkey          TEXT,    -- md5 hash to check if a task file has changed/updated
     PRIMARY KEY (blend, task)
);

GRANT SELECT ON blends_tasks TO PUBLIC;

DROP TABLE IF EXISTS blends_dependencies;
CREATE TABLE blends_dependencies (
  -- fieldname    type,
     blend        TEXT REFERENCES blends_metadata,
     task         TEXT, -- CHECK (task IN (SELECT task from blends_tasks)),
     package      TEXT,
     dependency   CHARACTER(1) CHECK (dependency IN ('d', 'i', 'r', 's', 'a')), -- Depends / Ignore / Recommends / Suggests / Avoid
     distribution TEXT CHECK (distribution IN ('debian', 'new', 'prospective', 'ubuntu', 'other')),
     component    TEXT CHECK (component IN ('main', 'main/debian-installer', 'contrib', 'non-free', 'universe', 'universe/debian-installer', 'multiverse', 'restricted', 'local')),
     provides     BOOLEAN, -- true if package is a virtual package
     PRIMARY KEY (blend, task, package)
);

GRANT SELECT ON blends_dependencies TO PUBLIC;

-- For Blends bugs pages in web sentinel we need some priorisation of the dependency relations to make sure we get the
-- proper relation for more than one binary package from a single source package with different dependency relation.
DROP TABLE IF EXISTS blends_dependencies_priorities;
CREATE TABLE blends_dependencies_priorities (
     dependency   CHARACTER(1) CHECK (dependency IN ('d', 'i', 'r', 's', 'a')), -- Depends / Ignore / Recommends / Suggests / Avoid
     priority     int
);

GRANT SELECT ON blends_dependencies_priorities TO PUBLIC;

INSERT INTO blends_dependencies_priorities (dependency, priority) VALUES ('d', 1);
INSERT INTO blends_dependencies_priorities (dependency, priority) VALUES ('r', 2);
INSERT INTO blends_dependencies_priorities (dependency, priority) VALUES ('s', 3);
INSERT INTO blends_dependencies_priorities (dependency, priority) VALUES ('a', 4);
INSERT INTO blends_dependencies_priorities (dependency, priority) VALUES ('i', 5);

-- This table's data is used to properly generate the task-description file for a Blend
-- Tasksel doesn't allow boolean(eg OR : |) comparisons in dependencies such as package1 | package2. 
-- In these cases we need to know which packages, from the blends_dependencies table, are the alternatives between them
-- in order to include only one package (the first available) from a group of alternatives in the task-description file.
DROP TABLE IF EXISTS blends_dependencies_alternatives;
CREATE TABLE blends_dependencies_alternatives (
  -- fieldname    type,
     blend              TEXT REFERENCES blends_metadata,
     task               TEXT,
     alternatives       TEXT, -- content is in format: package1 | package2 | package3 ...
     dependency         CHARACTER(1) CHECK (dependency IN ('d', 'i', 'r', 's', 'a')), -- Depends / Ignore / Recommends / Suggests / Avoid
     distribution       TEXT CHECK (distribution IN ('debian', 'new', 'prospective', 'ubuntu', 'other')),
     component          TEXT CHECK (component IN ('main', 'main/debian-installer', 'contrib', 'non-free', 'universe', 'universe/debian-installer', 'multiverse', 'restricted', 'local')),
     contains_provides  BOOLEAN,  -- true if alternatives contain a virtual package
     PRIMARY KEY (blend, task, alternatives)
);

GRANT SELECT ON blends_dependencies_alternatives TO PUBLIC;

CREATE TABLE mentors_raw_users (
  id NUMERIC,
  name TEXT,
  email TEXT,
  gpg_id TEXT,
  PRIMARY KEY (id));

CREATE TABLE mentors_raw_packages (
  id NUMERIC,
  name TEXT,
  user_id NUMERIC,
  description TEXT,
  needs_sponsor NUMERIC,
  PRIMARY KEY(id)
);

CREATE TABLE mentors_raw_package_versions (
    id NUMERIC,
    package_id NUMERIC,
    version debversion,
    maintainer TEXT,
    section TEXT,
    distribution TEXT,
    component TEXT,
    priority TEXT,
    uploaded TIMESTAMP,
    closes TEXT,
    PRIMARY KEY(id)
);

CREATE TABLE mentors_raw_package_info (
  id NUMERIC,
  package_version_id NUMERIC,
  from_plugin TEXT,
  outcome TEXT,
  data text,
  severity numeric
);

CREATE VIEW mentors_most_recent_package_versions AS
SELECT mpv.*
   FROM mentors_raw_package_versions mpv left outer join mentors_raw_package_versions mpv2
   on (mpv.package_id = mpv2.package_id and mpv.id < mpv2.id and 
   mpv.distribution = mpv2.distribution)
   where mpv2.id is null and mpv.package_id is not null;

GRANT SELECT ON mentors_raw_users TO PUBLIC;
GRANT SELECT ON mentors_raw_packages TO PUBLIC;
GRANT SELECT ON mentors_raw_package_versions TO PUBLIC;
GRANT SELECT ON mentors_raw_package_info TO PUBLIC;
GRANT SELECT ON mentors_most_recent_package_versions TO PUBLIC;

-- key_packages
CREATE TABLE key_packages (
   source text,
   reason text,
   primary key (source)
);

GRANT SELECT ON key_packages TO PUBLIC;

-- bugs that are closed by packages that are not in the archive (yet)
-- currently filled by
-- - ftpnew
-- potential other sources
-- - mentors
CREATE TABLE potential_bug_closures
  (id int,
   source text,
   distribution text,
   origin text
   );

GRANT SELECT ON potential_bug_closures TO PUBLIC;

CREATE INDEX potential_bug_closures_id_idx ON potential_bug_closures (id);
CREATE INDEX potential_bug_closures_source_idx ON potential_bug_closures (source);

-- piuparts_status

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

-- testing autoremovals

CREATE TABLE testing_autoremovals
  (source text,
   version text,
   bugs text,
   first_seen bigint,
   last_checked bigint,
   removal_time bigint,
   rdeps text,
   buggy_deps text,
   bugs_deps text,
   rdeps_popcon bigint

   );

GRANT SELECT ON testing_autoremovals TO PUBLIC;

CREATE INDEX testing_autoremovals_source_idx ON testing_autoremovals (source);

