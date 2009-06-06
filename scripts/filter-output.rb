#!/usr/bin/ruby -w

LINES = [
  "Can't parse line 66715: /org/lintian.debian.org/root/collection/strings: line 37: strings/./usr/share/doc/HOWTO/it-html/ELF-HOWTO/: Is a directory",
  "Can't parse line 124359: strings: 'unpacked/./usr/share/man/man3/Lire': No such file",
  'Duplicated key in language es:  gedit-plugins debian main squeeze 2.22.5-1 Conjunto de complementos de gedit 5edb9235bd149de240234eeb4065cff7'
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
