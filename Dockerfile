FROM ghcr.io/magfest/ubersystem:stock2024
ENV uber_plugins=["magstock"]

# install plugins
COPY . plugins/magstock/

RUN uv pip install --system -r plugins/magstock/requirements.txt
