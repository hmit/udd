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
    text, long_description text, description_md5 text, source text, source_version debversion, essential text, depends text,
    recommends text, suggests text, enhances text, pre_depends text, breaks text,
    installed_size int, homepage text, size int,
    build_essential text, origin text, sha1 text, replaces text, section text,
    md5sum text, bugs text, priority text, tag text, task text, python_version text,
    ruby_versions text,
    provides text, conflicts text, sha256 text, original_maintainer text,
    distribution text, release text, component text,
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
    text, distribution text, release text, component text, vcs_type text,
    vcs_url text, vcs_browser text,
    python_version text, ruby_versions text, checksums_sha1 text, checksums_sha256 text,
    original_maintainer text, dm_upload_allowed boolean,
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
    text, long_description text, description_md5 text, source text, source_version debversion, essential text, depends text,
    recommends text, suggests text, enhances text, pre_depends text, breaks text,
    installed_size int, homepage text, size int,
    build_essential text, origin text, sha1 text, replaces text, section text,
    md5sum text, bugs text, priority text, tag text, task text, python_version text,
    ruby_versions text,
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
    text, long_description text, description_md5 text, source text, source_version debversion, essential text, depends text,
    recommends text, suggests text, enhances text, pre_depends text, breaks text,
    installed_size int, homepage text, size int,
    build_essential text, origin text, sha1 text, replaces text, section text,
    md5sum text, bugs text, priority text, tag text, task text, python_version text,
    ruby_versions text,
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
    affects_experimental boolean);

CREATE TABLE bugs_packages
  (id int REFERENCES bugs, package text, source text,
	PRIMARY KEY (id, package));

CREATE INDEX bugs_packages_source_idx ON bugs_packages (source);
CREATE INDEX bugs_packages_package_idx ON bugs_packages (package);
CREATE INDEX bugs_source_idx ON bugs (source);
CREATE INDEX bugs_package_idx ON bugs (package);

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

CREATE TABLE archived_bugs_blocks
  (id int REFERENCES archived_bugs, blocked int,
PRIMARY KEY(id, blocked));

CREATE TABLE archived_bugs_blockedby
  (id int REFERENCES archived_bugs, blocker int,
PRIMARY KEY(id, blocker));

-- usertags are either for archived or unarchived bugs, so we can't add a
-- foreign key here.
CREATE TABLE bugs_usertags
  (email text, tag text, id int);

CREATE VIEW bugs_rt_affects_oldstable AS
SELECT id, package, source FROM bugs
WHERE affects_oldstable
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'squeeze', 'wheezy', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'lenny'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'lenny-ignore')
AND id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='lenny');

CREATE VIEW bugs_rt_affects_stable AS
SELECT id, package, source FROM bugs
WHERE affects_stable
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'lenny', 'wheezy', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'squeeze'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'squeeze-ignore')
AND id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='squeeze');

CREATE VIEW bugs_rt_affects_testing AS
SELECT id, package, source FROM bugs
WHERE affects_testing 
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sid', 'sarge', 'etch', 'lenny', 'squeeze', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'wheezy'))
AND id NOT IN (select id FROM bugs_tags WHERE tag = 'wheezy-ignore')
AND id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='wheezy');

CREATE VIEW bugs_rt_affects_unstable AS
SELECT id, package, source FROM bugs
WHERE affects_unstable 
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('lenny', 'sarge', 'etch', 'squeeze', 'wheezy', 'experimental'))
OR id IN (SELECT id FROM bugs_tags WHERE tag = 'sid'))
AND id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='sid');

CREATE VIEW bugs_rt_affects_testing_and_unstable AS
SELECT id, package, source FROM bugs
WHERE affects_unstable AND affects_testing
AND (id NOT IN (SELECT id FROM bugs_tags WHERE tag IN ('sarge', 'etch', 'lenny', 'squeeze', 'experimental'))
OR (id IN (SELECT id FROM bugs_tags WHERE tag = 'sid') AND id IN (SELECT id FROM bugs_tags WHERE tag = 'wheezy')))
AND id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='wheezy')
AND id in (select id from sources, bugs_packages where sources.source = bugs_packages.source and release='sid');

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
       package      text not null,
       release      text not null,
       component    text not null,
       language     text not null,
       description  text not null,
       long_description text not null,
       description_md5  text not null, -- md5 sum of the original English description
    PRIMARY KEY (package, release, component, language, description, description_md5)
);
GRANT SELECT ON descriptions TO PUBLIC;

CREATE TABLE ubuntu_descriptions (
       package      text not null,
       release      text not null,
       component    text not null,
       language     text not null,
       description  text not null,
       long_description text not null,
       description_md5  text not null, -- md5 sum of the original English description
    PRIMARY KEY (package, release, component, language, description, description_md5)
);
GRANT SELECT ON ubuntu_descriptions TO PUBLIC;

CREATE TABLE derivatives_descriptions (
       package      text not null,
       release      text not null,
       component    text not null,
       language     text not null,
       description  text not null,
       long_description text not null,
       description_md5  text not null, -- md5 sum of the original English description
    PRIMARY KEY (package, release, component, language, description, description_md5)
);
GRANT SELECT ON derivatives_descriptions TO PUBLIC;

-- Add house keeping table to enable deciding whether some translation file
-- was imported previousely and thus reducing workload on UDD host in
-- preventing doing duplicate work
CREATE TABLE description_imports (
    release                     text,
    component                   text,
    language                    text,
    translationfile             text,
    translationfile_sha1        text,
    import_date                 timestamp default now(),
    PRIMARY KEY (release, component, language)
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
drop view bapase;
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

DROP VIEW relevant_hints;
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
