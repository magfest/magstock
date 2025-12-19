FROM ghcr.io/magfest/ubersystem:main
ENV uber_plugins=["magstock"]

# install plugins
COPY . plugins/magstock/

RUN $HOME/.local/bin/uv pip install --system -r requirements.txt;
