#!/usr/bin/perl
# Auth: Wesley Schaal, wesley.schaal@farmbio.uu.se
#
use strict; use warnings;
use Getopt::Long qw(:config bundling);
use LWP::Simple;

#options
my $base = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/';
my ($db, $len, $tax) = ('nucleotide', '99:9999', 'Staphylococcus aureus');

my ($exact, $qry, $xtr, $verbose, $D, $help) = (2,'','','','','');
GetOptions ('l|length=s'   => \$len,
	    's|species=s'  => \$tax,
	    'm|misc=s'     => \$xtr,
	    'x|e|exact:i'  => \$exact,
	    'v|verbose'    => \$verbose,
	    'z|D|debug'    => \$D,
 	    'h|help|?'     => \&help) or help();

print("Need a gene to search for\n"),help() unless @ARGV;
$tax =~ s/^\s*|\s*$//g; print("Species?\n"),help() unless $tax;
$tax =~ s/\s+/+/g; $tax .= '[Organism]';
$len =~ /(\d+:\d+)/; $len = $1 || '';
$len .= '[SLEN]' if $len;
$xtr =~ s/^\s*|\s*$//g; $xtr =~ y/a-zA-Z .,//cd;
$xtr =~ s/\s+/+/g;

$qry  = "$tax+AND+";
$qry .= "$len+AND+" if $len;
$qry .= "$xtr+AND+" if $xtr;


printf "%-8s  %-16s  %9s  %s\n", 'Gene','Accession','Length','Title';
for my $arg (@ARGV) {
    $arg =~ s/^\s*|\s*$//g; $arg =~ /([\w_-]+)/; 
    my $gen = $1 || ''; 
    unless($gen) { print("Skipping unreadable gene '$arg'\n"); next; }
    $gen =~ s/\s+/+/g; $gen .= '[Gene%20Name]' if $exact;

    my $query = "$qry$gen";
    print "Q: $query\n" if $D||$verbose;

    #esearch
    my $url = $base . "esearch.fcgi?db=$db&term=$query&usehistory=y";
    my $output = get($url);
    print "__QRY__\n$output\n__EOL__\n\n" if $D;

    #parsing XML by hand (!!! OH NO !!!)
    my $cnt = $1 if ($output =~ /<eSearchResult><Count>(\d+)/);
    my $web = $1 if ($output =~ /<WebEnv>(\S+)<\/WebEnv>/);
    my $key = $1 if ($output =~ /<QueryKey>(\d+)<\/QueryKey>/);

    # unless($cnt) { print "$arg\tNo matches found\n"; next; }
    if ($exact==2 && !$cnt) {
	$query =~ s/\[Gene\%20Name\]//;
	print "Norrow search failed. Using loose criteria:\n$query\n" if $D||$verbose;
	$url = $base . "esearch.fcgi?db=$db&term=$query&usehistory=y";
	$output = get($url);
	print "__QRY__\n$output\n__EOL__\n\n" if $D;
	$cnt = $1 if ($output =~ /<eSearchResult><Count>(\d+)/);
	$web = $1 if ($output =~ /<WebEnv>(\S+)<\/WebEnv>/);
	$key = $1 if ($output =~ /<QueryKey>(\d+)<\/QueryKey>/);
    }
    if (!$cnt) {
	print "$arg\tNo matches found\n"; next;
    }

    #esummary
    $url = $base . "esummary.fcgi?db=$db&query_key=$key&WebEnv=$web";
    my $docsums = get($url);
    print "__SUM__\n$docsums\n__EOL__\n\n" if $D;
    # printf "%-8s  %-16s  %9s  %s\n", 'Gene','Accession','Length','Title' if $docsums;

    my $n=0 if $D;
    for my $rec (split('<DocSum>', $docsums)) {
	print "Record: ", ++$n, "\n" if $D;
	next unless $rec =~ /<Id>(\d+)<\/Id>/;
	# print("$arg\tBad record\n") unless $rec =~ /<Id>(\d+)<\/Id>/;
	if ($rec =~ /<Item Name=\"Caption\"[^>]*>([^<]+)</) {
	    my $acc = $1;
	    # my $gid = $1 if ($rec =~ /<Item Name=\"Gi\"[^>]*>([^<]+)</);
	    my $str = $1 if ($rec =~ /<Item Name=\"Title\"[^>]*>([^<]+)</);
	    # my $alt = $1 if ($rec =~ /<Item Name=\"Extra\"[^>]*>([^<]+)</);
	    # my $tax = $1 if ($rec =~ /<Item Name=\"Taxid\"[^>]*>([^<]+)</);	
	    my $len = $1 if ($rec =~ /<Item Name=\"Length\"[^>]*>([^<]+)</);
	    # print "$arg\t$acc\t$len\t$str\n";
	    # print "$arg\t$len\t$acc\t$str\n";
	    printf "%-8s  %-16s  %9d  %s\n", $arg, $acc, $len, $str;
	} else { 
	    print "$arg\tBad record\n";
	    print STDERR "Error: '$query'\n\n$rec\n";
	    # next(0);
	}
    }
}

sub help {
    print <<EOF;

Usage: $0 [opts] gene
where "gene" is what we are looking for *e.g., "est"). This is necessary. 
Additionally, "opts" may be one or more of the following:
  --misc="other keywords"        Use if needed to narrow the search.
  --species="Scientific name"    Defaults to "Staphylococcus aureus".
  --length=min:max               Number of bases. Set to 0 to skip. Defaults to "99:9999".
  --exact=0:1                    Narrow (1) or Loose (0) search. If not spcified, 
                                     try Narrow but drop to Loose if no hits found.
  --verbose                      Show query sent to server
  --help                         Show this help and exit

Values can be written as "--misc=foo" or "--misc foo" or abbreviated to "-mfoo".
Multi-word options must be protected in quotes (eg, --species "Escherichia coli").

EOF
    exit(0);
}

