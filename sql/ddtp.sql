-- DDTP Translations

BEGIN;

CREATE TABLE ddtp (
       package      text,
       distribution text,
       release      text,
       component    text,   -- == 'main' for the moment
       version      text,   -- different versions for a package might exist because some archs
                            -- might have problems with newer versions if a new version comes
                            -- with a new description we might have different translations for
                            -- a (package, distribution, release, component, language) key so
                            -- we also need to store the version number of a package translation
                            -- In case there are different versions with an identical description
                            -- this field will hold the highest version number according to
                            -- dpkg --compare-versions
       language     text,
       description  text,
       long_description text,
       md5sum       text,   -- md5 sum of the original English description as it is used
                            -- in DDTP.  This is obtained via
                            --   md5(description || E'\n' || long_description || E'\n')
                            -- from packages table
    PRIMARY KEY (package, distribution, release, component, version, language)
);


COMMIT;

