#!/usr/bin/env perl
# 
use strict; use warnings;

my (@genes, @muts);
my %trans = codons();
my $file = shift;
{
    local $/ = 'Query= '; open(F, '<', $file) or die; 
    @genes = <F>; close F;
}
shift @genes; #print scalar @genes;
$file =~ s#.*/##;  $file =~ s/\..*//; $file =~ s/[^\w-]//g;
    mkdir $file; print STDOUT "$file\n";

for my $gene (@genes) {
    my $name = $1 if $gene =~ /^([^\|\ ]+)/; die unless $name;
    $name =~ s/[^\w-]//g; print STDOUT "$name\n";
    open(G,'>',"$file/$name.txt") or die; select G; 
    print "$name\n"; 

    if ($gene =~ /No hits found/ms) {
	print "\nNo hits found\n";
	next;
    }
    
    $gene =~ s/Lambda.+//ms; # unnecessary
    $gene =~ s/^.+?(?:Query_)//ms;   print STDERR "\n\n\nHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH\n\n\n: $gene\n";
    @muts = ();
    
    convert($gene);
    summary();
}

sub convert {
    my $set = $_[0];
    my (@seq, @muts); my ($ns,$nr,$nb)=(0,0,0);
    
    for  (split(/\n/, $set),"\n") {
	next if /^#/;
	if (/^\s*$/ && $ns) {
	    print "\n",++$nb,"\t$seq[0]\n";
	    for my $i (1 .. $#seq) { print "\t$seq[$i]\n"; }
	    my $pep = ribo($seq[0]);
	    print ++$nr,"\t$pep\n";
	    push @muts, alts($nb, $nr, $pep, @seq);
	    $ns=0; @seq=(); $nr += 19; $nb += 59;
	} else {
	    my ($t,$q) = /^\S+\s+(\d+)\s+([\w\.-]+)\s+/ 
		or die ("Seq parse at $nb-$ns on:\n'$set'\n");
	    die("Odd offset") unless $ns || ($t % 3 == 1);
	    # wrong handling of gaps, fix later
	    my $gaps = $q =~ y/-//d;
	    $q .= 'x' x $gaps if $gaps;
	    $seq[$ns] = uc $q;
	    $ns++;
	}
    }
}

sub summary {
    my %prot;  my $Q = 'A';
    for my $query (@muts) {
	my (@silent, @differ);
	for my $mut (@{$query}) {
	    my ($silent, $res, @dna) = @{$mut};
	    my ($key) = $res =~ /(\d+)/;
	    if (exists $prot{$res}) {
		@{$prot{$res}}[1] .= ",$Q";
	    } else {
		$prot{$res} = [$key, $Q, $silent, @dna];
	    }
	    if($silent == 1) {
		push @silent, $res;
	    } else { 
		push @differ, $res;
	    }
	}
	# print "\nSilent $Q:  ", join(", ", @silent), "\n";
	# print "Mutant $Q:  ", join(", ", @differ), "\n";
	$Q++;
    }
    
    print "\n\nMutation table:\n--------------\n";
    for my $res (sort {$prot{$a}[0]<=>$prot{$b}[0]} keys %prot) {
	my ($key, $hits, $silent, @dna) = @{$prot{$res}};
	$silent = $silent ? ' - ' : 'mut';
	print "$res\t$silent\t$hits\t", join(", ",@dna),"\n";
    }
    print "\n";
}

sub alts {
    my ($drow, $prow, $pep) = (shift, shift, shift); my @set = @_;
    my @wt = split //, $set[0];  my $alt = 'A';

    for my $hit (1 .. $#set) {
	print $alt++,"\t";
	my $p = 0;
	while ($set[$hit] =~ /(...)/g) {
	    my $t = $1;
	    if ($t eq '...') { 
		print ' . ';
		$p += 3;
	    } elsif ($t =~ /-/) {
		print ' - ';
		$p += 3;
	    } else {
		my ($codon, @mut);
		for my $base (split //, $t) {
		    # $codon .= $base eq '.' ? $wt[$p] : $base;
		    if ($base eq '.') {
			$codon .= $wt[$p];
		    } else {
			$codon .= $base; 
			my $pos = $drow + $p;
			push @mut, "$wt[$p]$pos$base";
		    }
		    $p++;
		}
		my $num = int($p/3) - 1;
		my $loc = $prow + $num;
		my $nat = substr($pep, $num*3+1, 1);
		if(exists $trans{$codon}) {
		    my $res = $trans{$codon};
		    print " $res ";
		    my $silent = $nat eq $res ? 1 : 0;
		    unshift @mut, $silent, "$nat$loc$res";
		} else {
		    print " + ";
		    unshift @mut, 0, "$nat${loc}x";
		}
		push @{ $muts[$hit-1] }, [@mut];
	    }
	}
	print "\n";
    }
}


sub ribo {
    my $s = uc $_[0];
    my $e = length($s) % 3;
    $s = substr($s,0,-$e) if $e;
    $s =~ s/(...)/$trans{$1}/g;
    $s =~s/X.*//;
    $s =~ s/(.)/ $1 /g;
    # $s =~ s/(.{60})/$1\n/g;
    return $s;
}


sub codons {
    my (@base, @codon, @aa);
    @base = qw (T C A G);
    @aa   = qw (F F L L S S S S Y Y X X C C X W 
                L L L L P P P P H H Q Q R R R R
                I I I M T T T T N N K K S S R R
                V V V V A A A A D D E E G G G G);

    for my $i (@base) { for my $j (@base) { for my $k (@base) { push @codon, "$i$j$k"; } } }
    @trans{@codon} = @aa;
    %trans;
}
