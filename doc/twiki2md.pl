#!/usr/bin/perl

#  This script is for converting TWiki formatted documents to Markdown
#  format.  See the POD documentation at the end of this file for more
#  information.

#  Copyright (C) 2010, Frank Dean

#  twiki2mdml.pl is free software: you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.

#  twiki2mdml is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with twiki2mdml.pl.  If not, see
#  <http://www.gnu.org/licenses/>.

use strict;
use warnings;
use Getopt::Long;
use Pod::Usage;

# Verbose output
my $verbose = '';
# Man page option
my $man;
# Help option
my $help;
# Filename extension to use for converting internal links
my $internal_link_ext = '.html';
# If true, links to the Main web are converted from
# "Main.SomeOne" to "Some One" - see POD documentation.
my $hide_main_web_links = '';
# Whether to convert tables to HTML or Pandoc syntax
my $pandoc_table = 1;
# Whether we're in a TWiki <literal> section
my $literal = 0;
# The contents of the previous line
my $preceeding = '';


GetOptions('verbose!' => \$verbose,
		   'hide-main-web-links!' => \$hide_main_web_links,
		   'pandoc-tables!' => \$pandoc_table,
		   'man' => \$man,
		   'help' => \$help,
	) or pod2usage(2);
pod2usage(1) if $help;
pod2usage(-exitval => 0, -verbose => 2) if $man;

sub process_html_row() {
	if (/^\s*\|\s\*.*\*\s\|\s*$/) {
		# Header
		while (s/\|\s*\*([^|\*]*)\*\s*\|/<th>$1<\/th>|/) {};
		s/\|//;
		s/[\r\n]+$//;
		print "  <tr>$_</tr>\n";
	} else {
		# Normal row
		while (s/\|\s*([^|]*)\s*\|/<td>$1<\/td>|/) {};
		s/\|//;
		s/[\r\n]+$//;
		print "  <tr>$_</tr>\n";
	}
}

# Reads in the entire table into a 2 dimensional array.
# Then calculates the column widths and writes the table,
# padding as necessary.
sub process_pandoc_table() {
	my @table;
	while (!eof() && $_ && /^\s*\|.*\|\s*$/) {
		my @row = /\|([^\|]*)/g;
		my @columns;
		print STDERR "--- Start row ---\n" if $verbose;
		for (@row) {
			unless (/^[\s]*$/) {
				process_inline_fixes();
				process_inline_links();
				s/\s+([\S].*[\S])\s+/$1/;
				push @columns, $_;
			}
		}
		push @table, [ @columns ];
		print STDERR "--- End row ---\n" if $verbose;
		$_ = <>;
	}
	# We read a line too many, so hold onto it for later
	my $keep_line = $_;
	# @table now contains a 2 dimensional array containing the
	# entire table contents.

	# Find the width of each column
	my ($row, $col);
	my @colinfo;
	for $row ( 0 .. $#table) {
		for $col ( 0 .. $#{$table[$row]} ) {
			my $max = $colinfo[$col];
			my $cell = $table[$row][$col];
			my $len = length $cell;
			if (!defined $max || $len > $max) {
				$colinfo[$col] = $len;
			}
		}
	}
	my $width;
	my $line;
	for $row ( 0 .. $#table) {
		$line = '';
		for $col ( 0 .. $#{$table[$row]} ) {
			my $max = $colinfo[$col];
			my $cell = $table[$row][$col];
			$width = $colinfo[$col];
			if ( $col == $#{$table[$row]} ) {
				$line .= $cell;
			} else {
				$line .= sprintf("%-*s", $width + 1, $cell);
			}
		}
		$_ = $line;
		# Strip EOL characters
		s/^(.*[^\r\n])[\r\n]*/$1/;
		print "$_\n";
		$line = '';
		if ($row == 0) {
			for $col ( 0 .. $#{$table[$row]} ) {
				$width = $colinfo[$col];
				$line .= sprintf("%-.*s ", $width, "----------------------------------------------------------------------------------------------------------------------------------------------------------------");
			}
			print "$line\n";
		}
	}
	# Now let the extra line fall through for normal processing
	$_ = $keep_line;
	process_line() if (!eof());
}

sub process_html_table() {
	print "<table cellspacing=\"5\" id=\"table1\" cellpadding=\"3\" class=\"twikiTable\" border=\"0\">\n";
	while (!eof() && $_ && /^\s*\|.*\|\s*$/) {
		process_html_row();
		$_ = <>;
	}
	print "</table>\n";
	# We read a line after the table,
	# $_ still holds that value
	process_line() if (!eof());
}

sub process_table() {
	print STDERR "--- Start table ---\n" if $verbose;
	if ($pandoc_table) {
		print "<div class=\"twikiTable\">\n";
		process_pandoc_table();
		print "</div>\n";
	} else {
		process_html_table();
	}
	print STDERR "--- End table ---\n" if $verbose;
}

