#!/usr/bin/ruby
require 'dbi'
require 'cgi'

tstart = Time::now

class Actions
  attr_reader :actions, :act_todo, :act_status, :act_comment
  def initialize
    @actions = []
    @act_status = ""
    @act_todo = false
    @act_comment = ""
  end

  def add(desc)
    desc.chomp!
    date, who, act, comment = desc.split(' ', 4)
    date = Date::parse(date)
    if act =~ /^(.+)\((.+)\)$/
      act_name, act_arg = $1, $2
      if [ 'PROP_RM', 'PROP_RM_O', 'PROP_O', 'O', 'REQ_RM', 'RM', 'SEC_RM', 'O_PROP_RM' ].include?(act_name)
        # FIXME check bug
      elsif act_name == 'WAIT'
        act_arg = act_arg.to_i
      else
        puts "Unknown action: #{act} (#{desc})"
      end
      @actions << [date, who, [act_name, act_arg], comment]
    elsif act == 'OK'
      act_name = 'OK'
      act_arg = nil
      @actions << [date, who, [act_name, act_arg], comment]
    else
      puts "Unparseable action: #{act} (#{desc})"
      exit(1)
    end
  end
 
  def analyze_actions
    @actions.sort! { |a,b| b[0] <=> a[0] }
    idx = 0
    rm_o = false
    while idx < @actions.length
      if @actions[idx][2][0] == 'OK'
        @act_status = ""
        @act_comment = @actions[idx][3] if not @actions[idx][3].nil?
        break
      elsif @actions[idx][2][0] == 'WAIT'
        if @actions[idx][0] + @actions[idx][2][1] <= CURDATE
          idx += 1
          next # OK not valid anymore, consider next action
        else
          # nothing to do except waiting
          @act_status = "Waiting until #{@actions[idx][0] + @actions[idx][2][1]}"
          @act_comment = @actions[idx][3] if not @actions[idx][3].nil?
          break
        end
      elsif @actions[idx][2][0] == 'REQ_RM' or @actions[idx][2][0] == 'RM'
        @act_status = "<a href=\"http://bugs.debian.org/#{@actions[idx][2][1]}\">Removal was requested</a>"
        @act_comment = @actions[idx][3] if not @actions[idx][3].nil?
        break
      elsif @actions[idx][2][0] == 'O'
        @act_status = "<a href=\"http://bugs.debian.org/#{@actions[idx][2][1]}\">Was orphaned</a>"
        @act_comment = @actions[idx][3] if not @actions[idx][3].nil?
        break
      elsif @actions[idx][2][0] == 'PROP_RM_O'
        @act_status = "<a href=\"http://bugs.debian.org/#{@actions[idx][2][1]}\">Was orphaned, will need removal</a>"
        rm_o = true
        idx += 1
        @act_comment = @actions[idx][3] if not @actions[idx][3].nil?
        next
      elsif @actions[idx][2][0] == 'PROP_RM'
        ok = false
        if @actions[idx][0] + WAIT_RM_O <= CURDATE and !rm_o
          @act_status = "<a href=\"http://bugs.debian.org/#{@actions[idx][2][1]}\">Should be orphaned before removal (since #{@actions[idx][0] + 50})</a>"
          @act_todo = true
          ok = true
        end
        if @actions[idx][0] + WAIT_RM_RM <= CURDATE
          @act_status = "<a href=\"http://bugs.debian.org/#{@actions[idx][2][1]}\">Should be removed (since #{@actions[idx][0] + 100})</a>"
          @act_todo = true
          ok = true
        end
        if !ok
          @act_status = "<a href=\"http://bugs.debian.org/#{@actions[idx][2][1]}\">Removal suggested (since #{@actions[idx][0]})</a>"
        end
        @act_comment = @actions[idx][3] if not @actions[idx][3].nil?
        break
      elsif @actions[idx][2][0] == 'PROP_O'
        if @actions[idx][0] + WAIT_O_O <= CURDATE
          @act_status = "<a href=\"http://bugs.debian.org/#{@actions[idx][2][1]}\">Should be orphaned (since #{@actions[idx][0] + 50})</a>"
          @act_todo = true
        else
          @act_status = "<a href=\"http://bugs.debian.org/#{@actions[idx][2][1]}\">Orphaning suggested (since #{@actions[idx][0]})</a>"
        end
        @act_comment = @actions[idx][3] if not @actions[idx][3].nil?
        break
      elsif @actions[idx][2][0] == 'O_PROP_RM'
        if @actions[idx][0] + WAIT_ORM_RM <= CURDATE
          @act_status = "<a href=\"http://bugs.debian.org/#{@actions[idx][2][1]}\">Should be removed (O pkg) (since #{@actions[idx][0] + 50})</a>"
          @act_todo = true
        else
          @act_status = "<a href=\"http://bugs.debian.org/#{@actions[idx][2][1]}\">Removal suggested (O pkg) (since #{@actions[idx][0]})</a>"
        end
        @act_comment = @actions[idx][3] if not @actions[idx][3].nil?
        break
      else
        puts "Unknown act: #{@actions[idx][2][0]}"
      end
    end
  end

  def Actions::fetch
    d = IO::popen("svn cat svn://svn.debian.org/collab-qa/bapase/package-actions.txt")
    f = d.read
    d.close
    return Actions::read(f)
  end

  def Actions::read(data)
    pkgs = {}
    data.each_line do |l|
      next if l =~/^\s*#/ or l =~/^\s*$/
      pkg, rest = l.split(' ',2)
      if pkgs[pkg].nil?
        pkgs[pkg] = Actions::new
      end
      pkgs[pkg].add(rest)
    end
    pkgs.each_pair { |k, v| v.analyze_actions }
  end
