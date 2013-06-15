
sub vit_cmd_line {
  my $cmd = &prompt_str(":");

  if ( $cmd eq '' ) { 
    &draw_prompt_line('');
    return 0;
  }

  if ( $cmd eq 'q' ) { 
    endwin();
    exit();
  }

  if ( $cmd =~ /^s\/(.*?)\/(.*)\/$/ || $cmd =~ /^%s\/(.*?)\/(.*)\/$/ ) {
    my ($old,$new) = ($1,$2);
    my $rtn = &task_modify("/$old/$new/");    
    return $rtn;
  }

  $error_msg = "$cmd: command not found";
  &draw_error_msg();
  return 0;

}

return 1;
