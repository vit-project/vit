
sub start_search {
  my $ch = $_[0];
  if ( $search_direction == 1 ) {
    $search_pat = '/';
  } else {
    $search_pat = '?';
  }
  &draw_prompt($search_pat);
  echo();
  curs_set(1);
  GETCH: while (1) {
    my $ch = $prompt_win->getch();
    if ( $ch eq "\ch" ) {
      if ( length($search_pat) > 1 ) { chop $search_pat; } 
      &draw_prompt($search_pat);
      next GETCH;
    }
    if ( $ch eq "\cu" ) {
      if ( $search_direction == 1 ) {
        $search_pat = '/';
      } else {
        $search_pat = '?';
      }
      &draw_prompt($search_pat);
      next GETCH;
    }
    if ( $ch eq "\e" ) {
      &draw_prompt('');
      noecho();
      curs_set(0);
      return;
    }
    if ( $ch eq "\n" ) {
      last GETCH;
    }
    $search_pat .= $ch;
    &draw_prompt($search_pat);
  }
  noecho();
  curs_set(0);
  $search_pat = substr($search_pat, 1);
  if ( $search_pat eq '' ) { 
    $search_pat = '';
    &draw_prompt('');
    beep();
    return;
  }
  $refresh_needed = 1;
  if ( ! &do_search('n') ) {
    return;
  }
  $input_mode = 'search';
  return;
}

#------------------------------------------------------------------

sub do_search {
  my $ch = $_[0];
  my $rtn = &do_inner_search($ch);
  if ( $rtn == 1 ) {
    if ( $task_selected_idx - $display_start_idx >= $REPORT_LINES ) {
      $display_start_idx = $task_selected_idx - $REPORT_LINES + 1;
    } elsif ( $task_selected_idx < $display_start_idx ) {
      $display_start_idx = $task_selected_idx; 
    }
    return 1;
  } else {
    $error_msg = "Pattern not found: $search_pat";
    $search_pat = '';
    beep();
    return 0;
  } 
  return 0;
}

#------------------------------------------------------------------

sub do_inner_search {
  my $ch = $_[0];
  if ( $search_direction == 1 && $ch eq 'n' || $search_direction == 0 && $ch eq 'N' ) {
    for ( my $i = $task_selected_idx + 1; $i <= $#report_lines; $i++ ) {
      if ( $report_lines[$i] =~ /$search_pat/i ) {
         $task_selected_idx = $i;
         return 1;
      }
    }
    &draw_prompt('Search hit BOTTOM, continuing at TOP');
    usleep($error_delay);
    for ( my $i = 0; $i < $task_selected_idx; $i++ ) {
      if ( $report_lines[$i] =~ /$search_pat/i ) {
        $task_selected_idx = $i;
        return 1;
      }
    }
    if ( $report_lines[$task_selected_idx] =~ /$search_pat/i ) { return 1; }
    return 0;
  }
  if ( $search_direction == 1 && $ch eq 'N' || $search_direction == 0 && $ch eq 'n' ) {
    for ( my $i = $task_selected_idx - 1; $i >= 0; $i-- ) {
      if ( $report_lines[$i] =~ /$search_pat/i ) {
         $task_selected_idx = $i;
        return 1;
      }
    }
    &draw_prompt('Search hit TOP, continuing at BOTTOM');
    usleep($error_delay);
    for ( my $i = $#report_lines; $i > $task_selected_idx; $i-- ) {
      if ( $report_lines[$i] =~ /$search_pat/i ) { 
        $task_selected_idx = $i;
        return 1;
      }
    }
    if ( $report_lines[$task_selected_idx] =~ /$search_pat/i ) { return 1; }
    return 0;
  }
  return -1;
}

return 1;
