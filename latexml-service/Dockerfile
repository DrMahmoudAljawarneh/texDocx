FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    gcc \
    git \
    perl \
    libxml-libxml-perl \
    libxml-libxslt-perl \
    libarchive-zip-perl \
    libjson-perl \
    libtext-unidecode-perl \
    libwww-perl \
    liburi-perl \
    libio-string-perl \
    libimage-magick-perl \
    libparse-recdescent-perl \
    libhttp-daemon-perl \
    libfile-which-perl \
    libpod-parser-perl \
    libjson-xs-perl \
    libimage-size-perl \
    imagemagick \
    ghostscript \
    supervisor \
    curl \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-science \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/brucemiller/LaTeXML.git /tmp/latexml && \
    cd /tmp/latexml && \
    perl Makefile.PL && \
    make && \
    make install && \
    rm -rf /tmp/latexml

RUN git clone --depth 1 https://github.com/dginev/LaTeXML-Plugin-latexmls.git /tmp/latexmls-plugin && \
    cd /tmp/latexmls-plugin && \
    perl Makefile.PL && \
    make && \
    make install && \
    rm -rf /tmp/latexmls-plugin

# Copy custom LaTeXML package bindings (overriding defaults)
COPY bindings/ /tmp/latexml-bindings/
RUN for f in /tmp/latexml-bindings/*; do \
      pkgdir=$(find /usr/local/share/perl -path "*/LaTeXML/Package" -type d | head -1); \
      [ -n "$pkgdir" ] && cp "$f" "$pkgdir/" && echo "Installed $f -> $pkgdir/"; \
    done && rm -rf /tmp/latexml-bindings

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY app/ /app/
RUN mkdir -p /shared

EXPOSE 3334 3335 3336
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf", "-n"]
