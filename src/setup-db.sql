CREATE TABLE packages
  (package text, version text, architecture text, maintainer text, description
    text, source text, source_version text, essential text, depends text,
    recommends text, suggests text, enhances text, pre_depends text,
    installed_size int, homepage text, size int,
    build_essential text, origin text, sha1 text, replaces text, section text,
    md5sum text, bugs text, priority text, tag text, task text, python_version text,
    provides text, conflicts text, sha256 text, original_maintainer text,
    distribution text, release text, component text,
  PRIMARY KEY (package, version, architecture, distribution, release, component));

CREATE TABLE ubuntu_packages
  (package text, version text, architecture text, maintainer text, description
    text, source text, source_version text, essential text, depends text,
    recommends text, suggests text, enhances text, pre_depends text,
    installed_size int, homepage text, size int,
    build_essential text, origin text, sha1 text, replaces text, section text,
    md5sum text, bugs text, priority text, tag text, task text, python_version text,
    provides text, conflicts text, sha256 text, original_maintainer text,
    distribution text, release text, component text,
  PRIMARY KEY (package, version, architecture, distribution, release, component));

CREATE TABLE sources
  (package text, version text, maintainer text, format text, files text,
    uploaders text, bin text, architecture text, standards_version text,
    homepage text, build_depends text, build_depends_indep text,
    build_conflicts text, build_conflicts_indep text, priority text, section
    text, distribution text, release text, component text, vcs_type text,
    vcs_url text, vcs_browser text,
    python_version text, checksums_sha1 text, checksums_sha256 text,
    original_maintainer text, dm_upload_allowed text,
    PRIMARY KEY (package, version, distribution, release, component));

CREATE TABLE ubuntu_sources
  (package text, version text, maintainer text, format text, files text,
    uploaders text, bin text, architecture text, standards_version text,
    homepage text, build_depends text, build_depends_indep text,
    build_conflicts text, build_conflicts_indep text, priority text, section
    text, distribution text, release text, component text, vcs_type text,
    vcs_url text, vcs_browser text,
    python_version text, checksums_sha1 text, checksums_sha256 text,
    original_maintainer text, dm_upload_allowed text,
    PRIMARY KEY (package, version, distribution, release, component));

CREATE TABLE migrations
  (source text PRIMARY KEY, in_testing date, testing_version text, in_unstable date, unstable_version text, sync date, sync_version text, first_seen date);

CREATE TABLE popcon (
   package text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (package));
 
CREATE TABLE popcon_src (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));

CREATE TABLE popcon_src_average (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));

CREATE TABLE ubuntu_popcon (
   package text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (package));
 
CREATE TABLE ubuntu_popcon_src (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));

CREATE TABLE ubuntu_popcon_src_average (
   source text, insts int, vote int, olde int, recent int, nofiles int,
   PRIMARY KEY (source));

CREATE TABLE bugs_unarchived
  (id int PRIMARY KEY, package text, source text, arrival timestamp, status text,
     severity text, submitter text, owner text, title text,
     last_modified timestamp, affects_stable boolean,
    affects_testing boolean, affects_unstable boolean);

CREATE TABLE bugs_archived
  (id int PRIMARY KEY, package text, source text, arrival timestamp, status text,
     severity text, submitter text, owner text, title text,
     last_modified timestamp, affects_stable boolean,
    affects_testing boolean, affects_unstable boolean);

CREATE TABLE bug_merged_with
  (id int, merged_with int,
PRIMARY KEY(id, merged_with));

CREATE TABLE bug_user_tags
  (email text, tag text, id int);

CREATE TABLE bug_found_in
  (id int, version text,
   PRIMARY KEY(id, version));

CREATE TABLE bug_fixed_in
  (id int, version text,
   PRIMARY KEY(id, version));

CREATE TABLE bug_tags
  (id int, tag text, PRIMARY KEY (id, tag));

CREATE VIEW bugs AS
  SELECT id, package, source, arrival, status, severity, submitter, owner,
        title, last_modified, affects_stable, affects_testing,
	affects_unstable, TRUE as is_archived
  FROM bugs_archived
  UNION
  SELECT id, package, source, arrival, status, severity, submitter, owner,
	title, last_modified, affects_stable, affects_testing,
	affects_unstable, FALSE as is_archived FROM bugs_unarchived;

CREATE TABLE upload_history
 (package text, version text, date timestamp with time zone, changed_by text,
  maintainer text, nmu boolean, signed_by text, key_id text);

CREATE INDEX packages_source_idx on packages(source);
CREATE INDEX packages_distrelcomp_idx on packages(distribution, release, component);
CREATE INDEX sources_distrelcomp_idx on sources(distribution, release, component);

CREATE INDEX ubuntu_packages_source_idx on ubuntu_packages(source);
CREATE INDEX ubuntu_packages_distrelcomp_idx on packages(distribution, release, component);
CREATE INDEX ubuntu_sources_distrelcomp_idx on ubuntu_sources(distribution, release, component);

GRANT SELECT ON packages TO PUBLIC;
GRANT SELECT ON sources TO PUBLIC;
GRANT SELECT ON ubuntu_Packages TO PUBLIC;
GRANT SELECT ON ubuntu_sources TO PUBLIC;
GRANT SELECT ON popcon TO PUBLIC;
GRANT SELECT ON popcon_src_average TO PUBLIC;
GRANT SELECT ON popcon_src TO PUBLIC;
GRANT SELECT ON ubuntu_popcon TO PUBLIC;
GRANT SELECT ON ubuntu_popcon_src_average TO PUBLIC;
GRANT SELECT ON ubuntu_popcon_src TO PUBLIC;
GRANT SELECT ON bugs TO PUBLIC;
GRANT SELECT ON bugs_archived TO PUBLIC;
GRANT SELECt ON bugs_unarchived TO PUBLIC;
GRANT SELECT ON bug_merged_with TO PUBLIC;
GRANT SELECT ON bug_found_in TO PUBLIC;
GRANT SELECT ON bug_fixed_in TO PUBLIC;
GRANT SELECT ON bug_user_tags TO PUBLIC;

