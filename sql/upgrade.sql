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
