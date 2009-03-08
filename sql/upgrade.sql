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
