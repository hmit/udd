/* The upload-history importer failed to parse some e-mail addresses.
   This was fixed later but it might be reasonable not to restart the
   complete import process.  This code has the same effect inside the
   production database
 */
BEGIN;
UPDATE upload_history SET changed_by_name = regexp_replace(changed_by, E'^[^\\w]*\([^<]\+[.\\w]\) *<[.\\w]\+@[.\\w]\+>.*', E'\\1')
        WHERE changed_by_email NOT LIKE '%@%'
          AND changed_by       LIKE '%<%@%.%>%'
;
UPDATE upload_history SET changed_by_email = regexp_replace(changed_by, E'^[^<]\+<\([.\\w]\+@[.\\w]\+\)>.*', E'\\1')
        WHERE changed_by_email NOT LIKE '%@%'
          AND changed_by       LIKE '%<%@%.%>%'
;
/*
SELECT changed_by, changed_by_name, changed_by_email,
       regexp_replace(changed_by, E'^[^<]\+<\([.\\w]\+@[.\\w]\+\)>.*', E'\\1') AS changed_by_email_new,
       regexp_replace(changed_by, E'^[^\\w]*\([^<]\+[.\\w]\) *<[.\\w]\+@[.\\w]\+>.*', E'\\1') AS changed_by_name_new
  FROM upload_history
 WHERE changed_by_email NOT LIKE '%@%'
   AND changed_by       LIKE '%<%@%.%>%'
;
*/
UPDATE upload_history SET maintainer_name = regexp_replace(maintainer, E'^[^\\w]*\([^<]\+[.\\w]\) *<[.\\w]\+@[.\\w]\+>.*', E'\\1')
        WHERE maintainer_email NOT LIKE '%@%'
          AND maintainer       LIKE '%<%@%.%>%'
;
UPDATE upload_history SET maintainer_email = regexp_replace(maintainer, E'^[^<]\+<\([.\\w]\+@[.\\w]\+\)>.*', E'\\1')
        WHERE maintainer_email NOT LIKE '%@%'
          AND maintainer       LIKE '%<%@%.%>%'
;
/*
SELECT maintainer, maintainer_name, maintainer_email,
       regexp_replace(maintainer, E'^[^<]\+<\([.\\w]\+@[.\\w]\+\)>.*', E'\\1') AS maintainer_email_new,
       regexp_replace(maintainer, E'^[^\\w]*\([^<]\+[.\\w]\) *<[.\\w]\+@[.\\w]\+>.*', E'\\1') AS maintainer_name_new
  FROM upload_history
 WHERE maintainer_email NOT LIKE '%@%'
   AND maintainer       LIKE '%<%@%.%>%'
;
*/
COMMIT;
