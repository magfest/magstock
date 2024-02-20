FROM ghcr.io/magfest/ubersystem:main

# install plugins
COPY . plugins/magstock/

RUN /app/env/bin/paver install_deps
