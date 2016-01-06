# Copyright 2013 - 2016, Scott Kostyshak

sub parse_vitrc {
  my $vitrc = glob("~/.vitrc");
  if ( open(IN,"<$vitrc") ) {
    while (<IN>) {
      chop;
      my $parse_error = "ERROR: incorrect key bind line in .vitrc:\n $_\n";
      if ( $_ =~ s/^map // ) {
        my($scut, $cmd) = split(/=/, $_, 2);

        my $skey;
        if ($scut =~ s/([^ ]+)$//) {
          $skey = $1;
        }
        else {
          print STDERR "$parse_error";
          exit(1);
        }

        $skey = &replace_keycodes("$skey");
        $cmd = &replace_keycodes("$cmd");

        $skey = eval "\"$skey\"";

        $shortcuts{$skey} = $cmd;
      }
      elsif ( $_ =~ s/^set // ) {
        my($configname, $configval) = split(/=/, $_, 2);
        &audit("CONFIG: user requests to set '$configname' to '$configval'");
        if ($configname eq "burndown") {
          if (!&sanitycheck_bool($configval)) {
            print STDERR "ERROR: boolean config variable '$configname' must ".
                         "be set to 'yes' or 'no'.\n";
            exit(1);
          }
          $burndown = $configval;
        }
      }
    }
    close(IN);
  }
}

#------------------------------------------------------------------

sub replace_keycodes {
  my $str_ = $_[0];

  $str_ =~ s/<F1>/KEY_F(1)/e;
  $str_ =~ s/<F2>/KEY_F(2)/e;
  $str_ =~ s/<F3>/KEY_F(3)/e;
  $str_ =~ s/<F4>/KEY_F(4)/e;
  $str_ =~ s/<F5>/KEY_F(5)/e;
  $str_ =~ s/<F6>/KEY_F(6)/e;
  $str_ =~ s/<F7>/KEY_F(7)/e;
  $str_ =~ s/<F8>/KEY_F(8)/e;
  $str_ =~ s/<F9>/KEY_F(9)/e;
  $str_ =~ s/<F10>/KEY_F(10)/e;
  $str_ =~ s/<F11>/KEY_F(11)/e;
  $str_ =~ s/<F12>/KEY_F(12)/e;

  $str_ =~ s/<Home>/KEY_HOME/e;
  $str_ =~ s/<End>/KEY_END/e;

  $str_ =~ s/<Insert>/KEY_IC/e;
  $str_ =~ s/<Del>/KEY_DC/e;

  $str_ =~ s/<PageUp>/KEY_PPAGE/e;
  $str_ =~ s/<PageDown>/KEY_NPAGE/e;

  $str_ =~ s/<Up>/KEY_UP/e;
  $str_ =~ s/<Down>/KEY_DOWN/e;
  $str_ =~ s/<Right>/KEY_RIGHT/e;
  $str_ =~ s/<Left>/KEY_LEFT/e;

  $str_ =~ s/<Backspace>/KEY_BACKSPACE/e;

  # We don't evaluate these ones (no 'e').
  $str_ =~ s/<Space>/ /;
  $str_ =~ s/<Tab>/\t/;
  $str_ =~ s/<Return>/\n/;
  $str_ =~ s/<Esc>/\e/;

  return $str_;
}

#------------------------------------------------------------------

sub sanitycheck_bool {
  my $bool_ = $_[0];
  if ($bool_ ne "yes" && $bool_ ne "no") {
    return 0;
  }
  else {
    return 1;
  }
}

return 1;

