# 2008-09-22: Change severity from text to bugs_severity enum:
CREATE TYPE bugs_severity AS ENUM ('fixed', 'wishlist', 'minor', 'normal', 'important', 'serious', 'grave', 'critical');
ALTER TABLE bugs add severity2 bugs_severity;
update bugs set severity2 = severity::bugs_severity;
ALTER TABLE bugs drop severity;
ALTER TABLE bugs rename severity2 to severity;

# 2008-09-22: Add a affects_experimental to bugs and archived_bugs
ALTER TABLE bugs add affects_experimental boolean;
ALTER TABLE archived_bugs add affects_experimental boolean;
