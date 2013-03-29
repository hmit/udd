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
SELECT count(*) FROM bugs
WHERE status != 'done'
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
EOF
tot = getcount(q)
q = <<-EOF
SELECT count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing)
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
EOF
wheezy = getcount(q)

q = <<-EOF
SELECT count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id IN (SELECT id FROM bugs_rt_affects_unstable)
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
EOF
wheezy_sid = getcount(q)
q = <<-EOF
SELECT count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id NOT IN (SELECT id FROM bugs_rt_affects_unstable)
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
EOF
wheezy_only = getcount(q)

q = <<-EOF
SELECT count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id IN (SELECT id FROM bugs_rt_affects_unstable)
AND id IN (SELECT id FROM bugs_tags WHERE tag='patch')
AND status != 'done'
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
EOF
wh_patch = getcount(q)

q = <<-EOF
SELECT count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id IN (SELECT id FROM bugs_rt_affects_unstable)
AND status = 'done'
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
EOF
wh_done = getcount(q)

q = <<-EOF
SELECT count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id IN (SELECT id FROM bugs_rt_affects_unstable)
AND NOT (id IN (SELECT id FROM bugs_tags WHERE tag='patch'))
AND status != 'done'
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
EOF
wh_neither = getcount(q)

q = <<-EOF
SELECT count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id NOT IN (SELECT id FROM bugs_rt_affects_unstable)
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND bugs.source IN (SELECT hints.source FROM hints WHERE type IN ('approve','unblock'))
AND (severity >= 'serious')
EOF
wo_unblocked = getcount(q)

q = <<-EOF
SELECT count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id NOT IN (SELECT id FROM bugs_rt_affects_unstable)
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND NOT (bugs.source IN (SELECT hints.source FROM hints WHERE type IN ('approve','unblock')))
AND (severity >= 'serious')
EOF
wo_notunblocked = getcount(q)

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
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=wheezy_and_sid&patch=only&merged=ign&done=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&cdeferred=1">#{wh_patch}</a> bugs are tagged 'patch'.</strong>
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
      <ul>
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=wheezy_not_sid&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1&crttags=1&unblock-hint=only">#{wo_unblocked}</a> bugs are in packages that are unblocked by the release team.</strong>
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=wheezy_not_sid&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1&crttags=1&unblock-hint=ign">#{wo_notunblocked}</a> bugs are in packages that are not unblocked.</strong>
       </li>
      </ul>
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
<tr><td>3</td><td>25 (15+10)</td><td>249 (165+84)</td><td>+224 (+150/+74)</td></tr>
<tr><td>4</td><td>14 (8+6)</td><td>244 (176+68)</td><td>+230 (+168/+62)</td></tr>
<tr><td>5</td><td>2 (0+2)</td><td>224 (132+92)</td><td>+222 (+132/+90)</td></tr>
<tr><td>6</td><td>release!</td><td>212 (129+83)</td><td>+212 (+129/+83)</td></tr>
<tr><td>7</td><td>release+1</td><td>194 (128+66)</td><td>+194 (+128/+66)</td></tr>
<tr><td>8</td><td>release+2</td><td>206 (144+62)</td><td>+206 (+144/+62)</td></tr>
<tr><td>9</td><td>release+3</td><td>174 (105+69)</td><td>+174 (+105/+69)</td></tr>
<tr><td>10</td><td>release+4</td><td>120 (72+48)</td><td>+120 (+72/+48)</td></tr>
<tr><td>11</td><td>release+5</td><td>115 (74+41)</td><td>+115 (+74/+41)</td></tr>
<tr><td>12</td><td>release+6</td><td>93 (47+46)</td><td>+93 (+47/+46)</td></tr>
<tr><td>13</td><td>release+7</td><td>50 (24+26)</td><td>+50 (+24/+26)</td></tr>
<tr><td>14</td><td>release+8</td><td></td><td></td></tr>
<tr><td>15</td><td>release+9</td><td></td><td></td></tr>
<tr><td>16</td><td>release+10</td><td></td><td></td></tr>
<tr><td>17</td><td>release+11</td><td></td><td></td></tr>
<tr><td>18</td><td>release+12</td><td></td><td></td></tr>
</table>

</body></html>
EOF
