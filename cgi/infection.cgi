#!/usr/bin/perl -Tw
#
# Name: MDR sequence administration
# Auth: Wesley Schaal, wesley.schaal@Farmbio.com
# When: 2013-12-03

use DBI; use v5.10;
use CGI qw(:all *table *Tr *td -nosticky); autoEscape(undef);
use CGI::Carp qw(fatalsToBrowser);
require "./common.pl";

$appl = 'MDR Bacteria (VR/5011)';
$D=0;

# my $grp= "mdrusr";
# my $dbh = DBI->connect("DBI:mysql:"
# 	  . ";mysql_read_default_file=$ENV{HOME}/.my.cnf"
# 	  . ";mysql_read_default_group=$grp") ||
#     die "Can't connect to $db: $DBI::errstr";
my $dbf = '../data/bacteria.sqlite';
my $dbh = DBI->connect("dbi:SQLite:dbname=$dbf",'','');


for my $v (qw(eid submit))  { $$v = param($v); }
ShowHead();
if    ($submit)      { GetFile(); }
elsif ($eid)         { UplForm(); }
else                 { Browser(); }
ShowFoot();


sub Browser {
    my $sql = 'select * from sample order by eid';
    my $sth = $dbh->prepare($sql); $sth->execute();
    my @cols = @{ $sth->{NAME} };
    #my @colr = map {\${$cols[$_]}} (0..$#cols);
    #$sth->bind_columns(@colr) or die;

    print h2("Data for $appl");

    print br,start_table({cellpadding=>5,border=>1});
    print Tr(th([@cols]));
    while(my (@res) = $sth->fetchrow_array) {
	my $eid = shift @res;
	print Tr(td([a({href=>url . "?eid=$eid"},$eid), @res]));
    }
    print end_table;
}


sub UplForm {
# eid|sid|pid|bid|seq|sample|stamp
    $eid =~ y/0-9//cd;
    unless ($eid) { print 'Huh?'; ShowFoot(); exit(0); }
    my $sam = sprintf "S%06d", $eid;

    ($sid,$pid,$seq) = $dbh->selectrow_array("select sid,pid,seq from sample where eid = $eid");
    unless ($sid && $pid) { print 'What?'; ShowFoot(); exit(0); }
    my $pat = sprintf "P%04d-%04d", $sid, $pid;

    @insts = @{ $dbh->selectcol_arrayref('select prop from misc where type = "inst" order by pkey') };
    unshift @insts,'-';
    @chips = @{ $dbh->selectcol_arrayref('select prop from misc where type = "chip" order by pkey') };
    unshift @chips,'-';
    @chems = @{ $dbh->selectcol_arrayref('select prop from misc where type = "chem" order by pkey') };
    unshift @chems,'-';
    @rlens = @{ $dbh->selectcol_arrayref('select prop from misc where type = "rlen" order by pkey') };
    unshift @rlens,'-';

    print '<blockquote>',br;
    print h2('Sequence data for patient ' . font({color=>'darkred'},$pat)), hr;

    print ("Sample #: $sam");

    if($seq) {
	print p('Data files have already been uploaded. Uploading new files now will replace ' .
		'the current files. The contigs file is so large that you should just enter ' .
		'the path to its location, not actually upload it to the server.');
    } else {
   	print p('Upload the fasta sequences and mapping files. ' .
		'The contigs file is so large that you should just enter ' .
		'the path to its location, not actually upload it to the server.');
    }
    print start_multipart_form;
    print table({cellpadding=>'15'},
		Tr([td(b('Instrument') . br .
		       popup_menu(-name=>'inst',values=>\@insts)) .
		    td(b('Chip') . br .
		       popup_menu(-name=>'chip',values=>\@chips)) .
		    td(b('Read length') . br .
		       popup_menu(-name=>'rlen',values=>\@rlens)) .
		    td({align=>'right'},b('Chem') . br .
		       popup_menu(-name=>'chem',values=>\@chems)) ,
		    td(b('Fasta file') .   br . filefield(-name=>'fasta')) .
		    td(b('Mapping file') . br . filefield(-name=>'mapfil')) .
		    td({colspan=>2},b('Contigs Path') . br .
			textfield(-name=>'mnot',size=>'38',maxlength=>'127',-default=>$seq))
		   ]));

    print br({clear=>'all'}), hr;
    print table({align=>'center',width=>'50%',cellspacing=>'20'},
		Tr(th([submit(-name=>'submit',-label=>'Upload'),
		       defaults('Reset')])));
    print endform;
    print '</blockquote>';
}

sub GetFile {
    undef $\;
    @now = (localtime)[3..5];
    $date = sprintf "%04d-%02d-%02d", $now[2] +1900, $now[1] +1, $now[0];
    for my $v (qw(fasta fnot mapfil mnot))  { $$v = param($v); }
    $floc = tmpFileName($fasta);
    $mloc = tmpFileName($mapfil);

    print p("Date: $date"),br;
    print p("1Not: $fnot");
    print p("1Fil: $fasta");
    print p("1Loc: $floc"),br;
    print p("2Not: $mnot");
    print p("2Fil: $mapfil");
    print p("2Loc: $mloc");

}
