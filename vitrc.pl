# Copyright 2013, Scott Kostyshak

sub parse_vitrc {
  my $vitrc = glob("~/.vitrc");
  if ( open(IN,"<$vitrc") ) {
    while (<IN>) {
      chop;
      my $parse_error = "ERROR: incorrect key bind line in .vitrc:\n  $_";
      if ( $_ =~ s/^map// ) {
        my($scut, $cmd) = split(/=/, $_, 2);

        my $skey;
        if ($scut =~ s/ ([^ ]+)$//) {
          $skey = $1;
        }
        else {
          print STDERR "$parse_error";
          exit(1);
        }

        my $internal_flag;
	my $reread_flag;
        my $wait_flag;
        unless (GetOptionsFromString($scut,
          "internal|i" => \$internal_flag,
          "reread|r" => \$reread_flag,
          "wait|w"   => \$wait_flag)) {
            print STDERR "$parse_error";
            exit(1);
        }
        my $wait = 'no-wait';
        if ($wait_flag) {
          $wait = 'wait';
        }
        $skey = eval "\"$skey\"";
        if ($internal_flag) {
          $cmd = eval "\"$cmd\"";
        }
        my @attributes = ($cmd, $wait, $reread_flag, $internal_flag);
        $shortcuts{$skey} = \@attributes;
      }
    }
    close(IN);
  }
}

return 1;

