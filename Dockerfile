FROM opencadc/matplotlib:3.8-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && apt-get dist-upgrade -y

RUN apt-get install -y \
    xvfb \
    git \
    python3-astropy \
    python3-pip \
    python3-tz \
    python3-yaml

RUN pip install  --no-cache-dir \
        cadcdata \
        cadctap \
        caom2 \
        caom2repo \
        caom2utils \
        deprecated \
        ftputil \
        importlib-metadata \
        PyYAML \
        pytz \
        spherical-geometry \
        vos

RUN apt-get install -y saods9

RUN mkdir -p /usr/share/man/man1
RUN apt-get install -y default-jre

RUN rm -rf /var/lib/apt/lists/ /tmp/* /var/tmp/*

RUN git clone https://github.com/HEASARC/cfitsio && \
  cd cfitsio && \
  ./configure --prefix=/usr && \
  make -j 2 && \
  make shared && \
  make install && \
  make fitscopy && \
  cp fitscopy /usr/local/bin && \
  make clean && \
  cd /usr/src/app

WORKDIR /usr/src/app

RUN pip install aplpy \
    bs4 \
    mocpy

ADD  Aladin4Daniel.jar /usr/lib

ARG OMC_BRANCH=master
ARG OMC_REPO=opencadc-metadata-curation

RUN git clone https://github.com/${OMC_REPO}/caom2pipe.git --branch ${OMC_BRANCH} --single-branch && \
    pip install ./caom2pipe

RUN git clone https://github.com/${OMC_REPO}/cfht2caom2.git && \
    cp ./cfht2caom2/scripts/config.yml / && \
    cp ./cfht2caom2/scripts/cache.yml / && \
    cp ./cfht2caom2/scripts/docker-entrypoint.sh / && \
    pip install ./cfht2caom2

RUN git clone https://github.com/${OMC_REPO}/moc2caom2.git && \
  cp ./moc2caom2/scripts/config.yml / && \
  cp ./moc2caom2/scripts/docker-entrypoint.sh / && \
  pip install ./moc2caom2

ENTRYPOINT ["/docker-entrypoint.sh"]
