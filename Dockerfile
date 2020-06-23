FROM opencadc/astropy:3.8-slim

RUN apt-get update
RUN apt-get install -y \
    build-essential \\
    git
    
RUN pip install cadcdata && \
    pip install cadctap && \
    pip install caom2 && \
    pip install caom2repo && \
    pip install caom2utils && \
    pip install deprecated && \
    pip install ftputils && \
    pip install importlib-metadata && \
    pip install pytz && \
    pip install PyYAML && \
    pip install spherical-geometry && \
    pip install vos

WORKDIR /usr/src/app

ARG OMC_REPO=opencadc-metadata-curation

RUN git clone https://github.com/${OMC_REPO}/caom2pipe.git && \
  pip install ./caom2pipe
  
RUN git clone https://github.com/${OMC_REPO}/blank2caom2.git && \
  cp ./blank2caom2/scripts/config.yml / && \
  cp ./blank2caom2/scripts/docker-entrypoint.sh / && \
  pip install ./blank2caom2

ENTRYPOINT ["/docker-entrypoint.sh"]
