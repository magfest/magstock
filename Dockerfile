FROM ghcr.io/magfest/ubersystem:stock2019

# install plugins
COPY . plugins/magstock/

RUN /app/env/bin/paver install_deps