end

puts "Content-type: text/html\n\n"

WAIT_RM_O = 50
WAIT_RM_RM = 100
WAIT_O_O = 50
WAIT_ORM_RM = 50

DATEZERO = Date::parse('0000-01-01')
CURDATE = Date::today

dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
cgi = CGI.new

type = cgi.params['t']
if not type.nil?
  type = type[0]
end

if type == 'o'
  orphaned = true
  query = "select * from bapase where type is not null and type in ('O', 'ITA') order by orphaned_age desc"
elsif type == 'o2'
  orphaned = true
  query = "select * from bapase where type is not null and type in ('O', 'ITA') and orphaned_age >= 600 and orphaned_age < 730 and insts < 300 and last_modified_age > 60 order by last_modified_age desc"
elsif type == 'rfa'
  orphaned = true
  query = "select * from bapase where type is not null and type in ('RFA') order by orphaned_age desc"
elsif type == 'nmu'
  orphaned = true
  query = "select * from bapase where nmu and nmus > 1 order by nmus desc"
elsif type == 'testing'
  orphaned = true
  query = "select * from bapase where source not in (select source from sources where distribution='debian' and release='wheezy') order by testing_age desc, first_seen asc"
elsif type == 'nodd'
  orphaned = true
  query = <<EOF
WITH active_emails AS (SELECT email FROM carnivore_emails, active_dds WHERE active_dds.id = carnivore_emails.id)
select * from bapase where source in (
SELECT source
FROM sources
WHERE distribution = 'debian' AND release = 'sid'
AND sources.source NOT IN (
SELECT sources.source
FROM sources
LEFT OUTER JOIN uploaders ON (sources.source = uploaders.source AND sources.version = uploaders.version AND sources.distribution = uploaders.distribution AND sources.release = uploaders.release AND sources.component = uploaders.component)
WHERE sources.distribution = 'debian' AND sources.release = 'sid'
AND (maintainer_email in (select email from active_emails)
OR email in (SELECT email FROM active_emails)
OR maintainer_email ~ '.*@lists.(alioth.)?debian.org'
OR email ~ '.*@lists.(alioth.)?debian.org'))
) order by upload_age desc
EOF
elsif type == 'maintnmu'
  orphaned = true
  query = <<EOF
