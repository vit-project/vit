
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
  if ( $prompt =~ /^(:)(.*)/ || $prompt =~ /^(.*?:)(.*)/ ) {
    $prompt = $1;
    $str = $2;
  }
  echo();
  curs_set(1);
  &draw_prompt("$prompt$str");
  while (1) {
    my $ch = $prompt_win->getch();
    if ( $ch eq "\ch" ) {
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
    if ( $ch eq "\t" ) {
      $tab_cnt++;
      if ( $tab_cnt == 1 ) { $tab_match_str = $str; }
      if ( $tab_match_str eq '' ) {
        my $idx = $tab_cnt % ($#report_types + 1) - 1;
        $str = $report_types[$idx];
      } else {
        my @matches = (grep(/^$tab_match_str/,@report_types));
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
    if ( $ch eq "\n" ) {
      last;
    }
    $str .= $ch;
  }
  noecho();
  curs_set(0);
  if ( $str eq '' ) { beep(); }  
  $str =~ s/"/\\"/g;
  return $str;
} 

return 1;
