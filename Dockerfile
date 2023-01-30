FROM ghcr.io/magfest/magprime:main

# add our code
COPY . plugins/magstock/
RUN if [ -d plugins/magstock/plugins ]; then mv plugins/magstock/plugins/* plugins/; fi
RUN /app/env/bin/paver install_deps
