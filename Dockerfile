FROM opencadc/astropy:3.8-slim

RUN apt-get update
RUN apt-get install -y \
    build-essential \
    git
    
RUN pip install cadcdata\
    cadctap \
    caom2 \
    caom2repo \
    caom2utils \
    deprecated \
    importlib-metadata \
    pytz \
    PyYAML \
    spherical-geometry \
    vos

WORKDIR /usr/src/app

RUN apt-get install -y default-jre

RUN pip install mocpy

ADD  Aladin4Daniel.jar /usr/lib

ARG OMC_BRANCH=master
ARG OMC_REPO=opencadc-metadata-curation

RUN git clone https://github.com/${OMC_REPO}/caom2pipe.git --branch ${OMC_BRANCH} --single-branch && \
  pip install ./caom2pipe

RUN git clone https://github.com/${OMC_REPO}/moc2caom2.git && \
  cp ./moc2caom2/scripts/config.yml / && \
  cp ./moc2caom2/scripts/docker-entrypoint.sh / && \
  pip install ./moc2caom2

RUN git clone https://github.com/${OMC_REPO}/moc2caom2.git && \
  cp ./moc2caom2/scripts/config.yml / && \
  cp ./moc2caom2/scripts/docker-entrypoint.sh / && \
  pip install ./moc2caom2

ENTRYPOINT ["/docker-entrypoint.sh"]
