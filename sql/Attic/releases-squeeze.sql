/****************************************************************************************
 * Update releases table after Squeeze release                                          *
 ****************************************************************************************/

BEGIN;
UPDATE releases SET releasedate = '2011-02-06' WHERE release = 'squeeze';
UPDATE releases SET releasedate = '2011-02-06' WHERE release = 'squeeze-security';
UPDATE releases SET releasedate = '2011-02-06' WHERE release = 'squeeze-proposed-updates';

INSERT INTO releases VALUES ( 'wheezy',                  NULL,         700 );
INSERT INTO releases VALUES ( 'wheezy-security',         NULL,         701 );
INSERT INTO releases VALUES ( 'wheezy-proposed-updates', NULL,         702 );
COMMIT;