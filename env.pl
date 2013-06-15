
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
  my $id_column = 0;
  my ($header_color,$task_header_color,$vit_header_color);
  &audit("EXEC $task show 2>&1");
  open(IN,"$task show 2>&1 |");
  while(<IN>) {
    chop;
    if ( $_ =~ /color\.header\s+(.*)/ ) {
      $task_header_color = $1;
      next;
    }
    if ( $_ =~ /color\.vit\.header\s+(.*)/ ) {
      $vit_header_color = $1;
      next;
    }
    if ( $_ =~ /color\.vit\.selection\s+(.*)/ ) {
      my $str = $1;
      $str =~ s/\x1b.*?m//g;
      $str =~ s/^\s+//;
      $str =~ s/\s+$//;
      &extract_color($str,'vit selection');
      $selection_attrs = $parsed_attrs[1];
      init_pair($COLOR_SELECTION,$parsed_colors_fg[1],$parsed_colors_bg[1]);
      next;
    }
    if ( $_ =~ /default.command\s+(.*)/ ) { 
      $default_command = $1;
      $default_command =~ s/\x1b.*?m//g;
      $default_command =~ s/^\s+//g;
      $default_command =~ s/\s+$//g;
      next;
    }
    if ( $_ =~ /report\.(.*?)\.columns/ ) {
      push(@reports, $1);
      next;
    }
    if ( $_ =~ /The color .* is not recognized/ ) {
      endwin();
      print "$_\r\n";
      exit(1);
    }
  }
  close(IN);
  if ( defined $vit_header_color ) {
    $header_color = $vit_header_color;
  } elsif ( defined $task_header_color ) { 
    $header_color = $task_header_color;
  } else {
    init_pair($COLOR_HEADER,-1,-1); # not reached
  }
  if ( defined $header_color ) {
    &extract_color($header_color,'header');
    $header_color =~ s/\x1b.*?m//g;
    $header_color =~ s/^\s+//;
    $header_color =~ s/\s+$//;
    $header_attrs = $parsed_attrs[1];
    init_pair($COLOR_HEADER,$parsed_colors_fg[1],$parsed_colors_bg[1]);
  }
  if ( $cli_args ne '' ) { 
    chop $cli_args;
    $default_command = $cli_args; 
  } 
  &audit("EXEC $task rc._forcecolor=on rc.verbose=on $default_command 2>&1");
  open(IN,"$task rc._forcecolor=on rc.verbose=on $default_command 2>&1 |");
  while(<IN>) {
    chop;
    if ( $_ =~ /ID/ || ($default_command eq 'summary' && $_ =~ /Project/) ) {
      &parse_line(0,$_);
      @report_header_colors_fg = @parsed_colors_fg;
      @report_header_colors_bg = @parsed_colors_bg;
      @report_header_attrs = @parsed_attrs;
      if ( $parsed_colors_fg[0] eq '999999' ) { $parsed_colors_fg[0] = -1; }
      if ( $parsed_colors_bg[0] eq '999999' ) { $parsed_colors_bg[0] = -1; }
      init_pair($COLOR_REPORT_HEADER,$parsed_colors_fg[0],$parsed_colors_bg[0]);
      $id_column = 1;
    } 
  }
  close(IN);
  if ( ! $id_column && $default_command ne 'summary' ) {
    endwin();
    print "Fatal error: default.command (\"$default_command\") must print an \"ID\" column\n";
    exit(1);
  }
  &audit("ENV default command is \"$default_command\"");
  $current_command = $default_command;
  push(@reports,$default_command);
  push(@reports,'summary');
  @report_types = sort(@reports);

}

return 1;
