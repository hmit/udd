BEGIN;

DROP TABLE IF EXISTS bibref CASCADE;

CREATE TABLE bibref (
	source	text NOT NULL,
	key	text NOT NULL,
	value	text NOT NULL,
	rank    int  NOT NULL,
	PRIMARY KEY (source,key,rank) -- this helps preventing more than one times the same key for a single package
);

GRANT SELECT ON bibref TO PUBLIC;

COMMIT;

