CREATE TABLE blends_metadata (
  -- fieldname   type,   --  example value
     blend       TEXT,   --  'debian-med'   (== the source package name)
     blendname   TEXT,   --  'Debian Med'   (== human readable name)
     projecturl  TEXT,   --  'http://debian-med.alioth.debian.org/'
     tasksprefix TEXT,   --  'med'
     PRIMARY KEY (blend)
);

GRANT SELECT ON blends_metadata TO PUBLIC;

CREATE TABLE blends_tasks (
  -- fieldname   type,   --  example value
     blend       TEXT REFERENCES blends_metadata,
     task        TEXT,   --  'bio'
     PRIMARY KEY (blend, task)
);

GRANT SELECT ON blends_tasks TO PUBLIC;

CREATE TABLE blends_dependencies (
  -- fieldname    type,
     blend        TEXT REFERENCES blends_metadata,
     task         TEXT, -- CHECK (task IN (SELECT task from blends_tasks)),
     package      TEXT,
     dependency   CHARACTER(1) CHECK (dependency IN ('d', 's')), -- Depends / Suggests
     distribution TEXT CHECK (distribution IN ('debian', 'prospective', 'ubuntu', 'other')),
     PRIMARY KEY (blend, task, package)
);

GRANT SELECT ON blends_dependencies TO PUBLIC;
