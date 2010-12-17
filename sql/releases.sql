/****************************************************************************************
 * This table enables sorting of releases according to their release date.  To define   *
 * a reasonable order also for releases which are not or never will be released an      *
 * additional column sort is defined.                                                   *
 * The relevant discussion can be found here:                                           *
 *   http://lists.debian.org/debian-qa/2010/02/msg00001.html                            *
 ****************************************************************************************/

CREATE TABLE releases (
       release     text,  /* keep name column as in other tables */
       releasedate date,
       sort        int,
       PRIMARY KEY (release)
);

INSERT INTO releases VALUES ( 'etch',                     '2007-04-08', 400 );
INSERT INTO releases VALUES ( 'etch-security',            '2007-04-08', 401 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'etch-proposed-updates',    '2007-04-08', 402 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'lenny',                    '2009-02-14', 500 );
INSERT INTO releases VALUES ( 'lenny-security',           '2009-02-14', 501 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'lenny-proposed-updates',   '2009-02-14', 502 ); /* date or NULL ?? */
INSERT INTO releases VALUES ( 'squeeze',                  NULL,         600 );
INSERT INTO releases VALUES ( 'squeeze-security',         NULL,         601 );
INSERT INTO releases VALUES ( 'squeeze-proposed-updates', NULL,         602 );
INSERT INTO releases VALUES ( 'sid',                      NULL,      100000 );
INSERT INTO releases VALUES ( 'experimental',             NULL,      100001 );

GRANT SELECT ON releases TO PUBLIC ;

