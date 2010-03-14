-- Applications containing po files
-- PO: field
CREATE TABLE i18n_apps (
    package         text,
    version         debversion,
    release         text,
    maintainer      text,
    po_file         text,
      -- *.pot ignorieren!
    language        text,
    pkg_version_lang text, -- no idea what sense this field makes
    last_translator text,
    language_team   text,
    translated      int,
    fuzzy           int,
    untranslated    int,
    PRIMARY KEY (package, version, release, language)
);

-- Packages containing debconf translation in po files
-- PODEBCONF: field
CREATE TABLE po_debconf (
    package         text,
    version         debversion,
    release         text,
    maintainer      text,
    po_file         text,
      -- *.pot ignorieren!
    language        text,
    ID              text,  -- no idea what this field means
    pkg_version_lang text, -- no idea what sense this field makes
    last_translator text,
    language_team   text,
    translated      int,
    fuzzy           int,
    untranslated    int,
    PRIMARY KEY (package, version, release, language)
);

