BEGIN;

DROP TABLE IF EXISTS bibref CASCADE;

CREATE TABLE bibref (
	source	text NOT NULL,
	key	text NOT NULL,
	value	text NOT NULL,
	package text DEFAULT '',
	rank    int  NOT NULL,
	PRIMARY KEY (source,key,package,rank) -- this helps preventing more than one times the same key for a single package
);

GRANT SELECT ON bibref TO PUBLIC;

COMMIT;

