# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2014, Scott Kostyshak

#------------------------------------------------------------------

sub prompt_quit {
  my $yes;
  $yes = &prompt_y("Quit?");
  if ( ! $yes ) {
    &draw_prompt_line('');
    return;
  }
  endwin();
  exit();
}

#------------------------------------------------------------------

sub task_add {
  my $str = &prompt_str("Add: ");
  if ( $str eq '' ) {
    &draw_prompt_line('');
    return;
  }
  my ($es,$result) = &task_exec("add \"$str\"");
  if ( $es != 0 ) {
    $error_msg = $result;
    &draw_error_msg();
    return;
  }
  $feedback_msg = $result;
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub task_annotate {
  my $id = $report2taskid[$task_selected_idx];
  my $str = &prompt_str("Annotate: ");
  if ( $str eq '' ) {
    &draw_prompt_line('');
    return;
  }
  my ($es,$result) = &task_exec("$id annotate \"$str\"");
  if ( $es != 0 ) {
    $error_msg = $result;
    &draw_error_msg();
    return;
  }
  $feedback_msg = "Annotated task $id.";
  &draw_feedback_msg();
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub task_den_or_del {
  my ($ch, $str, $yes);
  my $id = $report2taskid[$task_selected_idx];
  for my $t (0 .. $#{ $report_tokens[$task_selected_idx] } ) {
    $str .= "$report_tokens[$task_selected_idx][$t]";
  }
  my $target = ( $str !~ s/^\s*\d+\/\d+\/\d+\s+// )
             ? "task"
             : "annotation";
  $str =~ s/\s+$//;
  $yes = &prompt_y("Delete current $target? ");
  if ( ! $yes ) {
    &draw_prompt_line('');
    return;
  }
  my ($es,$result) = ($target eq "annotation")
                   ? &task_exec("$id denotate \"$str\"")
                   : &task_exec("$id delete rc.confirmation:no");
  if ( $es != 0 ) {
    $error_msg = $result;
    &draw_error_msg();
    return;
  }
  $feedback_msg = "Deleted $target.";
  &draw_feedback_msg();
  &flash_current_task();
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub task_done {
  my ($ch, $str, $yes);
  my $id = $report2taskid[$task_selected_idx];
  $yes = &prompt_y("Mark task $id done? ");
  if ( ! $yes ) {
    &draw_prompt_line('');
    return;
  }
  my ($es,$result) = &task_exec("$id done");
  if ( $es != 0 ) {
    $error_msg = $result;
    &draw_error_msg();
    return;
  }
  $feedback_msg = "Marked task done.";
  &draw_feedback_msg();
  &flash_current_task();
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub task_filter {
  my ($c, $f);
  if ( $current_command =~ /(.*?)\s+(.*)/ ) {
    ($c,$f) = ($1,$2);
  } else {
    $c = $current_command;
    $f = '';
  }
  my $str = &prompt_str("Filter: $f");
  if ( $str eq '' ) {
    &draw_prompt_line('');
    $current_command = $c;
    if ( $f ne '' ) { $reread_needed = 1; }
    return;
  }
  $prev_command = $current_command;
  $current_command = "$c $str";
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub task_modify {
  my $args = $_[0];
  my $id = $report2taskid[$task_selected_idx];
  &shell_exec("$task $id modify \"$args\"",'wait');
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub task_modify_prompt {
  my $id = $report2taskid[$task_selected_idx];
  my $str = &prompt_str("Modify: ");
  if ( $str eq '' ) {
    &draw_prompt_line('');
    return;
  }
  &task_modify("$str");
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub task_set_priority {
  my $id = $report2taskid[$task_selected_idx];
  my $prio = &task_info('Priority');
  if ( $prio eq '' ) {
    $prio = 'N';
  }
  my $p = &prompt_chr("Change priority (l/m/h/n): ");
  $p = uc($p);
  if ( $p ne $prio && $p =~ /[LMHN]/ ) {
    if ( $p eq 'N' ) {
      $p = '';
    }
    my ($es,$result) = &task_exec("$id modify prio:$p");
    if ( $es != 0 ) {
      $error_msg = $result;
      &draw_error_msg();
      return;
    }
    $feedback_msg = "Modified task $id.";
    &flash_current_task();
    $reread_needed = 1;
  }
  else {
    &draw_prompt_line('');
    return;
  }
}

#------------------------------------------------------------------

sub task_set_project {
  my $id = $report2taskid[$task_selected_idx];
  my $p = &prompt_str("Project: ");
  if ( $p eq '' ) {
    &draw_prompt_line('');
    return;
  }
  my $proj = &task_info('Project');
  if ( $p eq $proj ) {
    beep();
    return;
  }
  my ($es,$result) = &task_exec("$id modify proj:$p");
  if ( $es != 0 ) {
    $error_msg = $result;
    &draw_error_msg();
    return;
  }
  $feedback_msg = "Modified task $id.";
  &flash_current_task();
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub shell_command {
  my $args = $_[0];
  my ($opts, $cmd);
  if ( $args =~ /([^ ]*) (.+)/ ) {
    $opts = $1;
    $cmd = $2;
  }
  else {
    $error_msg = "Empty shell command for ':!'. See help (:h).";
    &draw_error_msg();
    return;
  }

  my $wait = "no-wait";
  foreach my $l ( split //, $opts ) {
    if ( $l eq 'r' ) {
      $reread_needed = 1;
    } elsif ( $l eq 'w' ) {
      $wait = "wait";
    } else {
      $error_msg = "$l is not a valid command option to ':!'. See help (:h).";
      &draw_error_msg();
      return;
    }
  }

  $cmd =~ s/%TASKID/$report2taskid[$task_selected_idx]/g;
  $cmd =~ s/%TASKARGS/$current_command/g;

  &shell_exec($cmd,"$wait");
}

return 1;
