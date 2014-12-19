#!/usr/bin/ruby

require 'dbi'
require 'pp'
require 'cgi'
require 'time'

STDERR.reopen(STDOUT)

puts "Content-type: text/html\n\n"

TESTING='jessie'

q = {}
c = {}
ckp = {}

q[:tot] = <<-EOF
SELECT source IN (select source from key_packages) as kp, count(id) FROM bugs
WHERE status != 'done'
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
group by kp order by kp
EOF

q[:wh_patch] = <<-EOF
SELECT source IN (select source from key_packages) as kp, count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id IN (SELECT id FROM bugs_rt_affects_unstable)
AND id IN (SELECT id FROM bugs_tags WHERE tag='patch')
AND status != 'done'
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
group by kp order by kp
EOF

q[:wh_done] = <<-EOF
SELECT source IN (select source from key_packages) as kp, count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id IN (SELECT id FROM bugs_rt_affects_unstable)
AND status = 'done'
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
group by kp order by kp
EOF

q[:wh_neither] = <<-EOF
SELECT source IN (select source from key_packages) as kp, count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id IN (SELECT id FROM bugs_rt_affects_unstable)
AND NOT (id IN (SELECT id FROM bugs_tags WHERE tag='patch'))
AND status != 'done'
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND (severity >= 'serious')
group by kp order by kp
EOF

q[:wo_unblocked] = <<-EOF
SELECT source IN (select source from key_packages) as kp, count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id NOT IN (SELECT id FROM bugs_rt_affects_unstable)
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND bugs.source IN (SELECT hints.source FROM hints WHERE type IN ('approve','unblock'))
AND (severity >= 'serious')
group by kp order by kp
EOF

q[:wo_notunblocked] = <<-EOF
SELECT source IN (select source from key_packages) as kp, count(id) FROM bugs
WHERE id IN (SELECT id FROM bugs_rt_affects_testing) AND id NOT IN (SELECT id FROM bugs_rt_affects_unstable)
AND NOT (id IN (SELECT id FROM bugs_merged_with WHERE id > merged_with))
AND NOT (bugs.source IN (SELECT hints.source FROM hints WHERE type IN ('approve','unblock')))
AND (severity >= 'serious')
group by kp order by kp
EOF

$dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guest')
$dbh.execute("SET statement_timeout TO 90000")
def getcount(q)
  begin
    sth = $dbh.prepare(q)
    sth.execute
    rows = sth.fetch_all
    if rows.length == 1
      return rows[0][1], 0
    else
      return rows[0][1] + rows[1][1], rows[1][1]
    end
  rescue DBI::ProgrammingError => e
    puts "<p>The query generated an error, please report it to lucas@debian.org: #{e.message}</p>"
    puts "<pre>#{q}</pre>"
    exit(0)
  end
end

q.keys.each do |name|
  c[name], ckp[name] = getcount(q[name])
end

c[:jessie_only] = c[:wo_unblocked] + c[:wo_notunblocked]
ckp[:jessie_only] = ckp[:wo_unblocked] + ckp[:wo_notunblocked]
c[:jessie_sid] = c[:wh_neither] + c[:wh_done] + c[:wh_patch]
ckp[:jessie_sid] = ckp[:wh_neither] + ckp[:wh_done] + ckp[:wh_patch]
c[:jessie] = c[:jessie_only] + c[:jessie_sid]
ckp[:jessie] = ckp[:jessie_only] + ckp[:jessie_sid]

week = Time.now.strftime('%V')
fields = "&chints=1&cdeferred=1&crttags=1"
puts <<-EOF
<html><body>
<h1>Release Critical Bug report for Week #{week}</h1>

<p>The <a href="http://udd.debian.org/bugs.cgi">UDD bugs interface</a> currently knows about the following release critical bugs:</p>