# Slurps in the whole <pre> section, counting nested tags to ensure we
# get a complete section.  I imagine this will fail if a <pre> tag
# follows a </pre> tag on the last line.  The opening and closing
# <pre> tags are removed.  Where that results in a blank line, the
# whole line is dropped too.
sub process_pre_section() {
	my @lines;
	my $open = 0;
	my $close = 0;
	process_inline_fixes();
	# Remove <nop>
	s/<nop>//g;
	push(@lines, $_);
	# How many opening and closing tags in the line?
	$open += s/<pre>//g;
	$close += s/<\/pre>//g;
	until ($open == $close || eof()) {
		$_ = <>;
		process_inline_fixes();
		# Remove <nop>
		s/<nop>//g;
		push(@lines, $_);
		# How many opening and closing tags in the line?
		$open += s/<pre>//g;
		$close += s/<\/pre>//g;
	}
	
	my $index;
	my @result;
	foreach $index (0 .. $#lines) {
		# If the line has <pre> or </pre> tags, remove them
		if ($lines[$index] =~ /<\/?pre>/) {
			$lines[$index] =~ s/<\/?pre>//g;
			# if the result is an empty line, remove it
			unless ($lines[$index] =~ /^\s*$/) {
				push(@result, $lines[$index]);
			}
		} else {
			push(@result, $lines[$index]);
		}
	}

	# Need a blank line before a <pre> section
	# If the line preceeding the section wasn't blank, add one
	print "\n" if (!($preceeding =~ /^\s*$/));
	for (@result) {
		# HTML Entities inside <pre>
		if (/&\w+;/) {
			s/&nbsp;/ /g;
			s/&lt;/</g;
			s/&gt;/>/g;
			if (/&\w+;/) {
				my $hold = $_;
				s/(&\w+;)/$1/;
				print STDERR "*** WARNING *** Unknown HTML entity: $1\n";
				$_ = $hold;
			}
		}
		print "\t$_";
	}
	print STDERR "*** WARNING *** opening and closing <pre> tags mismatch\n" if eof();
}

sub process_inline_fixes() {
	# Escape any backslash characters
	s/\\/\\\\/g;
	s/%MAINWEB%\./Main./g;
	s/%BR%/<br\/>/g;
	# tw *bold* to **bold**
	s/(^|\s)(\*[^\s\*][^\*]*[^\s\*]\*)/$1*$2*/g;
	# tw _emphasied_ same rule for Markdown
	# tw __bold italic__ *__bold italic__*
	s/(^|\s)(__[^\s_][^_]*[^\s_]__)/$1*$2*/g;
	# tw =Fixed font= <code>Fixed Font</code>
	s/(^|\s)=([^\s=][^=]*[^\s=])=/$1<code>$2<\/code>/g;
	# tw ==bold fixed== <strong><code>Bold Fixed Font</code></strong>
	s/(^|\s)==([^\s=][^=]*[^\s=])==/$1**<code>$2<\/code>**/g;
	s/[\r\n]//g;
	s/^(.*)$/$1\n/g;
}

