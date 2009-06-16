-- http://screenshots.debian.net/json/screenshots

BEGIN;

DROP TABLE IF EXISTS screenshots CASCADE;

CREATE TABLE screenshots (
	package			text NOT NULL,
	version			text,
	homepage		text,
	maintainer_name		text,
	maintainer_email	text,
	description		text,
	section			text,
	screenshot_url		text NOT NULL,
	large_image_url		text NOT NULL,
	small_image_url		text NOT NULL,
    PRIMARY KEY (small_image_url)
);

GRANT SELECT ON screenshots TO PUBLIC;

COMMIT;

-- 'name'       --> 'package'
-- 'section'
-- 'maintainer' --> 'maintainer_name'
-- 'maintainer_email'
-- 'version'
-- 'homepage'
-- 'description'
-- 'url'	--> 'screenshot_url'
-- 'large_image_url'
-- 'small_image_url'
