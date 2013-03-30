require 'pp'

# Parser for Debian's use of RFC 822
class Deb822

  attr_reader :result
  def initialize(opts)
    @result = []
    @opts = opts
  end

  def parse(input)
    if input.kind_of?(String)
      parse_str(input)
    elsif input.kind_of?(IO)
      parse_str(input.read)
    else
      puts "Input class #{input.class} unrecognized"
    end
  end

  def Deb822.parse(input, opts)
    d = Deb822.new(opts)
    d.parse(input)
    return d.result
  end

  private
  def parse_str(str)
    curp = {}
    @result = []
    curh = nil
    str.each_line do |l|
      next if l =~ /^-----BEGIN PGP SIGNED MESSAGE-----$/
      next if l =~ /^Hash: /
      if l =~ /^$/
        @result << curp if not curp.empty?
        curp = {}
      elsif l =~ /^\s+/
        curp[curh] += "\n " + l.gsub(/^\s+/, '').chomp
      elsif l =~ /^([^:\s]*):\s*$/
        if @opts[:downcase]
          curh = $1.downcase
        else
          curh = $1
        end
        curp[curh] = ''
      elsif l =~ /^([^:\s]*): (.*)$/
        if @opts[:downcase]
          curh = $1.downcase
        else
          curh = $1
        end
        curp[curh] = $2
      end
    end
    @result << curp if not curp.empty?
    @result
  end
end

def show_universe
  res = Deb822::new.parse(IO::read('/var/lib/dpkg/status'))
  srcpkgs = []
  # find Sources list
  Dir.foreach('/var/lib/apt/lists/') do |e|
    if e =~ /Sources$/ and e =~ /ubuntu/
      l = Deb822::new.parse(IO::read("/var/lib/apt/lists/#{e}"))
      srcpkgs += l
    end
  end
  # hashing sources
  srcs = {}
  puts srcpkgs.class
  srcpkgs.each do |pkg|
    name = pkg['Package']
    srcs[name] = [] unless srcs[name]
    srcs[name] << pkg
  end
  res.each do |pkg|
    if pkg['Status'].split.include?('installed')
      # package installed
      if pkg['Source']
        src = pkg['Source']
      else
        src = pkg['Package']
      end
      srcp = nil
      if srcs[src]
        srcs[src].each do |s|
          if pkg['Version'] == s['Version']
            srcp = s
          end
        end
        STDERR.puts "#{pkg['Package']} not found1" unless srcp
        srcp = srcs[src][0]
      end
      STDERR.puts "#{pkg['Package']} not found2" unless srcp
      if srcp and srcp['Section'] =~ /^(un|mult)iverse/
        puts "#{pkg['Package']} (source: #{srcp['Package']}, #{pkg['Version']}) is in (un|mult)iverse"
      end
    end
  end
end