sub process_inline_links() {
	# Specifially replace "Main.SomeOne" with "Some One" so author names
	# are not linked to Main web.
	if ($hide_main_web_links) {
		while (s/(^|\s)(Main\.)(([A-Z]+[a-z]+)([A-Z]+\w*)+)(\s)/${1}${4} ${5}${6}/) {};
	}
	# Partially convert internal inter-web links
	# Main.TWikiUsers becomes ../Main/TWikiUsers
	# Final conversion happens later
	while (s/(^|\s)([A-Z]+[a-z]+)\.([A-Z]+[\w]*)([\W])/${1}..\/${2}\/${3}${4}/) {};
	# Forced Links
	# e.g. [[forced link]] becomes [forced link](ForcedLink.html)
	while (/\[\[([^\[\]]*)\]\]/) {
		my $phrase = $1;
		my $camel_case = $phrase;
		$camel_case =~ s/(\w+)/ucfirst $1/eg;
		$camel_case =~ s/\s//g;
		if ($camel_case =~ /#/) {
			$camel_case =~ /([^#]*)#([^#]+)/;
			my $anchor = $2;
			$camel_case = $1;
			s/\[\[[^\[\]]*\]\]/[${phrase}](${camel_case}${internal_link_ext}#${anchor})/;
		} else {
			s/\[\[[^\[\]]*\]\]/[${phrase}](${camel_case}${internal_link_ext})/;
		}
	}
	# Anchors
	s/^#([A-Z]+[a-z]+[A-Z]+[\w]*)([\W])/<a name="$1"><\/a>/;
	# [[target url][display]] to [display](target url)
	while (/^(.*)\[\[([^\[\]]*)\]\[([^\[\]]*)\]\](.*)/) {
		$_ = $1 . "[$3]($2)" . $4 . "\n";
	}
	while (/^(.*[\s])(http:\/\/[^\s<>]*)([\W<].*)$/) {
		$_ = $1 . "<$2>" . $3 . "\n";
		# Sometimes end up with 2 EOL characters, so strip extra one
		s/^(.*[\r\n])[\r\n]*/$1/;
	}
	# Turn CamelCase WikiLinks into Markdown html links
	while (s/(^|\s)((\.\.\/)?([A-Z]+[a-z]+[A-Z\/]+[\w\/]*))([\W])/${1}[${4}](${2}${internal_link_ext})${5}/) {
	};
	s/[\r\n]//g;
	s/^(.*)$/$1\n/g;
	# Remove <nop>
	s/<nop>//g;
	# Assume surviving lines starting with # are shell examples and indent
	s/^(#)/\t$1/;
}

sub process_line() {
	# Are we inside a <literal> section?
	if (/^\s*<\/literal>/) {
		$literal = 0;
	}
	if (/^\s*<literal>/) {
		$literal = 1;
	}
	if ($literal) {
		print;
	} else {
		if (/<pre>/) {
			process_pre_section();
		} elsif (/^\s*\|.*\|\s*$/) {
			process_table();
		} else {
			process_inline_fixes();
			process_inline_links();
			# From here on, only rules about how a line starts
			if (s/^---\+ // || s/^---\+!! //) {
				# Heading level 1
				print "\n" if (!$preceeding =~ /^$/);
				print $_;
				print '=' x length;
				print "\n";
			} elsif (s/^---\+\+ //) {
				# Heading level 2
				print "\n" if (!$preceeding =~ /^$/);
				print $_;
				print '-' x length;
				print "\n";
			} elsif (/^(---)(\++)( .*)$/) {
				# Other heading levels
				my $heading = $2;
				my $content = $3;
				$heading =~ s/\+/#/g;
				print "\n" if (!$preceeding =~ /^$/);
				print $heading . $content . "\n";
			} elsif (/^(%META.*)$/ || /^(%TOC.*)$/ ||
					 /^(%STARTINCLUDE.*)$/ ||
					 /^(%STOPINCLUDE.*)$/) {
				# ignore
				print "<!-- $1 -->\n";
			} else {
				# list
				if (/^(\t| {3})+(\*|1|A|i)/) {
					# Remove first indent
					s/^(\t| {3})//;
					# Replace subsequent indents with tab
					while (/^(\t*)( {3})/) {
						s/^(\t*)( {3})/$1\t/;
					}
					# numbered indents
					s/(^\s*)1\s/${1}1. /;
					s/(^\s*)A\s/${1}A. /;
					s/(^\s*)i\s/${1}i. /;
				}
				# horizontal rule
				s/^\s*---+/- - -/;
				print;
			}
		} # if <pre> section
	} # !literal
	$preceeding = $_;
}

print STDERR "Hiding Main web links\n" if $verbose && $hide_main_web_links;
print STDERR "Creating HTML style tables\n" if $verbose && !$pandoc_table;

while (<>) {
	process_line();
}

END { close(STDOUT) || die "can't close stdout: $!" }

__END__

=encoding utf8

=head1 NAME

twiki2mdml.pl - Convert a TWiki formatted document to Markdown format.

=head1 SYNOPSIS

twiki2mdml.pl [options] [sourcefile]

 Options:

   --help                   brief help message
   --man                    full documentation
   --verbose                verbosely detail operations
   --hide-main-web-links    hides internal links to Main web
   --nopandoc-tables        converts tables to HTML tables

=head1 OPTIONS

=over 8

=item B<--help>

Prints a brief help message and exits.

=item B<--man>

Prints the full documentation and exits.

=item B<--verbose>

Outputs text to stderr detailing operations.

=item B<--hide-main-web-links>

TWiki inter web links, e.g. TWiki.WelcomeGuest, are converted to
relative links,
e.g. [TWiki/WelcomeGuest](../TWiki/WelcomeGuest.html).  This
option converts such links to simple names.  I.e. "Main.SomeOne" is
simply converted to "Some One".  This may be desirable when the Main
web is not being converted and you wish references to author names to
simply be shown as text.

=item B<--nopandoc-tables>

The Markdown [2] format does not support tables.  By default, tables
are converted to the format supported by Pandoc [3].  This option
changes that behaviour to create HTML tables instead.

=back

=head1 DESCRIPTION

twiki2mdml.pl converts TWiki [1] formatted documents to Markdown [2]
format as extended by Pandoc [3].

[1]: http://www.twiki.org/

[2]: http://daringfireball.net/projects/markdown/

[3]: http://johnmacfarlane.net/pandoc/ "Pandoc"

The document to be converted is can be specified as a parameter or
read from stdin.  The result is written to stdout.

=head1 EXAMPLES

Typical usage:

	$ cat document.twiki | twiki2mdml.pl >document.mdml

To convert many files:

	$ for file in *.twiki; do echo $file; \
	  cat $file | twiki2mdml.pl >$file.txt ; done;

=head1 BUGS

The intention of the script is to catch the majority of situations.
Testing has not been exhaustive.  Additionally, some conversion is
specific to personal requirements.  E.g. We assume a TWiki line
starting with a # is really a shell script example and indent the
output with a tab.  In any event we need to do some conversion,
otherwise Markdown will treat this as a heading.

=head1 AUTHOR

frank.dean@smartpixie.com

=cut
