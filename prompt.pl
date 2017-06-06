# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2016, Scott Kostyshak

sub prompt_y {
  my $ch = &prompt_chr(@_);
  my $ans = 0;
  if ( $ch eq "y" || $ch eq "Y" ) { $ans = 1; }
  return $ans;
}

#------------------------------------------------------------------
# The following function is, with minor modifications, from
#   https://cpan.rt.develooper.com/Public/Bug/Display.html?id=27335
# TODO:
#   Is there a normal Perl way of doing the following more simple?
sub prompt_u8getch() {
  my $chr = $prompt_win->getch();

  my $cpt = ord($chr);
  if ($chr =~ /\A\d+\z/ || $cpt <= 127) {
    return $chr;
  }
  my $len=1;
     if (($cpt & 0xe0) == 0xc0) { $len = 2; }
  elsif (($cpt & 0xf0) == 0xe0) { $len = 3; }
  elsif (($cpt & 0xf8) == 0xf0) { $len = 4; }
  elsif (($cpt & 0xfc) == 0xf8) { $len = 5; }
  elsif (($cpt & 0xfe) == 0xfc) { $len = 6; }
  else {
    return $chr;
  }
  for my $i (2..$len) {
    my $chri = $prompt_win->getch();
    return $chri if ((ord($chri) & 0xc0) != 0x80);
    $chr .= $chri;
  }
  return decode_utf8($chr);
}

#------------------------------------------------------------------

sub prompt_chr {
  my ($prompt) = @_;
  my $ch;
  echo();
  curs_set(1);
  &draw_prompt($prompt);
  $ch = $prompt_win->getch();
  if ( $ch eq "410" ) {
    # FIXME resize
    # This code chunk is also in getch.pl, except the call to draw_prompt_cur.
    if ( $LINES > 1 ) {
      &audit("Received character 410. Going to refresh.");
      &init_curses('refresh');
      &draw_screen();
    } else {
      &audit("Received character 410, but terminal height ($LINES) too small to
        refresh.");
    }
    $ch = &prompt_chr($prompt);
  }
  noecho();
  curs_set(0);
  return $ch;
}

#------------------------------------------------------------------

sub prompt_str {
  my ($prompt) = @_;
  $cur_pos = length($prompt);
  my $str = '';
  my $tab_cnt = 0;# number of subsequent tab presses (for iterating through completions)
  my $tab_match_str = '';# value of $str upon first press of tab
  my $history_idx = 0;
  my $addedPromptStr = 0;
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
    my $ch = prompt_u8getch();
    if ( $tab_cnt > 0 && $ch ne "\t" && $ch ne "410" ) {
      # When another key than tab is pressed, then the counter is reset.
      # That is, only uninterrupted tab keys cycle through completions.
      # The only exceptions, which allow the continuation of tab cycling, are:
      #   - "410" (resize)
      $tab_cnt = 0;
      $tab_match_str = '';
      #NOTE: no "next" here on purpose
    }
    if ( $ch eq "\cu" ) {
      $str = substr($str, $cur_pos - $prompt_len);
      $cur_pos = $prompt_len;
      &draw_prompt_cur("$prompt$str");
      next;
    }
    if ( $ch eq "\e" || $ch eq "\cg" ) {
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
    if ( $ch eq KEY_UP ) {
      # We treat $history_idx specially because we save the prompt string the
      # first time
      # $#{ $histories{$prompt} } returns -1 if $prompt is not an existing key
      if ( $history_idx > 0 && $history_idx >= $#{ $histories{$prompt} } ) {
        next;
      }
      if ( $history_idx == 0 && $history_idx >= $#{ $histories{$prompt} } + 1 ) {
        next;
      }
      if ( $history_idx == 0 ) {
          if ( $addedPromptStr == 0 ) {
            # don't add sequential duplicates
            if ( $str ne $histories{$prompt}[0] ) {
              $addedPromptStr = 1;
              unshift @{ $histories{$prompt} }, $str;
            }
          }
          else {
            # if the user edits working prompt again, no need to add as separate
            $histories{$prompt}[0] = $str;
          }
      }
      $history_idx++;
      $str = $histories{$prompt}[$history_idx];
      &draw_prompt("$prompt$str");
    }
    if ( $ch eq KEY_DOWN ) {
      if ( $history_idx == 0 ) {
        next;
      }
      $history_idx--;
      $str = $histories{$prompt}[$history_idx];
      &draw_prompt("$prompt$str");
    }
    if ( $ch eq KEY_HOME ) {
      $cur_pos = $prompt_len;
      &draw_prompt_cur("$prompt$str");
    }
    if ( $ch eq KEY_END ) {
      $cur_pos = length("$prompt$str");
      &draw_prompt_cur("$prompt$str");
    }
    # Put hardcoded keys down here since they are the most fragile
    # and could be platform-dependent. If they are defined differently,
    # hopefully they will be matched above first.
    if ( $ch eq 330 ) { # KEY_DELETE is not defined
      if ( $cur_pos >= $prompt_len ) {
        substr($str, $cur_pos - $prompt_len, 1, "");
        &draw_prompt_cur("$prompt$str");
        next;
      }
    }
    if ( $ch eq "410" ) {
      # FIXME resize
      # This code chunk is also in getch.pl, except the call to draw_prompt_cur.
      &audit("Received character 410. Going to refresh");
      &init_curses('refresh');
      &draw_screen();
      &draw_prompt_cur("$prompt$str");
      curs_set(1);
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
  if ( $addedPromptStr == 0 ) {
    # we add if no elements or not a sequential duplicate
    if ( $#{ $histories{$prompt} } < 0 || $str ne $histories{$prompt}[0] ) {
      # do not add an empty string
      if ( $str ne "" ) {
        unshift @{ $histories{$prompt} }, $str;
      }
    }
  }
  else {
    $histories{$prompt}[0] = $str;
  }
  return $str;
}

return 1;
