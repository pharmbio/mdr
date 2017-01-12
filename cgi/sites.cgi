#!/usr/bin/perl -Tw
#
# Name: MDR portal - admin sites
# Auth: Wesley Schaal, wesley.schaal@farmbio.uu.se
# When: 2013-11-30

use DBI; use v5.10;
use CGI qw(:all *table *Tr *td *blockquote -nosticky);
use CGI::Carp qw(fatalsToBrowser);  autoEscape(undef);
require "./common.pl";
$appl = 'MDR Bacteria (VR/5011)';

# my $grp= "mdradd";
# my $dbh = DBI->connect("DBI:mysql:"
# 	  . ";mysql_read_default_file=$ENV{HOME}/.my.cnf"
# 	  . ";mysql_read_default_group=$grp") ||
#     die "Can't connect to $db: $DBI::errstr";
my $dbf = '../data/bacteria.sqlite';
my $dbh = DBI->connect("dbi:SQLite:dbname=$dbf",'','');

$D=0;

for $v (qw(sid mode))  { $$v = param($v); }

ShowHead();
print "mode= $mode" if $D;
if   ($mode eq 'usav')   { AddUser(); }
elsif($mode eq 'snew')   { NewSite(); }
elsif($mode eq 'ssav')   { SavSite(); }
elsif($mode eq 'sedt')   { EdtSite(); }
else                     { SiteLst(); }
ShowFoot();


sub SiteLst {
    print start_blockquote;
    print h2("Site Administration for $appl");

    my $sth = $dbh->prepare("select * from sites order by sid");
    $sth->execute(); my @cols = @{ $sth->{NAME} }; my @colr = map {\${$cols[$_]}} (0..$#cols);
    $sth->bind_columns(@colr) or die;

    print br, a({href=>url . "?mode=snew"}, "Add new site");
    print start_table({cellpadding=>5,border=>1});
    print Tr(th(['Site-ID', 'Site name', 'PI', 'Staff']));
    while($sth->fetch) {
	@users = @{$dbh->selectcol_arrayref("select name from users where sid = $sid")};
	$users = (join '; ', @users);
	print Tr(td({align=>'center'}, a({href=>url . "?mode=sedt;sid=$sid"}, $sid)) .
		 td("$site [$cc]") . td($pi) . td($users));
    }
    print end_table;
    print end_blockquote;
}

sub EdtSite {
    $sid =~ y/0-9//cd;
    unless ($sid) { SiteLst(); ShowFoot(); exit(0); }

    ($cc,$pi,$site) = $dbh->selectrow_array("select cc,pi,site from sites where sid = $sid");
    @users = @{$dbh->selectcol_arrayref("select name from users where sid = $sid")};
    $users = (join '; ', @users);

    print start_blockquote;
    print h2("Edit site $sid");
    print start_form;

    print table({cellpadding=>7},
		Tr(td([submit(-name=>'schg',value=>'Update'),defaults('Cancel')])));
    print table({cellpadding=>3},
		Tr([td(['Country',textfield(-name=>'cc',size=>'3',maxlength=>'3',-default=>$cc)]),
		    td(['Site name',textfield(-name=>'site',size=>'80',maxlength=>'250',-default=>$site)]),
		    td(['PI',textfield(-name=>'pi',size=>'40',maxlength=>'50',-default=>$pi)]),
		    td(['Members',$users])]));

    print hidden(-name=>'sid',default=>$sid,force=>1);
    print hidden(-name=>'mode',default=>'ssav',force=>1);
    print endform;
    print end_blockquote;
}


sub SavSite {
# needs more error checking
    $sid =~ y/0-9//cd;
    unless ($sid) { SiteLst(); ShowFoot(); exit(0); }

    for $v (qw(cc pi site))  { $$v = param($v); }

    print "UPDATE sites SET cc = '$cc', pi = '$pi', site = '$site'  WHERE sid = $sid" if $D;
    $qs = '?,' x 3; chop($qs);
    if($sid) {
	$dbh->do("UPDATE sites SET cc = '$cc', pi = '$pi', site = '$site'  WHERE sid = $sid") or
	    Fail("Cannot update site '$sid' because " . br . $dbh->errstr);
    } else { print font({size=>'+2',color=>'red'},
			"Site '$sid' missing or unrecognized."); }
    print font({size=>'+2',color=>'green'}, "Site $sid updated.");
    $CGI::Q->delete_all();
    SiteLst();
}

sub NewSite {
    #$dbh->begin_work;
    $dbh->do('INSERT into sites (sid) values (NULL)');
    $sid = $dbh->last_insert_id(undef,undef,undef,undef);
    #$dbh->commit;

    print start_form;
    print hidden(-name=>'sid',default=>$sid,force=>1);
    print endform;
    print font({size=>'+2',color=>'green'}, "Fill in details for new site");
    EdtSite();
}
