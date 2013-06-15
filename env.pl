
sub init_shell_env {
  if ( $ENV{'TERM'} =~ /^xterm/ || $ENV{'TERM'} =~ /^screen/ ) {
    &audit("ENV TERM=xterm-256color");
    $ENV{'TERM'} = 'xterm-256color';
  } 
  if ( $titlebar ) {
    &audit("ENV set titlebar");
    open(TTY, ">>/dev/tty");
    print TTY "\e]0;$version\cg\n";
    close(TTY);
  }
}

#------------------------------------------------------------------

sub init_task_env {
  my @reports;
  &audit("EXEC task 2>&1");
  open(IN,"task rc._forcecolor=on 2>&1 |");
  while(<IN>) {
    chop;
    if ( $_ =~ /^\[task (.*)\]$/ || $_ =~ /^\x1b.*?m\[task (.*)\]\x1b\[0m$/ ) {
      $default_command = $1;
      $default_command =~ s/ rc._forcecolor=on//;
      &parse_line(0,$_);
      @report_header_colors_fg = @parsed_colors_fg;
      @report_header_colors_bg = @parsed_colors_bg;
      @report_header_attrs = @parsed_attrs;
      my $fg = $report_header_colors_fg[0];
      my $bg = $report_header_colors_bg[0];
      $COLOR_HEADER = &get_color_pair($fg,$bg);
      $header_win->attron(COLOR_PAIR($COLOR_HEADER));
      &set_attron($header_win,$report_header_attrs[0]);
      $prompt_win->attron(COLOR_PAIR($COLOR_HEADER));
    }
  } 
  close(IN);
  $current_command = $default_command;
  push(@reports,$default_command);
  push(@reports,'summary'); # FIXME temp. hack
  &audit("EXEC task show 2>&1");
  open(IN,"task show 2>&1 |");
  while(<IN>) {
    chop;
    if ( $_ =~ /^report\.(.*?)\.columns/ ) {
      push(@reports, $1);
      next;
    }
    if ( $_ =~ /color\.vit\.selection\s+(.*)/ ) {
      my $cstr = $1;
      CASE: {
        if ( $cstr =~ /color(\d+) on color(\d+)/ ) {
          init_pair($COLOR_SELECTION,$1,$2);
          last CASE;
        }
        if ( $cstr =~ /on color(\d+)/ ) {
          init_pair($COLOR_SELECTION,-1,$1);
          last CASE;
        }
        if ( $cstr =~ /color(\d+)/ ) {
          init_pair($COLOR_SELECTION,$1,-1); 
          last CASE;
        }
        $error_msg = "Warning: the color '$cstr' is not recognized.  ";
        $error_msg .= "Only the 'colorN' notation is allowed.";
      }
      next;
    }
  }
  close(IN);
  @report_types = sort(@reports);
}

return 1;
