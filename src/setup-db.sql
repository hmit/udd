CREATE TABLE pkgs (pkg_id serial, name text, distr_id int, arch_id int, version text, src_id int, UNIQUE (name, distr_id, arch_id, version));
CREATE TABLE sources (src_id serial, name text, upload_date timestamp, uploader_key int, maintainer text, version text, distr_id int, UNIQUE (name, version, distr_id));
CREATE TABLE distr_ids (distr_id serial, name text);
CREATE TABLE arch_ids (arch_id serial, name text);
CREATE TABLE build_archs (src_id int, arch_id int);

CREATE INDEX pkgs_id_idx ON pkgs (pkg_id);
CREATE INDEX pkgs_name_idx ON pkgs (name);
CREATE INDEX sources_id_idx ON sources (src_id);
CREATE INDEX sources_name_idx ON sources (name);
CREATE INDEX arch_id_idx ON arch_ids using btree (arch_id);
CREATE INDEX pkgs_src_id_idx ON pkgs USING btree (srd_id);

GRANT SELECT ON pkgs TO PUBLIC;
GRANT SELECT ON sources TO PUBLIC;
GRANT SELECT ON distr_ids TO PUBLIC;
GRANT SELECT ON arch_ids TO PUBLIC;
GRANT SELECT ON build_archs TO PUBLIC;
