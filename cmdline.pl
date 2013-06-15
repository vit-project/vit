
sub cmd_line {
  my ($prompt) = @_;
  my $str = &prompt_str($prompt);
  if ( $str eq '' ) { 
    &draw_prompt_line('');
    return;
  }
  if ( $str =~ /^\d+$/ ) {
    if ( ! defined $taskid2report[$str] ) { 
       $error_msg = "Error: task number $str not found";
       &draw_error_msg();
       return;
    }
    $task_selected_idx = $taskid2report[$str] - 1;
    if ( $display_start_idx + $REPORT_LINES < $task_selected_idx ) { 
      $display_start_idx = int($task_selected_idx - $REPORT_LINES + ($REPORT_LINES / 2));
    }
    if ( $display_start_idx > $task_selected_idx ) { 
      $display_start_idx = int($task_selected_idx - $REPORT_LINES + ($REPORT_LINES / 2));
      if ( $display_start_idx < 0 ) { 
        $display_start_idx = 0; 
      } elsif ( $display_start_idx > $task_selected_idx) { 
        $display_start_idx = $task_selected_idx;
      }
    }
    &draw_screen();
    return;
  }
  if ( $str =~ /^s\/(.*?)\/(.*)\/$/ || $str =~ /^%s\/(.*?)\/(.*)\/$/ ) {
    my ($old,$new) = ($1,$2);
    my $rtn = &task_modify("/$old/$new/");    
    $reread_needed = 1;
    return;
  }
  if ( $str eq 'help' || $str eq 'h' ) {
    &shell_exec("view $commands_file",'no-wait');
    return;
  }
  if ( $str =~ /^help (.*)/ || $str =~ /^h (.*)/ ) { 
    my $p = $1;
    my $tmp_file = "/tmp/vit-help.$$";
    open(IN,"<$commands_file");
    open(OUT,">$tmp_file");
    print OUT "\n";
    while(<IN>) {
      if ( $_ =~ /$p/ ) { 
        print OUT $_;
      }
    }
    close(IN);
    print OUT "\n";
    close(OUT);
    &shell_exec("view $tmp_file",'no-wait');
    unlink($tmp_file);
    return;
  }
  if ( $str eq 'q' ) { 
    endwin();
    exit();
  }
  if ( grep(/^$str$/,@report_types) ) {
    $prev_command = $current_command;
    $current_command = $str;
    &read_report('init');
    &draw_screen(); 
    return;
  }
  if ( $str =~ /^(.*?) .*/ ) {
    my $s = $1;
    if ( grep(/^$s/,@report_types) ) {
      $prev_command = $current_command;
      $current_command = $str;
      &read_report('init');
      &draw_screen(); 
      return;
    }
  }
  $error_msg = "$str: command not found";
  &draw_error_msg();
  return;
}

return 1;
