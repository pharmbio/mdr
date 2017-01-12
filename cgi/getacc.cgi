#!/usr/bin/perl
# Auth: Wesley Schaal, wesley.schaal@farmbio.uu.se
#
#use strict; use warnings;
use DBI; use v5.10;
use CGI qw(:all *table *Tr *td *blockquote -nosticky);
use CGI::Carp qw(fatalsToBrowser);  autoEscape(undef);
#use Getopt::Long qw(:config bundling);
use LWP::Simple;
require "./common.pl";
$appl = 'MDR Bacteria (VR/5011)';
my $NCBI = 'http://www.ncbi.nlm.nih.gov/nuccore';
my $UTIL = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils';

my $dbf = '../data/bacteria.sqlite';
my $dbh = DBI->connect("dbi:SQLite:dbname=$dbf",'','');
my $submit = param('submit');
ShowHead();
ShowForm();
ShowFoot();


sub ShowForm {
    my $sql = 'select genus || " " || species as bact from bacteria';
#    my $sql = 'select genus || " " || species as bact from bacteria where mdr = 1';
    my @bact = @{ $dbh->selectcol_arrayref($sql) };

    print start_blockquote;
    print h2("Overview of $appl");
    print p(font({color=>'#D05050'},'Enter search terms into the the form to ' .
    		 'retreive data. Empty fields means "anything" for that field. '.
    		 'All specified fields will be used to limit the results. ' .
    		 '')) unless $submit;

    print start_form;
    print start_table({border=>1,align=>'center',width=>'95%',
    		       cellspacing=>0,cellpadding=>'10'});
    print start_Tr, start_td;
    print start_table({width=>'95%',cellpadding=>'5'}), start_Tr;
    print td(['Bacteria' . br .
    	      popup_menu(-name=>'bact',-values=>\@bact),
    	      'Gene Name' . br .
    	      textfield(-name=>'arg',size=>'8',maxlength=>'24'),
    	      'Other Keywords' . br .
    	      textfield(-name=>'xtr',size=>'16',maxlength=>'64'),
    	      'Length' . br .
    	      textfield(-name=>'length',size=>'9',maxlength=>'9'),
    	      'Exact' . br .
    	      popup_menu(-name=>'exact',-values=>['auto','narrow','loose']),
	     ]);
    print end_Tr, end_table;
    print end_td, end_Tr, end_table;
    print table({align=>'center',width=>'50%',cellspacing=>'10'},
    		Tr(th([submit(-name=>'submit',value=>'Search'),
    		       defaults('Reset')])));
    print end_form, br;

    SrchDB() if $submit;

    print end_blockquote;
}

sub SrchDB {
    my @vars = qw(bact arg xtr length exact);
    for my $v (@vars) { $$v = param($v); }

    print hr({width=>'65%'}), br;

    #options
    my $db   = 'nucleotide';
    my $qry  = '';
    my $D    = 0;

    $len ||= '99:9999';
    $tax ||= $bact;

    $tax =~ s/^\s*|\s*$//g; die('Missing Bacteria') unless $tax;
    $tax =~ s/\s+/+/g; $tax .= '[Organism]';
    $len =~ /(\d+:\d+)/; $len = $1 || '';
    $len .= '[SLEN]' if $len;
    $xtr =~ s/^\s*|\s*$//g; $xtr =~ y/a-zA-Z .,//cd;
    $xtr =~ s/\s+/+/g;
    
    $qry  = "$tax+AND+";
    $qry .= "$len+AND+" if $len;
    $qry .= "$xtr+AND+" if $xtr;
       
    #printf "%-8s  %-16s  %9s  %s\n", 'Gene','Accession','Length','Title';
    print start_table({border=>1,align=>'center',width=>'95%',cellspacing=>0,cellpadding=>'10'});

    $arg =~ s/^\s*|\s*$//g; $arg =~ /([\w_-]+)/; 
    my $gen = $1 || '';  return(1) unless($gen);
    $gen =~ s/\s+/+/g; $gen .= '[Gene%20Name]' unless $exact eq 'loose';
    
    my $query = "$qry$gen";
	
    print Tr(th(['Gene','Accession','Length','Title']));

    #esearch
    my $url = "$UTIL/esearch.fcgi?db=$db&term=$query&usehistory=y";
    my $output = get($url);
	
    #parsing XML by hand (!!! OH NO !!!)
    my $cnt = $1 if ($output =~ /<eSearchResult><Count>(\d+)/);
    my $web = $1 if ($output =~ /<WebEnv>(\S+)<\/WebEnv>/);
    my $key = $1 if ($output =~ /<QueryKey>(\d+)<\/QueryKey>/);
    
    if ($exact eq 'auto' && !$cnt) {
	$query =~ s/\[Gene\%20Name\]//;
	$url = "$UTIL/esearch.fcgi?db=$db&term=$query&usehistory=y";
	$output = get($url);
	$cnt = $1 if ($output =~ /<eSearchResult><Count>(\d+)/);
	$web = $1 if ($output =~ /<WebEnv>(\S+)<\/WebEnv>/);
	$key = $1 if ($output =~ /<QueryKey>(\d+)<\/QueryKey>/);
    }
    if (!$cnt) {
	#print "$arg\tNo matches found\n";
	print Tr(td($arg) . td({colspan=>3}, 'No Match'));
    }
    
    #esummary
    $url = "$UTIL/esummary.fcgi?db=$db&query_key=$key&WebEnv=$web";
    my $docsums = get($url);
    
    my $n=0 if $D;
    for my $rec (split('<DocSum>', $docsums)) {
	next unless $rec =~ /<Id>(\d+)<\/Id>/;
	if ($rec =~ /<Item Name=\"Caption\"[^>]*>([^<]+)</) {
	    my $acc = $1;
	    # my $gid = $1 if ($rec =~ /<Item Name=\"Gi\"[^>]*>([^<]+)</);
	    my $str = $1 if ($rec =~ /<Item Name=\"Title\"[^>]*>([^<]+)</);
	    # my $alt = $1 if ($rec =~ /<Item Name=\"Extra\"[^>]*>([^<]+)</);
	    # my $tax = $1 if ($rec =~ /<Item Name=\"Taxid\"[^>]*>([^<]+)</);	
	    my $len = $1 if ($rec =~ /<Item Name=\"Length\"[^>]*>([^<]+)</);
	    #printf "%-8s  %-16s  %9d  %s\n", $arg, $acc, $len, $str;
	    print Tr(td([$arg, a({href=>"$NCBI/$acc",-target=>'_new'},$acc), $len, $str]));
	} else { 
	    #print "$arg\tBad record\n";
	    print Tr(td($arg) . td({colspan=>3}, 'Bad record'));
	}
    }
    print end_table;
}

sub Fret {
    my $v = $_[0];
    return unless $v;
    $v = "Ignoring unexpected value for '$v'";
    print font({size=>'+1',color=>'green'},$v);
}

