#!/usr/bin/perl -Tw
#
# Name: MDR portal
# Auth: Wesley Schaal, wesley.schaal@farmbio.uu.se
# When: 2013-12-07

# TODO: Consider changing Site to Project

use DBI; use v5.10; # use strict; use warnings;
use CGI qw(:all *table *Tr *td *blockquote *div -nosticky);
use CGI::Carp qw(fatalsToBrowser);  autoEscape(undef);
use List::Util qw(first);
require "./common.pl";

$appl = 'MDR Bacteria (VR/5011)';
$D=0;
$no_site=0;
my $ncbi = 'http://www.ncbi.nlm.nih.gov/nuccore';

# my $grp= "mdrusr";
# my $dbh = DBI->connect("DBI:mysql:"
# 	  . ";mysql_read_default_file=$ENV{HOME}/.my.cnf"
# 	  . ";mysql_read_default_group=$grp") ||
#     die "Can't connect to $db: $DBI::errstr";
my $dbf = '../data/bacteria.sqlite';
my $dbh = DBI->connect("dbi:SQLite:dbname=$dbf",'','');

($min,$hour,$day,$mon,$year) = (localtime)[1..5];
$year += 1900; $mon++;
$today = sprintf("%4d-%02d-%02d", $year,$mon,$day);
$now   = sprintf("Fetched: %4d-%02d-%02d at %02d:%02d",
		 $year,$mon,$day,$hour,$min);
@restyp = @{ $dbh->selectcol_arrayref('select prop from misc where type = "outcome"') };
unshift @restyp, '-';

for my $v (qw(sid pid mode treatment submit hit list))  { $$v = param($v); }
ShowHead();
if    ($treatment)    { TreatDB(); }
elsif ($hit)          { ShowPat(); }
elsif ($list)         { ListPat(param('hits')); }
else                  { SrchAll(); }
ShowFoot();


sub SrchAll {
    my($sql,@sids,%sids,$bugs,@bugs,%bugs);

    @sids = @{ $dbh->selectcol_arrayref('select sid from sites order by sid') };
    $sql = 'select sid||": "||pi from sites order by sid';
    @sids{@sids} = @{ $dbh->selectcol_arrayref($sql) };
    unshift @sids,0; $sids{0} = ' - ';

    $sql = 'select bid from bacteria order by mdr desc,bid';
    # @bids = @{ $dbh->selectcol_arrayref($sql) };
    # $sql = 'select genus||" "||species from bacteria order by mdr desc,bid';
    # @bids{@bids} = @{ $dbh->selectcol_arrayref($sql) };
    # splice @bids,6,0,0; $bids{0} = ' - ';

    $sql = 'select bid,genus||" "||species as bug from bacteria where bid in ' .
	'(select bid from sample group by bid) order by genus,species';
    @bref = @{ $dbh->selectall_arrayref($sql) };
    @bugs = map { $bref[$_][0] } 0..$#bref; # looks clumsy
    @bugs{@bugs} = map { $bref[$_][1] } 0..$#bref;
    unshift @bugs, 0; $bugs{0} = '-';
    
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
    print td(['Site' . br .
	      popup_menu(-name=>'sid',-values=>\@sids,-labels=>\%sids),
	      'Patient ID #' . br .
	      textfield(-name=>'pid',size=>'6',maxlength=>'6'),
	      'Patient Code (ext)' . br .
	      textfield(-name=>'xid',size=>'16',maxlength=>'64'),
	      'Age (birthyear)' . br .
	      textfield(-name=>'birth',size=>'9',maxlength=>'9'),
	      'Sex' . br .
	      popup_menu(-name=>'sex',-values=>['-','F','M'])]);
    print end_Tr, end_table;
    print end_td, end_Tr, start_Tr, start_td;
    print start_table({width=>'95%',cellpadding=>'5'}), start_Tr;
    print td(['Bacteria' . br .
	      popup_menu(-name=>'bid',values=>\@bugs,labels=>\%bugs,default=>0),
	      'MDR gene' . br .
	      textfield(-name=>'gene',size=>'16',maxlength=>'32'),
	      'Sequenced' . br .
	      popup_menu(-name=>'seq',-values=>['-','Yes','No']),
	      'Outcome' . br .
	      popup_menu(-name=>'outcome',-values=>\@restyp)]);
    print end_Tr, end_table;
    print end_td, end_Tr, end_table;
    print table({align=>'center',width=>'50%',cellspacing=>'10'},
		Tr(th([submit(-name=>'submit',value=>'Search'),
		       defaults('Reset')])));
    print end_form, br;

    PrepSQL() if $submit;

    print end_blockquote;
}


