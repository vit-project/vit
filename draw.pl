# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2014, Scott Kostyshak

sub draw_header_line {
  my ($row,$lhs,$rhs) = @_;
  my $str = ' ' x $COLS;
  $header_win->addstr($row, 0, $str);
  $header_win->addstr($row, 0, $lhs);
  $header_win->addstr($row, $COLS - length($rhs), $rhs);
  $header_win->refresh();
}

#------------------------------------------------------------------

sub draw_prompt_line {
  my ($lhs) = @_;
  $prompt_win->addstr(0, 0, $lhs);
  $prompt_win->clrtoeol();
  $prompt_win->addstr(0, $COLS - length($cursor_position) - 1, $cursor_position);
  $prompt_win->refresh();
}

#------------------------------------------------------------------

sub draw_prompt {
  my ($lhs) = @_;
  $prompt_win->addstr(0, 0, $lhs);
  $prompt_win->clrtoeol();
  $prompt_win->refresh();
}

#------------------------------------------------------------------

sub draw_prompt_cur {
  my ($lhs) = @_;
  $prompt_win->addstr(0, 0, $lhs);
  $prompt_win->clrtoeol();
  $prompt_win->move(0, $cur_pos);
  $prompt_win->refresh();
}

#------------------------------------------------------------------

sub draw_error_msg {
  beep();
  &audit("ERROR $error_msg");
  $prompt_win->addstr(0, 0, ' ');
  $prompt_win->clrtoeol();
  $prompt_win->attron(COLOR_PAIR($COLOR_ERRORS));
  $prompt_win->attron(A_BOLD);
  $prompt_win->addstr(0, 0, $error_msg);
  $prompt_win->attroff(A_BOLD);
  $prompt_win->attroff(COLOR_PAIR($COLOR_ERRORS));
  $prompt_win->attron(COLOR_PAIR($COLOR_HEADER));
  $prompt_win->addstr(0, $COLS - length($cursor_position) - 1, $cursor_position);
  $prompt_win->refresh();
}

#------------------------------------------------------------------

sub draw_feedback_msg {
  my $len = length($feedback_msg);
  my $start = ($COLS/2) - ($len/2) - 3;
  $prompt_win->addstr(0, 0, ' ');
  $prompt_win->clrtoeol();
  $prompt_win->addstr(0, $start, $feedback_msg);
  $prompt_win->addstr(0, $COLS - length($cursor_position) - 1, $cursor_position);
  $prompt_win->refresh();
}

#------------------------------------------------------------------

sub draw_report_line {
  my ($i,$line,$mode) = @_;
  my ($x, $t, $cp, $str);
  $x = 0;
  if ( $mode eq 'with-selection' && $i == $task_selected_idx ) {
    $report_win->attron(COLOR_PAIR($COLOR_SELECTION));
    &set_attron($report_win,$selection_attrs);
  }
  for $t (0 .. $#{ $report_tokens[$i] } ) {
    if ( $mode eq 'without-selection' || $i != $task_selected_idx ) {
      my $fg = $report_colors_fg[$i][$t];
      my $bg = $report_colors_bg[$i][$t];
      $cp = &get_color_pair($fg,$bg);
      $report_win->attron(COLOR_PAIR($cp));
    }
    #if ( $t == 0 ) { debug("DRAW tok=$line.$t cp=$cp \"$report_tokens[$i][$t]\""); }
    &set_attron($report_win,$report_attrs[$i][$t]);
    $report_win->addstr($line,$x,$report_tokens[$i][$t]);
    &set_attroff($report_win,$report_attrs[$i][$t]);
    if ( $mode eq 'without-selection' || $i != $task_selected_idx ) {
      $report_win->attroff(COLOR_PAIR($cp));
    }
    $x += length($report_tokens[$i][$t]);
  }
  $str = ' ' x ($REPORT_COLS - $x);
  if ( $mode eq 'without-selection' || $i != $task_selected_idx ) {
    $report_win->attron(COLOR_PAIR($cp));
  }
  &set_attron($report_win,$report_attrs[$i][$#{ $report_tokens[$i] }]);
  $report_win->addstr($line,$x,$str);
  &set_attroff($report_win,$report_attrs[$i][$#{ $report_tokens[$i] }]);
  if ( $mode eq 'with-selection' && $i == $task_selected_idx ) {
    $report_win->attroff(COLOR_PAIR($COLOR_SELECTION));
    &set_attroff($report_win,$selection_attrs);
  } else {
    $report_win->attroff(COLOR_PAIR($cp));
  }
}

#------------------------------------------------------------------

sub flash_current_task {
  my ($x, $t, $cp, $str);
  my $i = $task_selected_idx;
  my $line = $task_selected_idx - $display_start_idx;

  &draw_report_line($i,$line,'without-selection');
  $report_win->refresh();
  usleep($flash_delay);

  $report_win->addstr($line,0,' ');
  $report_win->clrtoeol();
  $report_win->refresh();
  usleep($flash_delay);

  &draw_report_line($i,$line,'without-selection');
  $report_win->refresh();
  usleep($flash_delay);

  $report_win->addstr($line,0,' ');
  $report_win->clrtoeol();
  $report_win->refresh();
  usleep($flash_delay);

  &draw_report_line($i,$line,'without-selection');
  $report_win->refresh();
  usleep($flash_delay);
}

#------------------------------------------------------------------

sub flash_convergence {
  $header_win->attron(COLOR_PAIR($COLOR_HEADER));
  &set_attron($header_win,$header_attrs);
  &draw_header_line(1,'',"$tasks_completed tasks completed");
  usleep($flash_delay);
  &draw_header_line(1,$convergence,"$tasks_completed tasks completed");
  usleep($flash_delay);
  &draw_header_line(1,'',"$tasks_completed tasks completed");
  usleep($flash_delay);
  &draw_header_line(1,$convergence,"$tasks_completed tasks completed");
  usleep($flash_delay);
  &set_attroff($header_win,$header_attrs);
  $header_win->attroff(COLOR_PAIR($COLOR_HEADER));
}

#------------------------------------------------------------------

sub set_attron {
  my ($win,$attr) = @_;
  if ( ! defined $attr ) { return; }
  if ( $attr =~ /underline/ ) {
    $win->attron(A_UNDERLINE);
  }
  if ( $attr =~ /bold/ ) {
    $win->attron(A_BOLD);
  }
}

#------------------------------------------------------------------

sub set_attroff {
  my ($win,$attr) = @_;
  if ( ! defined $attr ) { return; }
  if ( $attr =~ /underline/ ) {
    $win->attroff(A_UNDERLINE);
  }
  if ( $attr =~ /bold/ ) {
    $win->attroff(A_BOLD);
  }
  if ( $attr =~ /inverse/ ) {
    $win->attroff(A_REVERSE);
  }
  if ( $attr =~ /standout/ ) {
    $win->attroff(A_STANDOUT);
  }
}

return 1;