<ul>
 <li>
 <strong>In Total: <a href="http://udd.debian.org/bugs.cgi?release=any&merged=ign&rc=1#{fields}">#{c[:tot]}</a> (Including <a href="http://udd.debian.org/bugs.cgi?release=any&merged=ign&rc=1&keypackages=only#{fields}">#{ckp[:tot]}</a> bugs affecting <a href="https://lists.debian.org/debian-devel-announce/2013/09/msg00006.html">key packages</a>)</strong>
  <ul>
   <li><strong>Affecting Jessie: <a href="http://udd.debian.org/bugs.cgi?release=jessie&merged=ign&rc=1#{fields}">#{c[:jessie]}</a> (key packages: <a href="http://udd.debian.org/bugs.cgi?release=jessie&merged=ign&rc=1&keypackages=only#{fields}">#{ckp[:jessie]}</a>)</strong>
    That's the number we need to get down to zero before the release. They can be split in two big categories:
    <ul>
     <li><strong>Affecting Jessie and unstable: <a href="http://udd.debian.org/bugs.cgi?release=jessie_and_sid&merged=ign&rc=1#{fields}">#{c[:jessie_sid]}</a> (key packages: <a href="http://udd.debian.org/bugs.cgi?release=jessie_and_sid&merged=ign&rc=1&keypackages=only#{fields}">#{ckp[:jessie_sid]}</a>)</strong>
      Those need someone to find a fix, or to finish the work to upload a fix to unstable:
      <ul>
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=jessie_and_sid&patch=only&merged=ign&done=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&cdeferred=1#{fields}">#{c[:wh_patch]}</a> bugs are tagged 'patch'. (key packages: <a href="http://udd.debian.org/bugs.cgi?release=jessie_and_sid&patch=only&merged=ign&done=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&cdeferred=1&keypackages=only#{fields}">#{ckp[:wh_patch]}</a>)</strong>
        Please help by reviewing the patches, and (if you are a DD) by uploading them.
       </li>
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=jessie_and_sid&merged=ign&done=only&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&cdeferred=1#{fields}">#{c[:wh_done]}</a> bugs are marked as done, but still affect unstable. (key packages: <a href="http://udd.debian.org/bugs.cgi?release=jessie_and_sid&merged=ign&done=only&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&cdeferred=1&keypackages=only#{fields}">#{ckp[:wh_done]}</a>)</strong>
        This can happen due to missing builds on some architectures, for example. Help investigate!
       </li>
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=jessie_and_sid&patch=ign&merged=ign&done=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&ctags=1&cdeferred=1#{fields}">#{c[:wh_neither]}</a> bugs are neither tagged patch, nor marked done. (key packages: <a href="http://udd.debian.org/bugs.cgi?release=jessie_and_sid&patch=ign&merged=ign&done=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&ctags=1&ctags=1&cdeferred=1&keypackages=only#{fields}">#{ckp[:wh_neither]}</a>)</strong>
Help make a first step towards resolution!
       </li>
      </ul>
     </li>

     <li><strong>Affecting Jessie only: <a href="http://udd.debian.org/bugs.cgi?release=jessie_not_sid&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1&crttags=1#{fields}">#{c[:jessie_only]}</a> (key packages: <a href="http://udd.debian.org/bugs.cgi?release=jessie_not_sid&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1&crttags=1&keypackages=only#{fields}">#{ckp[:jessie_only]}</a>)</strong>
      Those are already fixed in unstable, but the fix still needs to migrate to Jessie.  You can help by submitting unblock requests for fixed packages, by investigating why packages do not migrate, or by reviewing submitted unblock requests.
      <ul>
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=jessie_not_sid&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1&crttags=1&unblock-hint=only#{fields}">#{c[:wo_unblocked]}</a> bugs are in packages that are unblocked by the release team. (key packages: <a href="http://udd.debian.org/bugs.cgi?release=jessie_not_sid&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1&crttags=1&unblock-hint=only&keypackages=only#{fields}">#{ckp[:wo_unblocked]}</a>)</strong>
       <li><strong><a href="http://udd.debian.org/bugs.cgi?release=jessie_not_sid&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1&crttags=1&unblock-hint=ign#{fields}">#{c[:wo_notunblocked]}</a> bugs are in packages that are not unblocked. (key packages: <a href="http://udd.debian.org/bugs.cgi?release=jessie_not_sid&merged=ign&fnewerval=7&rc=1&sortby=id&sorto=asc&chints=1&ctags=1&cdeferred=1&crttags=1&unblock-hint=ign&keypackages=only#{fields}">#{ckp[:wo_notunblocked]}</a>)</strong>
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
<tr><th>Week</th> <th>Squeeze</th>        <th>Wheezy</th>         <th>Jessie</th></tr>
<tr><td>43</td>   <td>284 (213+71)</td>   <td>468 (332+136)</td>  <td>319 (240+79)</td></tr>
<tr><td>44</td>   <td>261 (201+60)</td>   <td>408 (265+143)</td>  <td>274 (224+50)</td></tr>
<tr><td>45</td>   <td>261 (205+56)</td>   <td>425 (291+134)</td>  <td>295 (229+66)</td></tr>
<tr><td>46</td>   <td>271 (200+71)</td>   <td>401 (258+143)</td>  <td>427 (313+114)</td></tr>
<tr><td>47</td>   <td>283 (209+74)</td>   <td>366 (221+145)</td>  <td>342 (260+82)</td></tr>
<tr><td>48</td>   <td>256 (177+79)</td>   <td>378 (230+148)</td>  <td>274 (189+85)</td></tr>
<tr><td>49</td>   <td>256 (180+76)</td>   <td>360 (216+155)</td>  <td>226 (147+79)</td></tr>
<tr><td>50</td>   <td>204 (148+56)</td>   <td>339 (195+144)</td>  <td>???</td></tr>
<tr><td>51</td>   <td>178 (124+54)</td>   <td>323 (190+133)</td>  <td>189 (134+55)</td></tr>
<tr><td>52</td>   <td>115 (78+37)</td>    <td>289 (190+99)</td>   <td></td></tr>
<tr><td>1</td>    <td>93 (60+33)</td>     <td>287 (171+116)</td>  <td></td></tr>
<tr><td>2</td>    <td>82 (46+36)</td>     <td>271 (162+109)</td>  <td></td></tr>
<tr><td>3</td>    <td>25 (15+10)</td>     <td>249 (165+84)</td>   <td></td></tr>
<tr><td>4</td>    <td>14 (8+6)</td>       <td>244 (176+68)</td>   <td></td></tr>
<tr><td>5</td>    <td>2 (0+2)</td>        <td>224 (132+92)</td>   <td></td></tr>
<tr><td>6</td>    <td>release!</td>       <td>212 (129+83)</td>   <td></td></tr>
<tr><td>7</td>    <td>release+1</td>      <td>194 (128+66)</td>   <td></td></tr>
<tr><td>8</td>    <td>release+2</td>      <td>206 (144+62)</td>   <td></td></tr>
<tr><td>9</td>    <td>release+3</td>      <td>174 (105+69)</td>   <td></td></tr>
<tr><td>10</td>   <td>release+4</td>      <td>120 (72+48)</td>    <td></td></tr>
<tr><td>11</td>   <td>release+5</td>      <td>115 (74+41)</td>    <td></td></tr>
<tr><td>12</td>   <td>release+6</td>      <td>93 (47+46)</td>     <td></td></tr>
<tr><td>13</td>   <td>release+7</td>      <td>50 (24+26)</td>     <td></td></tr>
<tr><td>14</td>   <td>release+8</td>      <td>51 (32+19)</td>     <td></td></tr>
<tr><td>15</td>   <td>release+9</td>      <td>39 (32+7)</td>      <td></td></tr>
<tr><td>16</td>   <td>release+10</td>     <td>20 (12+8)</td>      <td></td></tr>
<tr><td>17</td>   <td>release+11</td>     <td>24 (19+5)</td>      <td></td></tr>
<tr><td>18</td>   <td>release+12</td>     <td>2 (2+0)</td>        <td></td></tr>
</table>

</body></html>
EOF
