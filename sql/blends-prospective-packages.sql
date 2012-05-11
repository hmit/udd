DROP TABLE IF EXISTS blends_prospectivepackages CASCADE;

CREATE TABLE blends_prospectivepackages
  (blend text,
   package text,
   source text,
   maintainer text,
   maintainer_name text,
   maintainer_email text,
   changed_by text,
   changed_by_name text,
   changed_by_email text,
   uploaders text,
   description text,
   long_description text,
   description_md5 text,
   homepage text,
   section text,
   priority text,
   vcs_type text,
   vcs_url text,
   vcs_browser text,
   wnpp int,
   wnpp_type text,
   wnpp_desc text,
   license text,
   chlog_date text, -- time,
   chlog_version debversion
);

