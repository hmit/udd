#!/bin/sh

set -e

BUGSDUMP=/srv/udd.debian.org/mirrors/clone-bugs/udd-bugs.sql.gz

unset LANG
unset LC_ALL

psql --quiet udd 2>/dev/null <<EOT
DROP TABLE IF EXISTS bugs_blockedby;
DROP TABLE IF EXISTS bugs_fixed_in;
DROP TABLE IF EXISTS bugs_found_in;
DROP VIEW  IF EXISTS bapase ;
DROP VIEW  IF EXISTS bugs_count ;
DROP TABLE IF EXISTS bugs_merged_with;
DROP VIEW  IF EXISTS bugs_rt_affects_stable;
DROP VIEW  IF EXISTS bugs_rt_affects_testing;
DROP VIEW  IF EXISTS bugs_rt_affects_testing_and_unstable;
DROP VIEW  IF EXISTS bugs_rt_affects_unstable;
DROP VIEW  IF EXISTS bugs_rt_affects_oldstable;
DROP TABLE IF EXISTS bugs_packages;
DROP TABLE IF EXISTS bugs_blocks;
DROP TABLE IF EXISTS bugs_tags;
DROP VIEW  IF EXISTS all_bugs ;
DROP TABLE IF EXISTS bugs;
DROP TABLE IF EXISTS bugs_usertags;
EOT

zcat $BUGSDUMP | psql --quiet udd

# recreate lost views
psql --quiet udd <<EOT
CREATE VIEW all_bugs AS
   SELECT id, package, source, arrival, status, severity,
       submitter, submitter_name, submitter_email,
       owner, owner_name, owner_email,
       done, done_name, done_email, done_date,
       title, last_modified, forwarded,
       affects_oldstable, affects_stable, affects_testing, affects_unstable, affects_experimental
     FROM bugs
   UNION ALL
   SELECT id, package, source, arrival, status, severity,
       submitter, submitter_name, submitter_email,
       owner, owner_name, owner_email,
       done, done_name, done_email, done_date,
       title, last_modified, forwarded,
       affects_oldstable, affects_stable, affects_testing, affects_unstable, affects_experimental
     FROM archived_bugs;

GRANT SELECT ON all_bugs TO PUBLIC;

create view bugs_count as
select coalesce(b1.source, b2.source) as source, coalesce(rc_bugs, 0) as rc_bugs, coalesce(all_bugs, 0) as all_bugs from
((select source, count(*) as rc_bugs
from bugs
where severity >= 'serious'
and status='pending'
and id not in (select id from bugs_merged_with where id > merged_with)
group by source) b1
FULL JOIN (select source, count(*) as all_bugs
from bugs
where status='pending'
and id not in (select id from bugs_merged_with where id > merged_with)
group by source) b2 ON (b1.source = b2.source));
                                                                                          
grant select on bugs_count to public;

create view bapase as
select s.source, s.version, type, bug, description,
orphaned_time, (current_date - orphaned_time::date) as orphaned_age,
in_testing, (current_date - in_testing) as testing_age, testing_version,
in_unstable, (current_date - in_unstable) as unstable_age, unstable_version,
sync, (current_date - sync) as sync_age, sync_version,
first_seen, (current_date - first_seen) as first_seen_age,
uh.date as upload_date, (current_date - uh.date::date) as upload_age,
nmu, coalesce(nmus, 0) as nmus, coalesce(rc_bugs,0) as rc_bugs, coalesce(all_bugs,0) as all_bugs,
coalesce(insts,0) as insts, coalesce(vote,0) as vote, s.maintainer, bugs.last_modified,
(current_date - bugs.last_modified::date) as last_modified_age
from sources_uniq s
left join orphaned_packages op on s.source = op.source
left join migrations tm on s.source = tm.source
left join  upload_history uh on s.source = uh.source and s.version = uh.version
left join  upload_history_nmus uhn on s.source = uhn.source
left join bugs_count b on s.source = b.source
left join popcon_src ps on s.source = ps.source
left join bugs on op.bug = bugs.id
where s.distribution='debian' and s.release='sid';
GRANT SELECT ON bapase TO PUBLIC;

EOT
