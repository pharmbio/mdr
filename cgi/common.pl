my $WADM = 'wesley.schaal@farmbio.uu.se';
my $WNAM = 'wes';
#my @link = qw(Patients patient.cgi Infections infection.cgi Antibiotics antibio.cgi Config config.cgi);
my @link = qw(Accessions getacc.cgi Config config.cgi);

sub ShowHead {
    $headed++;
    my @lnx = @link; Fail("Header trouble: @lnx") unless $#lnx % 2;
    my ($v, $k);

    $\="\n";
    print header();
    print start_html(-title=>"$appl",
		          author=>$WADM,
		          'bgcolor="#FFFFFF"');
    print '<center><font color="555555">[';
    print a({href=>'.'},'MDR');
    while($k = shift(@lnx)) {
	Fail("Header trouble: @lnx") unless $v = shift(@lnx);
	print ' | ' . a({href=>"$v"},"$k");
    }
    print ' ]</font>';
    print '<h3><img src="img/farmbio.png"';
    print 'alt="<logo>"></h3></center>'
}


sub ShowFoot {
    my @lnx = @link; Fail("Footer trouble: @lnx") unless $#lnx % 2;
    my ($v, $k);
    @m = (localtime((stat($0))[9]))[3..5];
    $m = sprintf("%04d-%02d-%02d",$m[2]+1900,$m[1]+1,$m[0]);
    print br({clear=>'all'}),hr({noshade=>1});
    print "URL : self_url()", br if $D;
    print font({size=>'-1'},'URL: ' . url() .
	       br . 'Copyright &copy; 2017 pharmb.io. All rights reserved.' .
	       br . "Last modified: $m by " .
	       a({href=>"mailto:$WADM"},$WNAM) .
	       #br . a({href=>'contacts', target=>'_new'},'Contacts') .
	       br .'Nav: [ ' .
	       a({href=>'.'},'MDR'));
    while($k = shift(@lnx)) {
	Fail("Footer trouble: @lnx") unless $v = shift(@lnx);
	print font({size=>'-1'}," | " . a({href=>"$v"},"$k"));
    }
    print font({size=>'-1'},' ] ');
    print end_html;
}


sub Fail {
    #ShowHead(); # check for dup?
    ($reason) = @_;
    print h2("Error: &nbsp; $reason.");
    print p('Please contact ' .
	        a({href=>"mailto:$WADM?subject=Error on " . url(-absolute=>1) .
		          '&body=Time: ' . localtime() . '%0AError: ' .
			     $reason . '%0A%0A'},$WNAM) .
	        ' if you think you have found an error.');
    print p('Return to ' . a({href=>referer()},'Originating Page') . "\?\n");
    print end_html;
    exit 0;
}

1;