select * from bapase where source in (
  select source from sources where distribution='debian' and release='wheezy' and maintainer_email in (
select nmus.email from
(select email, count(*) as tot from
(select maintainer_email as email, source from sources_uniq
where release = 'sid'
and distribution = 'debian'
and component = 'main'
union
select email, source from uploaders 
where release = 'sid'
and distribution = 'debian'
and component = 'main') as foo
group by email) as tot,
(select email, count(*) as nmus from
(select sources.maintainer_email as email, sources.source from sources_uniq sources, upload_history uh
where release = 'sid'
and distribution = 'debian'
and component = 'main'
and sources.source = uh.source and sources.version = uh.version
and uh.nmu
union
select email, uploaders.source from uploaders, upload_history uh
where release = 'sid'
and distribution = 'debian'
and component = 'main'
and uploaders.source = uh.source and uploaders.version = uh.version
and uh.nmu
) as foo
group by email) as nmus
where nmus * 100 / tot >= 100
and nmus.email = tot.email)
union (select source from uploaders where distribution='debian' and release='wheezy' and email in (
select nmus.email from
(select email, count(*) as tot from
(select maintainer_email as email, source from sources_uniq sources
where release = 'sid'
and distribution = 'debian'
and component = 'main'
union
select email, source from uploaders 
where release = 'sid'
and distribution = 'debian'
and component = 'main') as foo
group by email) as tot,
(select email, count(*) as nmus from
(select sources.maintainer_email as email, sources.source from sources_uniq sources, upload_history uh
where release = 'sid'
and distribution = 'debian'
and component = 'main'
and sources.source = uh.source and sources.version = uh.version
and uh.nmu
union
select email, uploaders.source from uploaders, upload_history uh
where release = 'sid'
and distribution = 'debian'
and component = 'main'
and uploaders.source = uh.source and uploaders.version = uh.version
and uh.nmu
) as foo
group by email) as nmus
where nmus * 100 / tot >= 100
and nmus.email = tot.email
))) order by nmus
EOF
else
  puts <<-EOF
  <h1>Bapase</h1>
  <ul>
  <li><a href="bapase.cgi?t=o">Orphaned packages</a></li>
  <li><a href="bapase.cgi?t=rfa">RFAed packages</a></li>
  <li><a href="bapase.cgi?t=nmu">Packages maintained with NMUs</a></li>
  <li><a href="bapase.cgi?t=testing">Packages not in testing</a></li>
  <li><a href="bapase.cgi?t=nodd">Packages not maintained by DDs</a></li>
  <li><a href="bapase.cgi?t=maintnmu">Packages maintained or co-maintained by people with lots of NMUs</a></li>
  </ul>
  </body></html>
  EOF
  exit(0)
end

# FIXME add case where type is uknown

$actions = Actions::fetch

puts <<-EOF
<html><head>
<link rel="stylesheet" href="css/tablesorter/style.css" type="text/css" />
<script type="text/javascript" src="js/jquery.min.js"></script>
<script type="text/javascript" src="js/jquery.tablesorter.min.js"></script>
<script type="text/javascript">
    $(document).ready(function() {
        // call the tablesorter plugin
        $("table").tablesorter({
            // sort on the first column and third column, order asc
            // sortList: [[0,0],[2,0]]
            sortList: [[0,0]]
        });
    });
</script>
<title>Bapase</title>
</head><body>
<table class="tablesorter"><thead><tr>
<th></th><th>Package</th><th>Action</th>
EOF
puts "<th>Orphaned</th>" if orphaned
puts <<-EOF
<th>Testing</th>
<th>Migrate</th>
<th>Popcon</th>
<th>Bugs</th>
<th>Last upload</th>
<th>NMUs</th>
<th>Comments</th>
</tr></thead>
EOF
tqs = Time::now
sth = dbh.prepare(query)
sth.execute
tqe = Time::now
res = sth.fetch_all
n = 0
res.each do |r|
  n += 1
  pkg = r['source']
  puts "<tr><td>#{n}</td>"
  puts "<td><a href=\"http://packages.qa.debian.org/#{pkg}\">#{pkg}</a>"
  # FIXME removals
  if $actions[pkg]
    if $actions[pkg].act_todo
      puts "<td><b>#{$actions[pkg].act_status}</b></td>"
    else
      puts "<td>#{$actions[pkg].act_status}</td>"
    end
  else
    puts "<td></td>"
  end
  if orphaned
    if r['type']
      puts "<td><a href=\"http://bugs.debian.org/#{r['bug']}\">#{r['type']}</a>&nbsp;(#{r['orphaned_age']},&nbsp;#{r['last_modified_age']})</td>"
    else
      puts "<td></td>"
    end
  end
  if r['testing_age'] and r['testing_age'] > 1
    puts "<td>#{r['testing_age']}</td>"
  else
    puts "<td></td>"
  end
  if r['sync_age'] and r['sync_age'] > 1
    puts "<td>#{r['sync_age']}</td>"
  else
    puts "<td></td>"
  end
  puts "<td>#{r['insts']}&nbsp;/&nbsp;#{r['vote']}</td>"
  puts "<td><a href=\"http://bugs.debian.org/src:#{pkg}\">#{r['rc_bugs']}&nbsp;/&nbsp;#{r['all_bugs']}</a></td>"
  puts "<td>#{r['upload_age']}</td>"
  puts "<td>#{r['nmus']}</td>"
  if $actions[pkg]
    comment = $actions[pkg].act_comment.gsub(/#\d+/) do |bug|
      bugn = bug.gsub(/^#/, '')
      "<a href=\"http://bugs.debian.org/#{bugn}\">#{bug}</a>"
    end
    puts "<td>#{comment}</td>"
  else
    puts "<td></td>"
  end
  puts "</tr>"
end
puts "</table>"

tstop = Time::now
puts " -- #{res.length} packages listed. Page generated in #{tstop - tstart} seconds. Query took #{tqe - tqs} seconds."
puts "</body></html>"




#sth.finish
