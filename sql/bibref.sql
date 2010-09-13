-- http://upstream-metadata.debian.net/for_UDD/biblio.yaml

BEGIN;

DROP TABLE IF EXISTS bibref CASCADE;

CREATE TABLE bibref (
	package			text NOT NULL,
	key			text NOT NULL,
	value			text NOT NULL
);

GRANT SELECT ON bibref TO PUBLIC;

COMMIT;

-- 'name'       --> 'package'
-- 'section'
-- 'maintainer'
-- 'maintainer_email'
-- 'version'
-- 'homepage'
-- 'description'
-- 'url'
-- 'large_image_url'
-- 'small_image_url'