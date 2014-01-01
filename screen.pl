# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2014, Scott Kostyshak

sub draw_screen {
  my ($x,$t,$fg,$bg,$cp,$str);
  my $line = 0;

  $header_win->attron(COLOR_PAIR($COLOR_HEADER));
  &set_attron($header_win,$header_attrs);
  CASE: {
    if ( $current_command eq 'summary' && $num_projects == 1 ) {
      $str = '1 project';
      last CASE;
    }
    if ( $current_command eq 'summary' ) {
      $str = "$num_projects projects";
      last CASE;
    }
    if ( $num_tasks == 1 ) {
      $str = '1 task shown';
      last CASE;
    }
    $str = "$num_tasks tasks shown";
  }
  &draw_header_line(0,"task $current_command",$str);
  CASE: {
    if ( $current_command eq 'summary' && $num_tasks == 1 ) {
      $str = '1 task';
      last CASE;
    }
    if ( $current_command eq 'summary' ) {
      $str = "$num_tasks tasks";
      last CASE;
    }
    if ( $tasks_completed == 1 ) {
      $str = '1 task completed';
      last CASE;
    }
    $str = "$tasks_completed tasks completed";
  }
  &draw_header_line(1,$convergence,$str);
  &set_attroff($header_win,$header_attrs);
  $header_win->attroff(COLOR_PAIR($COLOR_HEADER));

  $header_win->attron(COLOR_PAIR($COLOR_REPORT_HEADER));
  $x = 1;
  for $t (0 .. $#report_header_tokens) {
    &set_attron($header_win,$report_header_attrs[$t]);
    $header_win->addstr(2,$x,$report_header_tokens[$t]);
    &set_attroff($header_win,$report_header_attrs[$t]);
    $x += length($report_header_tokens[$t]);
  }
  $str = ' ' x ($REPORT_COLS - $x + 1);
  &set_attron($header_win,$report_header_attrs[$#report_header_attrs]);
  $header_win->addstr(2,$x,$str);
  &set_attroff($header_win,$report_header_attrs[$#report_header_attrs]);
  $header_win->attroff(COLOR_PAIR($COLOR_REPORT_HEADER));
  $header_win->refresh();

  #debug("DRAW lines=$REPORT_LINES start=$display_start_idx cur=$task_selected_idx");
  for my $i ($display_start_idx .. ($display_start_idx+$REPORT_LINES-1)) {
    $cp = 0;
    if ( $i > $#report_tokens ) {
      $str = '~' . ' ' x ($COLS-2);
      $report_win->attron(COLOR_PAIR($COLOR_EMPTY_LINE));
      $report_win->attron(A_BOLD);
      $report_win->addstr($line,0,$str);
      $report_win->attroff(A_BOLD);
      $report_win->attroff(COLOR_PAIR($COLOR_EMPTY_LINE));
      $line++;
      next;
    }
    &draw_report_line($i,$line,'with-selection');
    $line++;
  }
  $report_win->refresh();
  if ( $display_start_idx == 0 ) {
    $cursor_position = 'Top';
  } elsif ( $display_start_idx + $REPORT_LINES >= $#report_tokens + 1 ) {
    $cursor_position = 'Bot';
  } else {
    $cursor_position = int($task_selected_idx/$#report_tokens*100) . '%';
  }
  CASE: {
    if ( $error_msg ne '' ) {
      &draw_error_msg();
      last CASE;
    }
    if ( $feedback_msg ne '' ) {
      &draw_feedback_msg();
      last CASE;
    }
    if ( $input_mode eq 'search' && $search_direction == 1 ) {
      &draw_prompt_line("/$search_pat");
      last CASE;
    }
    if ( $input_mode eq 'search' && $search_direction == 0 ) {
      &draw_prompt_line("?$search_pat");
      last CASE;
    }
    &draw_prompt_line('');
  }
  if ( $flash_convergence ) {
    &flash_convergence();
    $flash_convergence = 0;
    $prev_convergence = $convergence;
  }

}

return 1;

