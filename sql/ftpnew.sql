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

