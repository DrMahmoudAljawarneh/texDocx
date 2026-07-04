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
    imagemagick \
    ghostscript \
    supervisor \
    netcat-openbsd \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-science \
    texlive-latex-recommended \
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

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY app/ /app/
RUN mkdir -p /shared

EXPOSE 3334 3335 3336
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf", "-n"]
