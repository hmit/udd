#!/usr/bin/ruby -w

require 'dbi'
require 'pp'
require 'cgi'
require 'time'

puts "Content-type: text/html\n\n"

TESTING='wheezy'

$dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
$dbh.execute("SET statement_timeout TO 90000")

def getcount(q)
  begin
    sth = $dbh.prepare(q)
    sth.execute
    rows = sth.fetch_all
    return rows[0][0]
  rescue DBI::ProgrammingError => e
    puts "<p>The query generated an error, please report it to lucas@debian.org: #{e.message}</p>"
    puts "<pre>#{q}</pre>"
    exit(0)
  end
end

q = <<-EOF
select count(*) from bugs 
where status != 'done'
and not (id in (select id from bugs_merged_with where id > merged_with)) 
AND (severity >= 'serious')
EOF
tot = getcount(q)
q = <<-EOF
select count(id) from bugs 
where id in (select id from bugs_rt_affects_testing)
and not (id in (select id from bugs_merged_with where id > merged_with)) 
AND (severity >= 'serious')
EOF
wheezy = getcount(q)

q = <<-EOF
select count(id) from bugs 
where id in (select id from bugs_rt_affects_testing) and id in (select id from bugs_rt_affects_unstable) 
and not (id in (select id from bugs_merged_with where id > merged_with)) 
AND (severity >= 'serious')
EOF
wheezy_sid = getcount(q)
q = <<-EOF
select count(id) from bugs 
where id in (select id from bugs_rt_affects_testing) and id not in (select id from bugs_rt_affects_unstable) 
and not (id in (select id from bugs_merged_with where id > merged_with)) 
AND (severity >= 'serious')
EOF
wheezy_only = getcount(q)

q = <<-EOF
select count(id) from bugs 
where id in (select id from bugs_rt_affects_testing) and id in (select id from bugs_rt_affects_unstable) 
and id in (select id from bugs_tags where tag='patch') 
and not (id in (select id from bugs_merged_with where id > merged_with)) 
AND (severity >= 'serious')
EOF
wh_patch = getcount(q)

q = <<-EOF
select count(id) from bugs 
where id in (select id from bugs_rt_affects_testing) and id in (select id from bugs_rt_affects_unstable) 
and status = 'done'
and not (id in (select id from bugs_merged_with where id > merged_with)) 
AND (severity >= 'serious')
EOF
wh_done = getcount(q)

q = <<-EOF
select count(id) from bugs 
where id in (select id from bugs_rt_affects_testing) and id in (select id from bugs_rt_affects_unstable) 
and not (id in (select id from bugs_tags where tag='patch'))
and status != 'done'
and not (id in (select id from bugs_merged_with where id > merged_with)) 
AND (severity >= 'serious')
EOF
wh_neither = getcount(q)

week = Time.now.strftime('%V')
puts <<-EOF
<html><body>
<h1>Release Critical Bug report for Week #{week}</h1>

<p>The <a href="http://udd.debian.org/bugs.cgi">UDD bugs interface</a> currently knows about the following release critical bugs:</p>

<ul>
 <li>
 <strong>In Total: <a href="http://udd.debian.org/bugs.cgi?release=any&merged=ign&rc=1">#{tot}</a></strong>
  <ul>
   <li><strong>Affecting wheezy: <a href="http://udd.debian.org/bugs.cgi?release=wheezy&merged=ign&rc=1">#{wheezy}</a></strong>
    That's the number we need to get down to zero before the release. They can be split in two big categories:
    <ul>
     <li><strong>Affecting wheezy and unstable: <a href="http://udd.debian.org/bugs.cgi?release=wheezy_and_sid&merged=ign&rc=1">#{wheezy_sid}</a></strong>
      Those need someone to find a fix, or to finish the work to upload a fix to unstable:
      <ul>
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=wheezy_and_sid&patch=only&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&cdeferred=1">#{wh_patch}</a> bugs are tagged 'patch'.</strong>
        Please help by reviewing the patches, and (if you are a DD) by uploading them.
       </li>
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=wheezy_and_sid&merged=ign&done=only&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&cdeferred=1">#{wh_done}</a> bugs are marked as done, but still affect unstable.</strong>
        This can happen due to missing builds on some architectures, for example. Help investigate!
       </li>
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=wheezy_and_sid&patch=ign&merged=ign&done=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&ctags=1&cdeferred=1">#{wh_neither}</a> bugs are neither tagged patch, nor marked done.</strong>
Help make a first step towards resolution!
       </li>
      </ul>
     </li>

     <li><strong>Affecting wheezy only: <a href="http://udd.debian.org/bugs.cgi?release=wheezy_not_sid&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1&crttags=1">#{wheezy_only}</a></strong>
      Those are already fixed in unstable, but the fix still needs to migrate to wheezy.  You can help by submitting unblock requests for fixed packages, by investigating why packages do not migrate, or by reviewing submitted unblock requests.
     </li>
    </ul>
   </li>
  </ul>
 </li>
</ul>

<p>How do we compare to the Squeeze release cycle?</p>
<table border=1>
<tr><th>Week</th><th>Squeeze</th><th>Wheezy</th><th>Diff</th></tr>
<tr><td>43</td><td>284 (213+71)</td><td>468 (332+136)</td><td>+184 (+119/+65)</td></tr>
<tr><td>44</td><td>261 (201+60)</td><td>408 (265+143)</td><td>+147 (+64/+83)</td></tr>
<tr><td>45</td><td>261 (205+56)</td><td>425 (291+134)</td><td>+164 (+86/+78)</td></tr>
<tr><td>46</td><td>271 (200+71)</td><td>401 (258+143)</td><td>+130 (+58/+72)</td></tr>
<tr><td>47</td><td>283 (209+74)</td><td>366 (221+145)</td><td>+83 (+12/+71)</td></tr>
<tr><td>48</td><td>256 (177+79)</td><td>378 (230+148)</td><td>+122 (+53/+69)</td></tr>
<tr><td>49</td><td>256 (180+76)</td><td>360 (216+155)</td><td>+104 (+36/+79)</td></tr>
<tr><td>50</td><td>204 (148+56)</td><td>339 (195+144)</td><td>+135 (+47/+90)</td></tr>
<tr><td>51</td><td>178 (124+54)</td><td>323 (190+133)</td><td>+145 (+66/+79)</td></tr>
<tr><td>52</td><td>115 (78+37)</td><td>289 (190+99)</td><td>+174 (+112/+62)</td></tr>
<tr><td>1</td><td>93 (60+33)</td><td>287 (171+116)</td><td>+194 (+111/+83)</td></tr>
<tr><td>2</td><td>82 (46+36)</td><td>271 (162+109)</td><td>+189 (+116/+73)</td></tr>
<tr><td>3</td><td>25 (15+10)</td><td></td><td></td></tr>
<tr><td>4</td><td>14 (8+6)</td><td></td><td></td></tr>
<tr><td>5</td><td>2 (0+2)</td><td></td><td></td></tr>
<tr><td>6</td><td>release!</td><td></td></tr>
</table>

</body></html>
EOF
