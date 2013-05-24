DROP TABLE IF EXISTS blends_metadata CASCADE;
CREATE TABLE blends_metadata (
  -- fieldname   type,   --  example value
     blend       TEXT,   --  'debian-med'   (== the source package name)
     blendname   TEXT,   --  'Debian Med'   (== human readable name)
     projecturl  TEXT,   --  'http://debian-med.alioth.debian.org/'
     tasksprefix TEXT,   --  'med'
     homepage    TEXT,
     aliothurl   TEXT,
     projectlist TEXT,
     logourl     TEXT,
     outputdir   TEXT,
     datadir     TEXT,
     vcsdir      TEXT,
     css         TEXT,
     advertising TEXT,
     pkglist     TEXT,
     dehsmail    TEXT,
     PRIMARY KEY (blend)
);

GRANT SELECT ON blends_metadata TO PUBLIC;

DROP TABLE IF EXISTS blends_tasks;
CREATE TABLE blends_tasks (
  -- fieldname   type,    --  example value
     blend       TEXT REFERENCES blends_metadata,
     task        TEXT,    --  'bio'
     metapackage BOOLEAN, --  Some tasks should not end up in a metapackage
     PRIMARY KEY (blend, task)
);

GRANT SELECT ON blends_tasks TO PUBLIC;

DROP TABLE IF EXISTS blends_dependencies;
CREATE TABLE blends_dependencies (
  -- fieldname    type,
     blend        TEXT REFERENCES blends_metadata,
     task         TEXT, -- CHECK (task IN (SELECT task from blends_tasks)),
     package      TEXT,
     dependency   CHARACTER(1) CHECK (dependency IN ('d', 'i', 'r', 's')), -- Depends / Recommends / Suggests
     distribution TEXT CHECK (distribution IN ('debian', 'new', 'prospective', 'ubuntu', 'other')),
     component    TEXT CHECK (component IN ('main', 'contrib', 'non-free', 'universe', 'multiverse', 'restricted', 'local')),
     PRIMARY KEY (blend, task, package)
);

GRANT SELECT ON blends_dependencies TO PUBLIC;
