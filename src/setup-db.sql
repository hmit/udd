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

CREATE TABLE popcon
  (Name text, vote int, olde int, recent int, nofiles int, UNIQUE (Name));

CREATE VIEW popcon_average AS
  SELECT sources.package, avg(vote) AS vote, avg(olde) AS old, avg(recent) AS recent, avg(nofiles) as nofiles
    FROM sources, popcon,
          (SELECT DISTINCT packages.package, packages.source FROM packages) as packages
    WHERE sources.release = 'sid' AND
          packages.source = sources.package AND
	  popcon.name = packages.package
    GROUP BY sources.package;


CREATE VIEW popcon_max AS
  SELECT sources.package, max(vote) AS vote, max(olde) AS old, max(recent) AS recent, max(nofiles) as nofiles
    FROM sources, popcon, packages
    WHERE sources.release = 'sid' AND
          packages.source = sources.package AND
	  popcon.name = packages.package
    GROUP BY sources.package;


CREATE INDEX pkgs_name_idx ON Packages (Package);
CREATE INDEX sources_id_idx ON sources (Package);
CREATE INDEX pkgs_src_id_idx ON Packages USING btree (Source);
CREATE INDEX popcon_name_idx ON popcon (name);
CREATE INDEX sources_distribution_idx on sources(distribution);
CREATE INDEX sources_release_idx on sources(release);
CREATE INDEX sources_component_idx on sources(component);

GRANT SELECT ON Packages TO PUBLIC;
GRANT SELECT ON sources TO PUBLIC;
GRANT SELECT ON popcon TO PUBLIC;

GRANT SELECT ON popcon_average TO PUBLIC;
GRANT SELECT ON popcon_sum TO PUBLIC;
