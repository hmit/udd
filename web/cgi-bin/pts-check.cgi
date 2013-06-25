#!/usr/bin/ruby
require 'dbi'
require 'cgi'

puts "Content-type: text/html\n\n"

puts <<-EOF
<html>
<html><head>
<title>PTS subscription check</title>
</head><body>
EOF

cgi = CGI::new

def quote(s)
  DBI::DBD::Pg::quote(s)
end

if cgi.has_key?('email')
allpkgs = cgi.has_key?('allpkgs')
pw = IO::read('/srv/udd.debian.org/guestdd-password').chomp
dbh = DBI::connect('DBI:Pg:dbname=udd;port=5452;host=localhost', 'guestdd', pw)
maint = dbh.select_all("select source from sources where distribution='debian' and release='sid' and maintainer_email=#{quote(cgi['email'])}").map { |e| e[0] }.uniq
upload = dbh.select_all("select source from uploaders where distribution='debian' and release='sid' and email=#{quote(cgi['email'])}").map { |e| e[0] }.uniq
pts = dbh.select_all("select source from pts where #{quote(cgi['email'])}=email").map { |e| e[0] }
puts "<h1>PTS subscriptions check for #{cgi['email']}</h1>"
if (maint - pts).length > 0
puts "Packages you maintain but are not subscribed to:<br/><pre>"
(maint - pts).sort.each { |s| puts "subscribe #{s} #{cgi['email']}" }
puts "</pre>"
end
if (upload - pts).length > 0
puts "Packages you are uploader for but are not subscribed to:<br/><pre>"
(upload - pts).sort.each { |s| puts "subscribe #{s} #{cgi['email']}" }
puts "</pre>"
end
puts 'To be sent in the body of a mail to pts@qa.debian.org. See <a href="http://www.debian.org/doc/developers-reference/resources.html#pts-commands">Developers Reference</a> for more info.<br/>If you are a DD, you can also connect to master and feed those commands to /org/packages.qa.debian.org/bin/pts'
else
puts <<-EOF

<form method="get" ACTION="pts-check.cgi">
Email to check: <input type="text" name="email" value="email" size="30"/>
<input type="submit"/><br/>
</form>
EOF
end
puts <<-EOF
</body>
</html>
EOF
