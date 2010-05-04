#!/usr/bin/ruby -w
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

if cgi.has_key?('email')
allpkgs = cgi.has_key?('allpkgs')
pw = IO::read('/org/udd.debian.org/guestdd-password').chomp
dbh = DBI::connect('DBI:Pg:dbname=udd;port=5441;host=localhost', 'guestdd', pw)
maint = dbh.select_all("select source from sources where distribution='debian' and release='sid' and maintainer_email=#{dbh.quote(cgi['email'])}").map { |e| e[0] }.uniq
upload = dbh.select_all("select source from uploaders where distribution='debian' and release='sid' and email=#{dbh.quote(cgi['email'])}").map { |e| e[0] }.uniq
pts = dbh.select_all("select source from pts where #{dbh.quote(cgi['email'])}=email").map { |e| e[0] }
puts "<h1>PTS subscriptions check for #{cgi['email']}</h1>"
if (maint - pts).length > 0
puts "Packages you maintain but are not subscribed to:<br/><ul>"
(maint - pts).sort.each { |s| puts "<li><a href=\"http://packages.qa.debian.org/#{s}\">#{s}</a></li>" }
puts "</ul>"
end
if (upload - pts).length > 0
puts "Packages you are uploader for but are not subscribed to:<br/><ul>"
(upload - pts).sort.each { |s| puts "<li><a href=\"http://packages.qa.debian.org/#{s}\">#{s}</a></li>" }
puts "</ul>"
end
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