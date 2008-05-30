CREATE TABLE pkgs (pkg_id serial, name text, distr_id int, arch_id int, version text, src_id int);
CREATE TABLE sources (src_id serial, name text, upload_date timestamp, uploader_key int, maintainer int, build_archs int, version text, distr_id int);
CREATE TABLE distr_ids (distr_id serial, name text);
CREATE TABLE arch_ids (arch_id serial, name text);

GRANT SELECT ON pkgs TO PUBLIC;
GRANT SELECT ON sources TO PUBLIC;
GRANT SELECT ON distr_ids TO PUBLIC;
GRANT SELECT ON arch_ids TO PUBLIC;
