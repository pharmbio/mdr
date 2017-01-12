#!/usr/bin/perl
use v5.10; use strict; use warnings;
use LWP::Simple;
use Time::Piece;
use File::Copy;

# 
# TODO: Look for diffs rather than blindly recopy
# 
my %bugs;
my $rem = 'http://pubmlst.org/data/dbases.xml';
my $loc = 'dbases.xml';
my $mod = (stat($loc))[9];
my $t   = localtime($mod); 
my $ymd = $t->ymd;
my $fh;

die("Can't find mlst db. Run from mlst folder.") unless -e $loc;
copy($loc, "$loc.$ymd") || die("Can't backup old mlst db");
getstore($rem, $loc);

open($fh, '<', $loc) or die("Can't read mlst db");
while(<$fh>) {
    if(/alleles/) {
	my ($url, $dir, $tfa);
	s/\<.?url\>//g; s/^\s*|\s*$//g;
	$url = $_; die unless $url;
	($dir,$tfa) = m#alleles/([^/]+)/([^/]+\.tfa)$#;
	print "$dir\t$url\n";
	mkdir("alleles/$dir") unless $bugs{$dir};
	$bugs{$dir}++;
	getstore($url,"alleles/$dir/$tfa");
    }
    elsif(m#profiles/#) {
	my ($url, $pro);
	s/\<.?url\>//g; s/^\s*|\s*$//g;
	$url = $_; die unless $url;
	($pro) = m#profiles/([^/]+\.txt)$#;
	next unless $pro;
	print "$url\n";
	getstore($url,"profiles/$pro");
    }
}
    
