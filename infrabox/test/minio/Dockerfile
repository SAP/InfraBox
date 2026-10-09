FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends wget ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN wget -q -O /usr/local/bin/minio \
    "https://dl.min.io/server/minio/release/linux-amd64/archive/minio.RELEASE.2022-11-08T05-27-07Z" && \
    chmod +x /usr/local/bin/minio
EXPOSE 9000
ENTRYPOINT ["minio"]
