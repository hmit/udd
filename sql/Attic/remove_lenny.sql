BEGIN;
DELETE FROM packages     WHERE release LIKE 'lenny%' ;
DELETE FROM sources      WHERE release LIKE 'lenny%' ;
DELETE FROM descriptions WHERE release LIKE 'lenny%' ;
COMMIT;
