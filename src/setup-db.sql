CREATE TABLE Packages
  (Package text, Version text, Architecture text, Maintainer text, Description
    text, Source text, Source_version text, Essential text, Depends text,
    Recommends text, Suggests text, Enhances text, Pre_Depends text,
    Installed_Size int, Homepage text, Size int, MD5Sum text, Distribution
    text, Release text, Component text,
  UNIQUE (Package, Version, Architecture, Distribution, Release, Component));

CREATE TABLE sources
  (Package text, Version text, Maintainer text, Format text, Files text,
    Uploaders text, Bin text, Architecture text, Standards_Version text,
    Homepage text, Build_Depends text, Build_Depends_Indep text,
    Build_Conflicts text, Build_Conflicts_Indep text, Priority text, Section
    text, Distribution text, Release text, Component text, Vcs_Arch text,
    Vcs_Browser text, Vcs_Bzr text, Vcs_Cvs text, Vcs_Darcs text, Vcs_Git text,
    Vcs_Hg text, Vcs_Svn text, X_Vcs_Browser text, X_Vcs_Bzr text, X_Vcs_Darcs
    text, X_Vcs_Svn text,
    UNIQUE (package, version, distribution, release, component));

CREATE TABLE migrations
  (package text, in_testing date, testing_version text, in_unstable date, unstable_version text, sync date, sync_version text, first_seen date,
  UNIQUE (package));

CREATE TABLE popcon
  (Name text, insts int, vote int, olde int, recent int, nofiles int, distribution text, UNIQUE (Name, distribution));

CREATE TABLE bugs
  (id int, package text, source text, arrival timestamp, status text,
     severity text, tags text, submitter text, owner text, title text,
     last_modified timestamp, affects_stable boolean,
    affects_testing boolean, affects_unstable boolean, UNIQUE (id), is_archived boolean);

CREATE TABLE bug_merged_with
  (bug int, merged_with int);

CREATE TABLE bug_user_tags
  (bug_user text, tag text, bug_nr text);

CREATE TABLE bug_found_in
  (id int, version text);

CREATE TABLE bug_fixed_in
  (id int, version text);

CREATE TABLE upload_history
 (package text, version text, date timestamp with time zone, changed_by text, maintainer text, nmu boolean, signed_by text, key_id text);

CREATE VIEW popcon_src_average AS
  SELECT sources.package, avg(insts), avg(vote) AS vote, avg(olde) AS old, avg(recent) AS recent, avg(nofiles) as nofiles, sources.distribution
    FROM sources, popcon,
          (SELECT DISTINCT packages.package, packages.source, packages.distribution FROM packages) as packages
    WHERE 
          packages.source = sources.package AND
	  packages.distribution = sources.distribution AND
	  popcon.name = packages.package AND
	  popcon.distribution = sources.distribution
    GROUP BY sources.package, sources.distribution;

CREATE VIEW popcon_src_max AS
  SELECT sources.package, max(insts), max(vote) AS vote, max(olde) AS old, max(recent) AS recent, max(nofiles) as nofiles, sources.distribution
    FROM sources, popcon,
          (SELECT DISTINCT packages.package, packages.source, packages.distribution FROM packages) as packages
    WHERE 
          packages.source = sources.package AND
	  packages.distribution = sources.distribution AND
	  popcon.name = packages.package AND
	  popcon.distribution = sources.distribution
    GROUP BY sources.package, sources.distribution;

CREATE INDEX pkgs_src_id_idx ON Packages USING btree (Source);
CREATE INDEX sources_distribution_idx on sources(distribution);
CREATE INDEX sources_release_idx on sources(release);
CREATE INDEX sources_component_idx on sources(component);

GRANT SELECT ON Packages TO PUBLIC;
GRANT SELECT ON sources TO PUBLIC;
GRANT SELECT ON popcon TO PUBLIC;
GRANT SELECT ON popcon_src_average TO PUBLIC;
GRANT SELECT ON popcon_src_max TO PUBLIC;
GRANT SELECT ON bugs TO PUBLIC;
GRANT SELECT ON bug_merged_with TO PUBLIC;
GRANT SELECT ON bug_found_in TO PUBLIC;
GRANT SELECT ON bug_fixed_in TO PUBLIC;
GRANT SELECT ON bug_user_tags TO PUBLIC;

