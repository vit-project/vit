# Copyright 2012 - 2013, Steve Rader
# Copyright 2013 - 2018, Scott Kostyshak

sub parse_args {
  while ( @ARGV ) {
    if ( $ARGV[0] eq '--help' || $ARGV[0] eq '-help' || $ARGV[0] eq '-h' ) {
      &usage();
    }
    if ( $ARGV[0] eq '--version' || $ARGV[0] eq '-version' || $ARGV[0] eq '-v' ) {
      print "$version\n";
      exit 0;
    }
    if ( $ARGV[0] eq '--audit' || $ARGV[0] eq '-audit' || $ARGV[0] eq '-a' ) {
      $audit = 1;
      shift @ARGV;
      next;
    }
    if ( $ARGV[0] eq '--titlebar' || $ARGV[0] eq '-titlebar' || $ARGV[0] eq '-t' ) {
      $titlebar = 1;
      shift @ARGV;
      next;
    }
    if ( $ARGV[0] eq '--default-tags' || $ARGV[0] eq '-default-tags' || $ARGV[0] eq '-d' ) {
      shift @ARGV;
      $default_tags = shift @ARGV or die usage();
      $default_tags_add = $default_tags; 
      $default_tags_add =~ s|-[^ ]*||;
      $default_command = "$default_tags $default_command";
      $current_command = $default_command;
      next;
    }
    $cli_args .= "$ARGV[0] ";
    shift @ARGV;
    next;
  }
  if ( $audit ) {
    open(AUDIT, ">", "vit_audit.log") or die "$!";
    open STDERR, '>&AUDIT';

    # flush AUDIT after printing to it
    my $ofh = select AUDIT;
    $| = 1;
    select $ofh;

    print AUDIT "$$ INIT $0 " . join(' ',@ARGV), "\r\n";
    print AUDIT "$$ INIT default tags: $default_tags; default tags for new tasks: $default_tags_add\r\n";
  }
}

#------------------------------------------------------------------

sub usage {
  print "usage: vit [switches] [task_args]\n";
  print "  -audit                        print task commands to vit_audit.log\n";
  print "  -titlebar                     sets the xterm titlebar to \"$version\"\n";
  print "  -default-tags '+tag1 -tag2'   filter by these tags, and add '+' tags to newly created tasks\n";
  print "  -version                      prints the version\n";
  print "  task_args                     any set of task commandline args that print an \"ID\" column\n";
  exit 0;
}

return 1;

