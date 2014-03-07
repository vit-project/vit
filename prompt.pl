# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2014, Scott Kostyshak

sub prompt_y {
  my $ch = &prompt_chr(@_);
  my $ans = 0;
  if ( $ch eq "y" || $ch eq "Y" ) { $ans = 1; }
  return $ans;
}

#------------------------------------------------------------------

sub prompt_chr {
  my ($prompt) = @_;
  my $ch;
  echo();
  curs_set(1);
  &draw_prompt($prompt);
  $ch = $prompt_win->getch();
  noecho();
  curs_set(0);
  return $ch;
}

#------------------------------------------------------------------

sub prompt_str {
  my ($prompt) = @_;
  $cur_pos = length($prompt);
  my $str = '';
  my $tab_cnt = 0;
  my $tab_match_str = '';
  my $mode;
  my @match_types;
  if ( $prompt =~ /^(:)(.*)/ || $prompt =~ /^(.*?: )(.*)/ || $prompt =~ /^(.*?:)(.*)/ ) {
    $prompt = $1;
    $str = $2;
  }
  my $prompt_len = length($prompt);
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
# tab completion is broken and undocumented
#    if ( $ch eq "\b" || $ch eq "\c?" ) {
#      if ( $str ne '' ) {
#        chop $str;
#        if ( length($str) < length($tab_match_str) ) {
#          chop $tab_match_str;
#        }
#      } else {
#        $tab_match_str = '';
#        $tab_cnt = 0;
#      }
#      &draw_prompt("$prompt$str");
#      next;
#    }
    if ( $ch eq "\cu" ) {
      $str = substr($str, $cur_pos - $prompt_len);
      $tab_match_str = '';
      $tab_cnt = 0;
      $cur_pos = $prompt_len;
      &draw_prompt_cur("$prompt$str");
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
# This code was causing problems and was undocumented.
#    if ( $ch eq "\cw" ) {
#      if ( $str eq '' ) {
#        chop $str;
#        beep();
#        next;
#      }
#      if ( $str =~ s/^(.*\s+)\S+\s+$/$1/ ) {
#        &draw_prompt("$prompt$str");
#        next;
#      }
#      if ( $str =~ s/^.*\s+$// ) {
#        &draw_prompt("$prompt$str");
#        next;
#      }
#      if ( $str =~ s/^(.*\s+).*/$1/ ) {
#        &draw_prompt("$prompt$str");
#        next;
#      }
#      $str = "";
#      &draw_prompt("$prompt$str");
#      next;
#    }
    if ( $ch eq KEY_BACKSPACE || $ch eq "\b" || $ch eq "\c?" ) {
      if ( $cur_pos > $prompt_len ) {
        $cur_pos--;
        substr($str, $cur_pos - $prompt_len, 1, "");
        &draw_prompt_cur("$prompt$str");
        next;
      }
    }
    if ( $ch eq KEY_LEFT ) {
      if ( $cur_pos > $prompt_len ) {
        $cur_pos -= 1;
      }
      &draw_prompt_cur("$prompt$str");
      next;
    }
    if ( $ch eq KEY_RIGHT ) {
      if ( $cur_pos < length("$prompt$str") ) {
        $cur_pos += 1;
      }
      &draw_prompt_cur("$prompt$str");
      next;
    }
    if ( ! &is_printable($ch) ) {
      next;
    }
    if ( &is_printable($ch) ) {
      substr($str, $cur_pos - $prompt_len, 0, $ch);
      $cur_pos++;
    }
    &draw_prompt_cur("$prompt$str");
  }
  noecho();
  curs_set(0);
  if ( $mode ne 'project' && $str eq '' ) { beep(); }
  if ( ! $str =~ /^:!/ ) {
    $str =~ s/"/\\"/g;
    $str =~ s/^\s+//;
    $str =~ s/\s+$//;
  }
  return $str;
}

return 1;
