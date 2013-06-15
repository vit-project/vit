
sub read_report {
  my $report_header_idx = 0; 
  my $args;
  @report_tokens = ();
  @report_colors_fg = ();
  @report_colors_bg = ();
  @report_attrs = ();
  @report_header_tokens = ();
  @report_header_colors_fg = ();
  @report_header_colors_bg = ();
  @report_header_attrs = ();

  &audit("EXEC task 2>&1");
  open(IN,"task rc._forcecolor=on 2>&1 |");
  while(<IN>) {
    chop;
    if ( $_ =~ /^\[(.*)\]$/ || $_ =~ /^\x1b.*?m\[(.*)\]\x1b\[0m$/ ) { 
      $report_descr = $1;
      $report_descr =~ s/ rc._forcecolor=on//;
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
      last; 
    }
  }
  close(IN);

  &audit("EXEC task show color.vit.selection 2>&1");
  open(IN,"task show color.vit.selection 2>&1 |");
  while(<IN>) {
    chop;
    if ( $_ !~ /^color.vit.selection\s+(.*)/ ) { next; }
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
      $error_msg = "Warning: the color '$cstr' is not recognized.  Only the 'colorN' notation is allowed.";
    }
    last;
  }
  close(IN);

  &audit("EXEC task stat 2>&1");
  open(IN,"task stat 2>&1 |");
  while(<IN>) {
    chop;
    if ( $_ =~ /^\s*$/ ) { next; }
    $_ =~ s/\x1b.*?m//g;
    if ( $_ =~ /Pending\s+(\d+)/ ) {
      $tasks_pending = $1;
      next;
    } 
    if ( $_ =~ /Completed\s+(\d+)/ ) {
      $tasks_completed = $1;
      next;
    } 
  } 
  close(IN);

  $args = "rc.defaultwidth=$REPORT_COLS rc.defaultheight=$REPORT_LINES burndown.daily";
  &audit("EXEC task $args 2>&1");
  open(IN,"task $args 2>&1 |");
  while(<IN>) {
    if ( $_ =~ /Estimated completion: No convergence/ ) {
      $convergence = "no convergence";
      last;
    }
    if ( $_ =~ /Estimated completion: .* \((.*)\)/ ) { 
      $convergence = "convergence in $1";
      last; 
    }
  }
  close(IN);

  $args = "rc.defaultwidth=$REPORT_COLS rc.defaultheight=0 rc._forcecolor=on";
  &audit("EXEC task $args 2> /dev/null");
  open(IN,"task $args 2> /dev/null |");
  my $i = 0;
  my $prev_id;
  while(<IN>) {
    chop;
    if ( $_ =~ /^\s*$/ ) { next; }
    if ( $_ =~ /^(\d+) tasks[s]{0}$/ || $_ =~ /^\x1b.*?m(\d+) tasks[s]{0}\x1b\[0m$/ ) { 
      $num_tasks = $1;
      next;
    }
    &parse_report_line($i,$_);
    $_ =~ s/\x1b.*?m//g; 
    if ( $_ =~ /^ID / ) { # FIXME?
      $report_header_idx = $i;
      $i++;
      next;
    }
    if ( $_ =~ /^\s*(\d+) / ) {
      $report2taskid[$i] = $1;
    } else {
      $report2taskid[$i] = $prev_id;
    }
    $prev_id = $report2taskid[$i];
    $i++;
  }
  close(IN);

  @report_header_tokens = @{ $report_tokens[$report_header_idx] };
  @report_header_attrs = @{ $report_attrs[$report_header_idx] };
  splice(@report_tokens,$report_header_idx,1);
  splice(@report_colors_fg,$report_header_idx,1);
  splice(@report_colors_bg,$report_header_idx,1);
  splice(@report_attrs,$report_header_idx,1);
  splice(@report2taskid,$report_header_idx,1);

}

return 1;

