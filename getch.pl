
sub getch_loop {
  while (1) {
    my $ch = $report_win->getch();
    $refresh_needed = 0; 
    $reread_needed = 0; 
    $error_msg = '';
    $feedback_msg = '';

    CASE: {

      if ( $ch eq '0' ) {
        $task_selected_idx = 0;
        $display_start_idx = 0;
        $refresh_needed = 1;
        last CASE;
      }

      if ( $ch =~ /^\d$/ ) {
        &cmd_line(":$ch");
        last CASE;
      }

      if ( $ch eq 'a' ) {
        &task_add();
        last CASE;
      }

      if ( $ch eq 'A' ) {
        &task_annotate();
        last CASE;
      }

      if ( $ch eq 'c' ) {
        &task_change();
        last CASE;
      }

      if ( $ch eq 'D' ) {
        &task_denotate();
        last CASE;
      }

      if ( $ch eq 'd' ) {
        if ( grep(/^Complete\s*$/,@report_header_tokens) ) { # FIXME: really, good enough?
          $error_msg = "Error: task has already been completed.";
          $refresh_needed = 1;
          last CASE;
        }
        &task_done();
        last CASE;
      }

      if ( $ch eq "e" ) {
        &shell_exec("task $report2taskid[$task_selected_idx] edit",'wait');
        $reread_needed = 1;
        last CASE;
      }

      if ( $ch eq 'f' ) {
        &task_filter();
        last CASE;
      }

      if ( $ch eq 'G' ) {
        $task_selected_idx = $#report_tokens;
        if ( $display_start_idx + $REPORT_LINES <= $#report_tokens ) { 
          $display_start_idx = $task_selected_idx - $REPORT_LINES + 1;
        }
        $refresh_needed = 1;
        last CASE;
      }

      if ( $ch eq 'h' ) {
        &task_set_prio('H');
        last CASE;
      }

      if ( $ch eq 'H' ) {
        $task_selected_idx = $display_start_idx;
        $refresh_needed = 1;
        last CASE;
      }


      if ( $ch eq 'j' || $ch eq KEY_DOWN || $ch eq ' ' ) {
        if ( $task_selected_idx >= $#report_tokens ) { 
          beep;
          last CASE;
        }
        $task_selected_idx++;
        if ( $task_selected_idx - $REPORT_LINES >= $display_start_idx ) {
          $display_start_idx++;
        }
        $refresh_needed = 1;
        last CASE;
      }  

      if ( $ch eq 'k' || $ch eq KEY_UP ) {
        if ( $task_selected_idx == 0 ) {
          beep;
          last CASE;
        }
        $task_selected_idx--;
        if ( $task_selected_idx < $display_start_idx ) {
          $display_start_idx--;
        }
        $refresh_needed = 1;
        last CASE;
      }  

      if ( $ch eq 'L' ) {
        $task_selected_idx = $display_start_idx + $REPORT_LINES - 1;
        if ( $task_selected_idx >= $#report_tokens-1 ) { $task_selected_idx = $#report_tokens; }
        $refresh_needed = 1;
        last CASE;
      }

      if ( $ch eq 'l' ) {
        &task_set_prio('L');
        last CASE;
      }

      if ( $ch eq 'M' ) {
        $task_selected_idx = $display_start_idx + int($REPORT_LINES / 2);
        if ( $display_start_idx + $REPORT_LINES > $#report_tokens ) { 
          $task_selected_idx = $display_start_idx + int(($#report_tokens - $display_start_idx) / 2);
        }
        $refresh_needed = 1;
        last CASE;
      }

      if ( $ch eq 'm' ) {
        &task_set_prio('M');
        last CASE;
      }

      if ( $ch eq 'N' && $input_mode eq 'search' ) {
        &do_search('N');
        $refresh_needed = 1;
        last CASE;
      }

      if ( $ch eq 'n' && $input_mode eq 'cmd' ) {
        &task_set_prio('');
        last CASE;
      }

      if ( $ch eq 'n' && $input_mode eq 'search' ) {
        &do_search('n');
        $refresh_needed = 1;
        last CASE;
      }

      if ( $ch eq 'p' ) {
        &task_set_project();
        last CASE;
      }

      if ( $ch eq 'u' ) {
        &shell_exec('task undo','wait');
        $reread_needed = 1;
        last CASE;
      }

      if ( $ch eq 'Z' && $prev_ch eq 'Z' ) {
        return;
      } 

      if ( $ch eq '/' ) {
        $search_direction = 1;
        &start_search();
        last CASE;
      }

      if ( $ch eq '?' ) {
        $search_direction = 0;
        &start_search();
        last CASE;
      }

      if ( $ch eq ':' ) {
        &cmd_line(':');
        last CASE;
      }

      if ( $ch eq '=' || $ch eq "\n" ) {
        if ( $current_command eq 'summary' ) {
          my $p = $report_tokens[$task_selected_idx][0];
          $p =~ s/(.*?)\s+.*/$1/;
          $p =~ s/\(none\)//;
          $current_command = "ls proj:$p";
          $reread_needed = 1;
        } else { 
          &shell_exec("task $report2taskid[$task_selected_idx] info",'wait');
        }
        last CASE;
      }

      if ( $ch eq "\cb" || $ch eq KEY_PPAGE ) {
        $display_start_idx -= $REPORT_LINES;
        $task_selected_idx -= $REPORT_LINES;
        if ( $display_start_idx < 0 ) { $display_start_idx = 0; }
        if ( $task_selected_idx < 0 ) { $task_selected_idx = 0; }
        $refresh_needed = 1;
        last CASE;
      }

      if ( $ch eq "\cf" || $ch eq KEY_NPAGE ) {
        $display_start_idx += $REPORT_LINES;
        $task_selected_idx += $REPORT_LINES;
        if ( $task_selected_idx > $#report_tokens ) { 
          $display_start_idx = $#report_tokens; 
          $task_selected_idx = $#report_tokens; 
        }
        $refresh_needed = 1;
        last CASE;
      }

      if ( $ch eq "\cl" ) {
        endwin();
        &init_curses('refresh');
        &read_report('refresh');
        if ( $task_selected_idx > $display_start_idx + $REPORT_LINES - 1 ) { 
          $display_start_idx = $task_selected_idx - $REPORT_LINES + 1;
        }
        &draw_screen();
        last CASE;
      }

      if ( $ch eq "\e" ) {
        $error_msg = '';
        $feedback_msg = '';
        $refresh_needed = 1;
        $input_mode = 'cmd';
        last CASE;
      }
      if ( $ch eq 'Z' ) { last CASE; }
      if ( $ch eq "410" ) { last CASE; } # FIXME resize
      if ( $ch eq '-1' ) { last CASE; }
      beep();
    }
    if ( $ch ne '/' && $ch ne '?' && $ch ne 'n' && $ch ne 'N' ) {
      $input_mode = 'cmd';
    }
    $prev_ch = $ch;
    if ( $reread_needed ) { &read_report('refresh'); }
    if ( $refresh_needed || $reread_needed ) { &draw_screen(); }

  }
}

return 1;
