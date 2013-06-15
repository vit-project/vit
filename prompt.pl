
sub prompt_y {
  my ($prompt) = @_;
  my $ans = 0;
  my $ch;
  echo();
  curs_set(1);
  &draw_prompt($prompt);
  $ch = $prompt_win->getch();
  if ( $ch eq "y" || $ch eq "Y" ) { $ans = 1; }
  noecho();
  curs_set(0);
  return $ans;
}

#------------------------------------------------------------------

sub prompt_str {
  my ($prompt) = @_;
  my $str = '';
  my $tab_cnt = 0;
  my $tab_match_str = '';
  my $mode;
  my @match_types;
  if ( $prompt =~ /^(:)(.*)/ || $prompt =~ /^(.*?: )(.*)/ || $prompt =~ /^(.*?:)(.*)/ ) {
    $prompt = $1;
    $str = $2;
  } 
  if ( $prompt eq ':' ) { 
    $mode = 'cmd';
    @match_types = @report_types;
  } else {
    $mode = lc($prompt);
    $mode =~ s/:.*$//;
    if ( $mode eq 'project' ) {
      @match_types = @project_types;
    }
  }
  curs_set(1);
  &draw_prompt("$prompt$str");
  while (1) {
    my $ch = $prompt_win->getch();
    #debug("TOP str=\"$str\" ch=\"$ch\"");
    if ( $ch eq "\b" || $ch eq "\c?" ) {
      if ( $str ne '' ) {
        chop $str;
        if ( length($str) < length($tab_match_str) ) { 
          chop $tab_match_str;
        }
      } else {
        $tab_match_str = '';
        $tab_cnt = 0;
      }
      &draw_prompt("$prompt$str");
      next; 
    }
    if ( $ch eq "\cu" ) {
      $str = '';
      $tab_match_str = '';
      $tab_cnt = 0;
      &draw_prompt("$prompt$str");
      next; 
    }
    if ( $ch eq "\e" ) {
      noecho();
      curs_set(0);
      return '';
    }
    if ( $ch eq "\n" ) {
      last;
    }
    if ( $ch eq "\t" ) {
      if ( $mode ne 'cmd' && $mode ne 'project' ) { 
        beep();
        next;
      }
      $tab_cnt++;
      if ( $tab_cnt == 1 ) { $tab_match_str = $str; }
      if ( $tab_match_str eq '' ) {
        my $idx = $tab_cnt % ($#match_types + 1) - 1;
        $str = $match_types[$idx];
      } else {
        my @matches = (grep(/^$tab_match_str/,@match_types));
        if ( $#matches == -1 ) {
          $tab_cnt = 0;
          beep();
        } else  {
          my $idx = $tab_cnt % ($#matches + 1) - 1;
          $str = $matches[$idx];
        }
      }
      &draw_prompt("$prompt$str");
      next;
    }
    if ( $ch eq "\cw" ) {
      if ( $str eq '' ) { 
        chop $str;
        beep();
        next;
      }
      if ( $str =~ s/^(.*\s+)\S+\s+$/$1/ ) {
        &draw_prompt("$prompt$str");
        next;
      }
      if ( $str =~ s/^.*\s+$// ) {
        &draw_prompt("$prompt$str");
        next;
      }
      if ( $str =~ s/^(.*\s+).*/$1/ ) {
        &draw_prompt("$prompt$str");
        next;
      }
      $str = "";
      &draw_prompt("$prompt$str");
      next;
    }
    $str .= $ch;
    &draw_prompt("$prompt$str");
  }
  noecho();
  curs_set(0);
  if ( $mode ne 'project' && $str eq '' ) { beep(); }  
  $str =~ s/"/\\"/g;
  $str =~ s/^\s+//;
  $str =~ s/\s+$//;
  return $str;
} 

return 1;
