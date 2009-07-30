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