sub PrepSQL {
    my @vars = qw(xid birth sex bid gene seq outcome);
    print hr({width=>'65%'});

    $where = '';
    for my $v (@vars) { $$v = param($v); }
    for my $v (@vars,'sid','pid')  {
	$$v =~ s/^\s*|\s*$//g; $$v =~ s/^-$//;
	if ($v ~~ [qw(birth sid pid bid)] && $$v) {
	    $$v =~ y/0-9<>,!-//cd;
	    next unless $$v;
	    $$v =~ s/(\d+)/$year-$1/eg if $v eq 'birth';
	    my $va = $v eq 'sid' || $v eq 'pid' ? "a.$v" : $v;
	    ### add negation ###
	    if   ($$v =~ /^\d+$/)         { $where .= "$va = $$v and "; }
	    elsif($$v =~ /^([<>])(\d+)$/) { $where .= "$va $1 $2 and "; }
	    elsif($$v =~ /^(\d+)-(\d+)$/) { $where .= "($va between $2 and $1) and "; }
	    elsif($$v =~ /\d+,[\d,]*\d+/) { $where .= "$va in ($$v) and "; } # ",,"
	    else { Fret("$v = $$v"); }
	} elsif ($v eq 'sex' && $$v) {
	    if ($$v =~ /^([FM])/i) { $where .= "$v = '$1' and "; }
	    else { Fret("Ignoring unexpected value for '$v'"); }
	} elsif ($v eq 'outcome' && $$v) {
	    if ($$v ~~ @restyp) { $where .= "$v = '$$v' and "; }
	    else { Fret($v); }
	} elsif ($v eq 'seq' && $$v) {
	    if    ($$v eq 'Yes') { $where .= "$v != '' and "; }
	    elsif ($$v eq 'No')  { $where .= "($v is NULL or $v = '') and "; }
	    else { Fret($v); }
	} elsif ($$v) {
	    # filter with $dbh->quote($$v) ?
	    $$v =~ y/A-Za-z0-9.,ÅåÄäÖöÉéÈèÜü\/-//cd;
	    if     ($$v =~ s/^=\s*//)      { $where .= "$v  = '$$v' and "; }
	    elsif  ($$v =~ s/^\!\s*=\s*//) { $where .= "$v != '$$v' and "; }
	    elsif  ($$v =~ s/^\!\s*//) { $where .= "$v not like '\%$$v\%' and "; }
	    else                       { $where .= "$v like '\%$$v\%' and "; }
	}
	print p("$v = '$$v'") if $D>1;
    }

    if($no_site) {
	$where = "where a.sid=1 and $where";
    } elsif($where) {
	$where = "where $where";
    }
    $where =~ s/and\s*$//;
    $sql = "select distinct a.sid || ':' || a.pid from patients a left join " .
	"sample b using (sid,pid) left join treat c using (eid) $where";
    @hits = @{ $dbh->selectcol_arrayref($sql) };
    print p($sql),"@hits" if $D;
    @hits ? ListPat(@hits) : print p("No matches found");
}


sub ListPat {
    my @v = @_; my(@vv, $vv);
    for my $v (@v) {
	next unless my ($a,$b) = $v =~ /^(\d+):(\d+)$/;
	push @vv,"(sid=$a and pid=$b)";
    }
    $vv = join(" or ",@vv);

    $sql = "select a.sid,a.pid,xid,sex,birth,(select ifnull((select " .
	"ifnull(genus,'')||' '||ifnull(species,'') from bacteria c where " .
	"b.bid=c.bid),'')||'|'||ifnull(cid,'')||'|'||ifnull(stamp,'') " .
	"from sample b where ($vv) and a.pid=b.pid group by b.pid having " .
	"max(eid)) goo from patients a where ($vv)";  print(p($sql)) if $D;
    $sth = $dbh->prepare($sql); $sth->execute();

    print start_blockquote, br, start_form, start_table({cellpadding=>5,border=>1});
    print Tr(th(['ID', 'Code', 'Sex', 'Age', 'Latest MDR', 'Sample', 'Last Updated']));
    while(my ($sid,$pid,$xid,$sex,$birth,$src) = $sth->fetchrow_array) {
	my ($bid,$cid,$stamp) = split(/\|/,$src);
	# my $age = $year - $birth;
	my $age = substr($stamp,0,4) - $birth;
	print Tr(td({align=>'center'},
#		    a({href=>url . "?mode=psum;sid=$sid;pid=$pid"}, "$sid:$pid")) .
		    submit(-name=>'hit',value=>"$sid:$pid")) .
		 td($xid) . td{align=>'center'},($sex) . td({align=>'center'},$age) .
		 td($bid) . td($cid) . td($stamp));
    }
    print end_table, p($now);
    print hidden('hits',@v);
    print end_form,end_blockquote;
}


sub ShowPat {
    @hits = param('hits');($sid,$pid) = split(/:/,$hit) if $hit;
    $sid =~ y/0-9//cd; $pid =~ y/0-9//cd; $eid =~ y/0-9//cd;
    unless ($sid && $pid) { SrchAll(); ShowFoot(); exit(0); }
    my $n = first {$hits[$_] eq "$hit"} 0..$#hits;
    print "HITS: $n ; $#hits ; $hit ; ", join(',',@hits)if $D;

    Nav($n,@hits);

    my $sql = "select xid,sex,birth from patients where sid=$sid and pid=$pid";
    my ($xid,$sex,$birth) = $dbh->selectrow_array($sql);

    $sql = "select eid,cid,seq,src,stamp, (select ifnull(genus,'')||' '||" .
	"ifnull(species,'') from bacteria b where a.bid=b.bid) bug from " .
	"sample a where sid=$sid and pid=$pid order by eid desc"; print p($sql) if $D;
    $sth = $dbh->prepare($sql); $sth->execute();
    @cols = @{ $sth->{NAME} }; @colr = map {\${$cols[$_]}} (0..$#cols);
    $sth->bind_columns(@colr);

    $sql = 'select date(stamp) trdate, treatment,outcome,comment from treat where eid = ?';
    $stt = $dbh->prepare($sql);

    ####################

    my $id  = sprintf "P%04d-%04d", $sid, $pid;
    #my $age = $year - $birth;
    print table({border=>0,width=>'50%',align=>'center',bgcolor=>'#F0F0F6'},
	  Tr(td(table({cellpadding=>'4',cellspacing=>'10',align=>'center',width=>'90%'},
			    Tr(td([b(u('Patient'))     . br . $id,
				   b(u('External ID')) . br . $xid,
				   b(u('Born'))  . br . $birth,
				   b(u('Sex'))         . br . $sex,
				   a({href=>"patient.cgi?mode=pedt;sid=$sid;pid=$pid"},
				     font({color=>'red'},'Edit')) . br . '&nbsp;',
				  ])))))),br,hr({width=>'65%'});
    ####################

    print start_form;
    print p(a({href=>"infadm.cgi?sid=$sid;pid=$pid"},'Report new infection'));

    while($sth->fetch) {
	my $day = substr($stamp,0,10);
	my $age = substr($day,0,4) - $birth;

	print start_form;

	print start_table({cellpadding=>4,cellspacing=>1,border=>1,width=>'90%'});
	print Tr(td($day), td("$age years old"), td($cid), td(b(font({color=>'darkred'}, $bug))));
	print start_Tr,start_td({valign=>'top',colspan=>3});

	print start_table({width=>'100%',border=>0});
	print Tr(td(b('Treatments:')));
	print Tr(td(b('Date')) . td(b('Treatment')) .
		 td(b('Outcome')) . td({width=>'50%'},b('Comment')));
	$stt->execute($eid);
	while(my ($tdate,$treatment,$outcome,$comment) = $stt->fetchrow_array) {
	    print Tr(td({valign=>'top'},[$tdate, $treatment,$outcome,$comment]));

	}
	print Tr(td(br . submit(-name=>'treatment',value=>"Add/Edit treatment")));
	print end_table, end_td;

	# DISC DIFF, MIC
	# $sql = 'select drug||"|"||mgl from mic join antibio using (aid) where ' .
	     "eid = $eid order by drug"; # print p($sql);
	# my $mic = $dbh->selectcol_arrayref($sql);
	# # print scrolling_list(-name=>'mic_profile', values=>$mic, size=>12);

	print start_td({valign=>'top',colspan=>1});
	$sql = 'select drug||"|"||diff from disc join antibio using (aid) where ' .
	    "eid = $eid order by drug"; # print p($sql);
	my $disc = $dbh->selectcol_arrayref($sql);

	print start_div({-style=>'height:160px;border:1px solid;overflow:auto;'});
	print start_table({width=>'100%',cellpadding=>0,cellspacing=>0,border=>1});
	print Tr(td([b('Antibiotic'),b('Disc Diff'),b('MIC')]));
	for my $row (@{$disc}) { print Tr(td([split /\|/,$row])); }
	print end_table, end_div, end_td, end_Tr;

	print start_Tr, start_td({valign=>'top',colspan=>4});
	print start_table({width=>'100%',border=>0});
	print Tr(td({colspan=>2}, b('Sequence: &nbsp;') . 
		    a({href=>"infection.cgi?eid=$eid"}, $seq ? 'UPLOADED' : 'PENDING')));

	# ARDB
	print start_Tr, start_td({valign=>'top'});
	my $sta = $dbh->prepare("select gene,pident,acc from resist where eid = $eid");
	$sta->execute;

	print b('Resistant Genes'), br, br;
	print start_div({-style=>'height:180px;width:360px;overflow:auto;'});
	print start_table({width=>'100%',cellpadding=>0,cellspacing=>0,border=>1});
	print Tr(td(['Gene', 'identity','accession']));
	while(my @row = $sta->fetchrow_array) { 
	    print Tr(td([$row[0], $row[1], a({href=>"$ncbi/$row[2]",-target=>'_new'},$row[2])]));
	}
	print end_table, end_div, end_td;
	

	print end_td; 


	# TODO: Combine MIC and DD -- kludge it for now

	# MLST
	print start_td({valign=>'top'});
	$sql = "select typ,ident from mlst where eid = $eid and loc = 'ST'"; #print p($sql);
	my @mlst = $dbh->selectrow_array($sql);
	my $stm = $dbh->prepare("select loc,typ,ident from mlst where eid = $eid and loc != 'ST'");
	$stm->execute;

	#print start_div({-style=>'height:160px;width:360px;border:1px solid;overflow:auto;'});
	print b('MLST'),br, b("ST = $mlst[0] ($mlst[1])"), br,br;
	print start_div({-style=>'height:180px;width:360px;overflow:auto;'});
	print start_table({width=>'100%',cellpadding=>0,cellspacing=>0,border=>1});
	#print Tr(td([b('MLST'),b("ST: $mlst[0]"),b($mlst[1])]));
	print Tr(td[qw(Locus type identity)]);
	while(my @row = $stm->fetchrow_array) { print Tr(td([@row])); }
	print end_table, end_div, end_td;


	# # DISC DIFF, MIC
	# # $sql = 'select drug||"|"||mgl from mic join antibio using (aid) where ' .
	#      "eid = $eid order by drug"; # print p($sql);
	# # my $mic = $dbh->selectcol_arrayref($sql);
	# # # print scrolling_list(-name=>'mic_profile', values=>$mic, size=>12);

	# print start_td({valign=>'top'});
	# $sql = 'select drug||"|"||diff from disc join antibio using (aid) where ' .
	#     "eid = $eid order by drug"; # print p($sql);
	# my $disc = $dbh->selectcol_arrayref($sql);

	# print start_div({-style=>'height:160px;width:360px;border:1px solid;overflow:auto;'});
	# print start_table({width=>'100%',cellpadding=>0,cellspacing=>0,border=>1});
	# print Tr(td([b('Antibiotic'),b('Disc Diff'),b('MIC')]));
	# for my $row (@{$disc}) { print Tr(td([split /\|/,$row])); }
	# print end_table, end_div, end_td;

 	print end_Tr, end_table, end_td, end_Tr, end_table, br;
	print hidden(-name=>'eid',value=>$eid);
	print end_form;
    }
}


sub Nav {
    my $n = shift; my @v = @_;
    my $prev = $n        ? $v[$n-1] : '';
    my $next = $n == $#v ? '' : $v[$n+1];

    print start_form, hr({width=>'65%'});
    print start_table({align=>'center'}),start_Tr;
    print start_td({bgcolor=>'#f0e0ff'});
    print $prev ? submit(-name=>'hit',value=>$prev) :
        font({color=>'#606060'},' First ');
    print ' &nbsp; &nbsp; ';
    print b(" Patient $v[$n] ");
    print ' &nbsp; &nbsp; ';
    print $next ? submit(-name=>'hit',value=>$next) :
        font({color=>'#606060'},' Last ');
    print end_td,td(' &nbsp; &nbsp; ');
    print td(' &nbsp; &nbsp; ');
    print td({bgcolor=>'#e0f0ff'},'&nbsp;' .
	     a({href=>url},'New Search'));
    # submit(-name=>'list',value=>'Search results')); # restore srch params
    print end_Tr,end_table,hr({width=>'65%'});
    print hidden('hits',@v);
    print end_form;
}


sub TreatDB {
    my $eid = param('eid'); $eid =~ y/0-9//cd;

    my $sql = "select sid,pid,seq,src,stamp,(select ifnull(genus,'')" .
	"||' '|| ifnull(species,'') from bacteria b where a.bid=b.bid) " .
	"bug from sample a where eid=$eid";
    my ($sid,$pid,$seq,$src,$stamp,$bug) = $dbh->selectrow_array($sql);
    unless ($sid && $pid && $eid) { SrchAll(); ShowFoot(); exit(0); }

    $sql = "select xid,sex,birth from patients where sid=$sid and pid=$pid";
    my ($xid,$sex,$birth) = $dbh->selectrow_array($sql);

    $sql = "select tid,treatment,outcome,date(stamp) trdate from treat where eid= ?";
    $stt = $dbh->prepare($sql);

    ####################
    my $id  = sprintf "P%04d-%04d", $sid, $pid;
    my $age = $year - $birth;
    print table({border=>0,width=>'50%',align=>'center',bgcolor=>'#F0F0F6'},
	  Tr(td(table({cellpadding=>'4',cellspacing=>'10',align=>'center',width=>'90%'},
			    Tr(td([b(u('Patient'))     . br . $id,
				   b(u('External ID')) . br . $xid,
				   b(u('Age'))         . br . $age,
				   b(u('Sex'))         . br . $sex,
				   a({href=>"patient.cgi?mode=pedt;sid=$sid;pid=$pid"},
				     font({color=>'red'},'Edit')) . br . '&nbsp;',
				  ])))))),br,hr({width=>'65%'});
    ####################

    my $day = substr($stamp,0,10);
    print start_form;

    print start_table({cellpadding=>4,cellspacing=>1,border=>1,width=>'90%'});
    print Tr(td($day), td({align=>'right'},b(font({color=>'darkred'}, $bug))));
    print start_Tr,start_td({colspan=>2});

    print start_table({width=>'80%',align=>'center',border=>0});
    print Tr(td([b('Treatment'),b('Outcome'),b('Date')]));
    $stt->execute($eid); my $row=0;
    while(my ($tid,$treatment,$outcome,$tdate) = $stt->fetchrow_array) {
	print Tr(td([textfield(-name=>"treatment.$tid",size=>'42',default=>$treatment),
		     popup_menu(-name=>"outcome.$tid",-values=>\@restyp,default=>$outcome),
		     textfield(-name=>"tdate.$tid",size=>'14',default=>$tdate)]));
    }
    print Tr(td([textfield(-name=>'treatment.0',size=>'42',default=>''),
		 popup_menu(-name=>'outcome.0',-values=>\@restyp,default=>'-'),
		 textfield(-name=>'tdate.0',size=>'14',default=>$today)]));

    print Tr(td(br . submit(-name=>'tsav',value=>"save changes")));
    print end_table, end_td, end_Tr, end_table, br;
    print hidden(-name=>'eid',value=>$eid);
    print end_form;

}


sub Fret {
    my $v = $_[0];
    return unless $v;
    $v = "Ignoring unexpected value for '$v'";
    print font({size=>'+1',color=>'green'},$v);
}

#print br, a({href=>"patient.cgi"}, "Add new patient");

#($user = $ENV{REMOTE_USER}) =~ y/a-zA-Z0-9_-//cd; #a-zA-Z0-9åäöéèëáàüßïõñÅÄÖÉÈËÁÀÜÏÕÑ_-;
#Fail("User '$user' not found. Serious configuration error.") unless $user eq 'wes';

#@cols = split(/,/,$cols);  ${$cols[$_]} = $res[$_] for (0 .. $#cols);

    # print start_table({cellpadding=>4,cellspacing=>1,border=>0});
    # print start_Tr;
    # print td(table({cellpadding=>'4',cellspacing=>'1',border=>'1'},
    # 		   Tr([td(b('Patient'))      .  td($id),
    # 		       td(b('External ID'))  .  td($xid),
    # 		       td(b('Age/Sex'))      .  td("$age / $sex"),
    # 		      ])));
    # print end_Tr,end_table;

#'Date of activity' . br .
#    textfield(-name=>'dates',size=>'16',maxlength=>'32')]);

#insert into mic select 1,aid, (select prop from misc where oid = mic * abs(random() % 17)+15) mgl,'' from antibio where par > 0 and mic = 1;
