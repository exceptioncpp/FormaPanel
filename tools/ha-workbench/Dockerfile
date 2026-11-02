ARG BUILD_FROM=ghcr.io/esphome/esphome-hassio:2026.10.1
FROM ${BUILD_FROM}
WORKDIR /app
COPY server.py /app/server.py
COPY web /app/web
ENV ESPHOME_IS_HA_ADDON="" ESPHOME_ESP_IDF_PREFIX=/data/cache/idf ESPHOME_HOST_PREFIX=/data/cache/host
ENTRYPOINT ["python", "-u", "/app/server.py"]
