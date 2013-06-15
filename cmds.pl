
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

sub task_denotate {
  my ($ch, $str, $yes);
  my $id = $report2taskid[$task_selected_idx];
  for my $t (0 .. $#{ $report_tokens[$task_selected_idx] } ) {
    $str .= "$report_tokens[$task_selected_idx][$t]";
  }
  if ( $str !~ s/^\s*\d+\/\d+\/\d+\s+// ) {
    &draw_prompt_line('');
    beep();
    return;
  }
  $str =~ s/\s+$//;
  $yes = &prompt_y("Delete current annotation? ");
  if ( ! $yes ) {
    &draw_prompt_line('');
    return;
  }
  my ($es,$result) = &task_exec("$id denotate \"$str\"");
  if ( $es != 0 ) { 
    $error_msg = $result;
    &draw_error_msg();
    return;
  }
  $feedback_msg = "Deleted annotation.";
  &draw_feedback_msg();
  &flash_current_task();
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub task_change {
  my $id = $report2taskid[$task_selected_idx];
  my $str = &prompt_str("Change: ");
  if ( $str eq '' ) { 
    &draw_prompt_line('');
    return; 
  }
  &task_modify("$str");
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
  my ($es,$result) = &task_exec("$id modify \"$args\"");
  if ( $result =~ /Modified 0 tasks./ ) {
    $error_msg = "Modifying task $id failed.";
    &draw_error_msg();
    return;
  }
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

sub task_set_prio {
  my $p = $_[0];
  my $yes;
  my $id = $report2taskid[$task_selected_idx];
  my $prio = &task_info('Priority');
  if ( $p eq $prio ) { 
    beep();
    return;
  }
  if ( $p eq '' ) { 
    $yes = &prompt_y("Set task ${id}'s priority to none? ");
  } else { 
    $yes = &prompt_y("Set task ${id}'s priority to $p? ");
  }
  if ( ! $yes ) {
    &draw_prompt_line('');
    return;
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

#------------------------------------------------------------------

sub task_set_project {
  my $id = $report2taskid[$task_selected_idx];
  my $p = &prompt_str("Project: ");
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

return 1;
