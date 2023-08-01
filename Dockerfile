FROM ghcr.io/magfest/ubersystem:stock2023

# install plugins
COPY . plugins/magstock/
RUN git clone --depth 1 --branch stock2023 https://github.com/magfest/covid.git plugins/covid

RUN /app/env/bin/paver install_deps
