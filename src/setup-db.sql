CREATE TABLE Packages
  (Package text, Version text, Architecture text, Maintainer text, Description
    text, Source text, Source_version text, Essential text, Depends text,
    Recommends text, Suggests text, Enhances text, Pre_Depends text,
    Installed_Size int, Homepage text, Size int, MD5Sum text, Distribution
    text, Release text, Component text,
  PRIMARY KEY (Package, Version, Architecture, Distribution, Release, Component));

CREATE TABLE sources
  (Package text, Version text, Maintainer text, Format text, Files text,
    Uploaders text, Bin text, Architecture text, Standards_Version text,
    Homepage text, Build_Depends text, Build_Depends_Indep text,
    Build_Conflicts text, Build_Conflicts_Indep text, Priority text, Section
    text, Distribution text, Release text, Component text, Vcs_Arch text,
    Vcs_Browser text, Vcs_Bzr text, Vcs_Cvs text, Vcs_Darcs text, Vcs_Git text,
    Vcs_Hg text, Vcs_Svn text, X_Vcs_Browser text, X_Vcs_Bzr text, X_Vcs_Darcs
    text, X_Vcs_Svn text,
    PRIMARY KEY (package, version, distribution, release, component));

CREATE TABLE migrations
  (source text PRIMARY KEY, in_testing date, testing_version text, in_unstable date, unstable_version text, sync date, sync_version text, first_seen date);

CREATE TABLE popcon (
   package text, insts int, vote int, olde int, recent int, nofiles int,
   distribution text,
   PRIMARY KEY (package, distribution));

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

CREATE VIEW popcon_src_average AS
  SELECT packages.package, avg(insts) AS insts, avg(vote) AS vote, avg(olde) AS old, avg(recent) AS recent, avg(nofiles) as nofiles, packages.distribution
    FROM popcon,
          (SELECT DISTINCT packages.package, packages.source, packages.distribution FROM packages) as packages
    WHERE 
	  popcon.package = packages.package AND
	  popcon.distribution = packages.distribution
    GROUP BY packages.source, packages.distribution, packages.package;

CREATE VIEW popcon_src_max AS
  SELECT packages.package, max(insts) AS insts, max(vote) AS vote, max(olde) AS old, max(recent) AS recent, max(nofiles) as nofiles, packages.distribution
    FROM popcon,
          (SELECT DISTINCT packages.package, packages.source, packages.distribution FROM packages) as packages
    WHERE 
	  popcon.package = packages.package AND
	  popcon.distribution = packages.distribution
    GROUP BY packages.source, packages.distribution, packages.package;

CREATE INDEX packages_source_idx on packages(source);
CREATE INDEX sources_distribution_idx on sources(distribution);
CREATE INDEX sources_release_idx on sources(release);
CREATE INDEX sources_component_idx on sources(component);

GRANT SELECT ON Packages TO PUBLIC;
GRANT SELECT ON sources TO PUBLIC;
GRANT SELECT ON popcon TO PUBLIC;
GRANT SELECT ON popcon_src_average TO PUBLIC;
GRANT SELECT ON popcon_src_max TO PUBLIC;
GRANT SELECT ON bugs TO PUBLIC;
GRANT SELECT ON bugs_archived TO PUBLIC;
GRANT SELECt ON bugs_unarchived TO PUBLIC;
GRANT SELECT ON bug_merged_with TO PUBLIC;
GRANT SELECT ON bug_found_in TO PUBLIC;
GRANT SELECT ON bug_fixed_in TO PUBLIC;
GRANT SELECT ON bug_user_tags TO PUBLIC;

