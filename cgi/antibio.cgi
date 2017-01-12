#!/usr/bin/perl -Tw
#
# Name: MDR portal - pick antibiotics for MIC profiles (etc)
# Auth: Wesley Schaal, wesley.schaal@farmbio.uu.se
# When: 2014-03-08

use DBI; use v5.10;
use CGI qw(:all *table *Tr *td *blockquote -nosticky);
use CGI::Carp qw(fatalsToBrowser);  autoEscape(undef);
require "./common.pl";
$appl = 'MDR Bacteria (VR/5011)';

my $dbf = '../data/bacteria.sqlite';
my $dbh = DBI->connect("dbi:SQLite:dbname=$dbf",'','');

my $mode = param('mode');

ShowHead();
if   ($mode eq 'mic')   { SavMICs(); }
elsif($mode eq 'new')   { NewDrug(); }
elsif($mode eq 'add')   { SavDrug(); }
else                    { Antibio(); }
ShowFoot();

sub Antibio {
    my $sql = 'select aid,drug from antibio where par = 0 order by aid';
    my $sth = $dbh->prepare($sql); $sth->execute();
    my $sql = 'select aid,mic,drug from antibio where par = ? order by drug';
    my $sti = $dbh->prepare($sql);

    print start_blockquote, h2("List of Antibiotics for MIC Profiles");
    print p('This is an incomplete though reasonably long list of antibiotics ' .
	    '(etc) roughly grouped by class. The main purpose of this list is ' .
	    'for the selection of diagnostic drugs of the MIC profiles. ' .
	    'Check/uncheck the boxes next to each as appropriate and click the ' .
	    'Update button. You may also ' . a({href=>url . '?mode=new'}, 'ADD') .
	    ' a new drug, but please make certain to check for alternates names ' .
	    'of drugs already on this list.');

    print start_form;
    print table({cellpadding=>7},
		Tr(td([submit(-name=>'mic',value=>'Update'),defaults('Cancel')])));

    print start_table({cellpadding=>5,border=>1});
    print Tr(th(['Class','MIC','Drug']));
    while(my($par,$cat) = $sth->fetchrow_array) {
	$sti->execute($par); my $first=1;
	while(my($aid,$mic,$drug) = $sti->fetchrow_array) {
	    print $first ? td($cat) : td('&nbsp;');
	    print td({align=>'center'},
		     #checkbox(-name=>"cb$aid", -checked=>$mic,
		     checkbox(-name=>$aid, -checked=>$mic,
		     -value=>1, -label=>''));
	    print td($drug);
	    print end_Tr;
	    $first=0;
	}
    }
    print end_table;
    print hidden(-name=>'mode',default=>'mic',force=>1);
    print end_form, end_blockquote;
}


sub SavMICs {
    # maybe use a transaction for this step
    my $new = join(',',grep {/^\d+$/} param);
    $dbh->do("update antibio set mic = 1 where mic = 0 and aid in ($new)") or die($dbh->errstr());
    $dbh->do("update antibio set mic = 0 where mic = 1 and aid not in ($new)") or die($dbh->errstr());

    $CGI::Q->delete_all();
    print blockquote(h3("MIC list updated"));
    Antibio();
}


sub NewDrug {
    print start_blockquote, h2("Add a new antibiotic to the list");
    print p('Instructions ...');

    my $sql = 'select aid from antibio where par = 0 order by aid';
    my $cat = $dbh->selectcol_arrayref($sql);
    $sql = 'select drug from antibio where par = 0 order by aid';
    my %lab; @lab{@$cat} = @{ $dbh->selectcol_arrayref($sql) };
    unshift @$cat, '0'; $lab{'0'} = 'choose a category';

    print start_form;
    print table({cellpadding=>7},
		Tr(td([submit(-name=>'mic',value=>'Save'),defaults('Cancel')])));

    print table({cellpadding=>5,border=>0},
		Tr(td([popup_menu(-name=>par, -values=>$cat, -labels=>\%lab),
		      textfield(-name=>drug, size=>40, maxlength=>127)])));
    print end_table;
    print hidden(-name=>'mode',default=>'add',force=>1);
    print end_form, end_blockquote;

}


sub SavDrug {
    # set MIC flag too?
    my($par, $drug) = (param('par'), param('drug'));

    die("Bad Category ID '$par'") unless $par =~ /^\d+$/;
    $drug =~ y#a-zA-Z0-9/ -##cd;

    $dbh->do("insert into antibio (par,drug) values ($par,'$drug')");

    $CGI::Q->delete_all();
    print blockquote(h3("Antibiotic added"));
    Antibio();
}
