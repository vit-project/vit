# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2016, Scott Kostyshak

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
  $cur_pos = length($lhs);
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
    my $tok = $report_tokens[$i][$t];
    $report_win->addstr($line,$x,$tok);
    &set_attroff($report_win,$report_attrs[$i][$t]);
    if ( $mode eq 'without-selection' || $i != $task_selected_idx ) {
      $report_win->attroff(COLOR_PAIR($cp));
    }
    $x += length($tok);
  }
  my $repeat_count=($REPORT_COLS - $x);
  if ( $repeat_count < 0 ) {
    # FIXME
    # I added this "if" block when VIT exited with a Perl warning that
    # "VIT fatal error: (converted from warning) Negative repeat count does
    # nothing..."
    # Note that warnings are (purposefully) converted to errors because of
    # using "strict'. There is likely a bug in the algorithm as I'm guessing
    # the original author of this code never intended for the value to be
    # negative. I do not think this is a serious bug, and thus I leave this
    # note as a reminder for if someone takes an in-depth look at the algorithm
    # or decides for other reasons that a refactoring is needed. I can only
    # reproduce this issue with a private dataset and unfortunately it is not
    # the normal case for bugs where one can whittle the dataset down and
    # easily anonymize it. I will keep the dataset to test in the future in
    # case a fix is proposed. The tar where will I keep my private
    # reproduceable dataset is named "vit_negative_repeat.tar.gz".
    # There are other similar situations in the code. To see the FIXMEs that
    # are associated with them, do "git grep bd4a905c".
    # scott k, 2016-05-15
    $repeat_count = 0;
  }
  $str = ' ' x $repeat_count;
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
