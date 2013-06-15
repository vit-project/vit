
sub task_done {
  my ($ch, $str, $yes);
  my $id = $report2taskid[$task_selected_idx];
  $yes = &prompt_y("Mark task $id done? ");
  if ( ! $yes ) {
    &draw_prompt_line('');
    return;
  }
  &audit("EXEC task $id done 2>&1");
  open(IN,"task $id done 2>&1 |");
  my $result = '';
  while(<IN>) {
    chop;
    $_ =~ s/\x1b.*?m//g; # decolorize
    if ( $_ =~ /^\w+ override:/ ) { next; }
    $result .= "$_ ";
  }
  close(IN);
  if ( $result =~ s/.*(Could not lock.*pending.data\'.)\s*/$1/ ) {
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

sub task_add {
  my $id = $report2taskid[$task_selected_idx];
  my $descr = &prompt_str("Add: ");
  if ( $descr eq '' ) { 
    &draw_prompt_line('');
    return; 
  }
  &audit("EXEC task add \"$descr\" 2>&1");
  open(IN,"task add \"$descr\" 2>&1 |");
  my $result = '';
  while(<IN>) {
    chop;
    $_ =~ s/\x1b.*?m//g; # decolorize
    if ( $_ =~ /^Created task/ ) { 
      $result = $_; 
      last;
    }
  }
  close(IN);
  if ( $result =~ s/.*(Could not lock.*pending.data\'.)\s*/$1/ ) {
    $error_msg = $result;
    &draw_error_msg();
    return;
  }
  $feedback_msg = $result;
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub task_change {
  my $id = $report2taskid[$task_selected_idx];
  my $descr = &prompt_str("Change: ");
  if ( $descr eq '' ) { 
    &draw_prompt_line('');
    return; 
  }
  my $rtn = &task_modify("$descr");
  $reread_needed = 1;
}

#------------------------------------------------------------------

sub task_modify {
  my $args = $_[0];
  my $id = $report2taskid[$task_selected_idx];
  &audit("EXEC task $id modify \"$args\" 2>&1");
  open(IN,"task $id modify \"$args\" 2>&1 |");
  my $result = '';
  while(<IN>) {
    chop;
    $_ =~ s/\x1b.*?m//g; # decolorize
    if ( $_ =~ /^\w+ override:/ ) { next; }
    $result .= "$_ ";
  }
  close(IN);
  if ( $result =~ s/.*(Could not lock.*pending.data\'.)\s*/$1/ ) {
    $error_msg = $result;
    &draw_error_msg();
    return;
  }
  if ( $result =~ /Modified 0 tasks./ ) {
    $error_msg = "Modifying task $id failed.";
    &draw_error_msg();
    return
  }
  $feedback_msg = "Modified task $id.";
  $reread_needed = 1;
}

return 1;
