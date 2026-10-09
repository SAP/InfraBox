FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN wget -q --no-check-certificate -O /usr/local/bin/minio \
    "https://github.com/minio/minio/releases/download/RELEASE.2025-07-23T15-54-02Z/minio.linux-amd64.RELEASE.2025-07-23T15-54-02Z" && \
    chmod +x /usr/local/bin/minio
EXPOSE 9000
ENTRYPOINT ["minio"]
