
sub set_env {
  $ENV{'PATH'} = "$ENV{'PATH'}:$ENV{'HOME'}/bin";
  if ( $ENV{'TERM'} =~ /^xterm/ ) {
    &audit("ENV TERM=xterm-256color");
    $ENV{'TERM'} = 'xterm-256color';
  } else {
    print "fatal error: 256 color xterm required\n";
    exit;
  }
  if ( $titlebar ) {
    &audit("ENV set titlebar");
    open(TTY, ">>/dev/tty");
    print TTY "\e]0;$version\cg\n";
    close(TTY);
  }
}

return 1;
