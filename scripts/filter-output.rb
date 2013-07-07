#!/usr/bin/ruby -w
# coding: utf-8

STDIN.set_encoding("BINARY")

LINES = [
  "Can't parse line 66715: /org/lintian.debian.org/root/collection/strings: line 37: strings/./usr/share/doc/HOWTO/it-html/ELF-HOWTO/: Is a directory",
  "Can't parse line 124359: strings: 'unpacked/./usr/share/man/man3/Lire': No such file",
  'Duplicated key in language es:  gedit-plugins debian main squeeze 2.22.5-1 Conjunto de complementos de gedit 5edb9235bd149de240234eeb4065cff7',
  './munge_ddc.py /srv/udd.debian.org/email-archives/debian-devel-changes/debian-devel-changes.current > debian-devel-changes.current.out',
  /illegal package name Package: /,
  /Skipping upload: /,
  /Can't parse line .* Use of uninitialized value in split at/,
  /Can't parse line .* Use of uninitialized value.*in pattern match \(m\/\/\) at/,
  /debtags: can not parse line /,
  /Bug .*: unable to open .srv.bugs.debian.org.versions.pkg/,
  /failed to convert to utf8/
]

STDIN.each_line do |l|
  l = l.chomp
  ok = 0
  LINES.each do |re|
    if (re.class == String and l == re) or (re.class == Regexp and l =~ re)
      ok = 1
    end
  end
  if ok == 0
    puts l
  end
end
