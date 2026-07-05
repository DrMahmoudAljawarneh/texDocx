#!/usr/bin/perl
use strict;
use warnings;
use HTTP::Daemon;
use HTTP::Status;
use IO::File;
use File::Temp qw(tempfile);
use File::Basename;
use HTTP::Response;

my $port = $ARGV[0] || 3334;
my $host = $ARGV[1] || '0.0.0.0';

my $d = HTTP::Daemon->new(
    LocalAddr => $host,
    LocalPort => $port,
    Reuse     => 1,
) or die "Cannot start daemon on $host:$port: $!";

print "latexmls daemon listening on $host:$port\n";

sub parse_form_data {
    my $content = shift;
    my %params;
    foreach my $pair (split /&/, $content) {
        my ($name, $value) = split /=/, $pair, 2;
        if (defined $name && defined $value) {
            $value =~ tr/+/ /;
            $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
            $params{$name} = $value;
        }
    }
    return %params;
}

sub handle_latexml {
    my ($source, $c) = @_;
    my ($fh, $tmpfile) = tempfile(UNLINK => 1);
    print $fh $source;
    close $fh;

    my ($fh_out, $tmpfile_out) = tempfile(UNLINK => 1);
    close $fh_out;
    my ($fh_err, $tmpfile_err) = tempfile(UNLINK => 1);
    close $fh_err;

    `latexml --dest=$tmpfile_out $tmpfile 2>$tmpfile_err`;
    my $exit = $? >> 8;

    my $xml_output = "";
    if (-e $tmpfile_out) {
        open my $fh_xml, '<', $tmpfile_out or die "Can't open $tmpfile_out: $!";
        local $/;
        $xml_output = <$fh_xml>;
        close $fh_xml;
        unlink $tmpfile_out;
    }

    my $err_output = "";
    if (-e $tmpfile_err) {
        open my $fh_err_file, '<', $tmpfile_err or die "Can't open $tmpfile_err: $!";
        local $/;
        $err_output = <$fh_err_file>;
        close $fh_err_file;
        unlink $tmpfile_err;
    }

    unlink $tmpfile;

    if ($exit != 0) {
        warn "LaTeXML failed with exit code $exit:\n$err_output\n";
        my $res = HTTP::Response->new(500);
        $res->content("LaTeXML compilation failed:\n" . $err_output);
        $res->content_type("text/plain");
        $c->send_response($res);
    } else {
        my $res = HTTP::Response->new(200);
        $res->content($xml_output);
        $res->content_type("application/xml");
        $c->send_response($res);
    }
}

sub handle_render_png {
    my ($source, $c) = @_;
    my $tmpdir = File::Temp->newdir();
    my $tex_path = "$tmpdir/doc.tex";
    my $pdf_path = "$tmpdir/doc.pdf";
    my $png_path = "$tmpdir/doc.png";

    open my $fh, '>', $tex_path or die "Cannot write $tex_path: $!";
    print $fh $source;
    close $fh;

    my $pdflatex_out = `cd $tmpdir && pdflatex -interaction=nonstopmode doc.tex 2>&1`;
    my $exit = $? >> 8;

    if ($exit != 0 || !-e $pdf_path) {
        my $res = HTTP::Response->new(500);
        $res->content("pdflatex failed (exit $exit):\n$pdflatex_out");
        $res->content_type("text/plain");
        $c->send_response($res);
        return;
    }

    `gs -dNOPAUSE -dBATCH -sDEVICE=png16m -r200 -dSAFER -sOutputFile="$png_path" "$pdf_path" 2>/dev/null`;

    if (!-e $png_path) {
        my $res = HTTP::Response->new(500);
        $res->content("Failed to convert PDF to PNG");
        $res->content_type("text/plain");
        $c->send_response($res);
        return;
    }

    open my $fh_png, '<', $png_path or die "Cannot read $png_path: $!";
    binmode $fh_png;
    local $/;
    my $png_data = <$fh_png>;
    close $fh_png;

    my $res = HTTP::Response->new(200);
    $res->content($png_data);
    $res->content_type("image/png");
    $c->send_response($res);
}

while (my $c = $d->accept) {
    while (my $r = $c->get_request) {
        if ($r->method ne 'POST') {
            $c->send_error(RC_FORBIDDEN, "Only POST allowed");
            next;
        }
        my $path = $r->url->path || '/';
        my %params = parse_form_data($r->content);
        my $source = $params{'source'} || '';

        if ($path eq '/render-png') {
            handle_render_png($source, $c);
        } else {
            handle_latexml($source, $c);
        }
    }
    $c->close;
}
