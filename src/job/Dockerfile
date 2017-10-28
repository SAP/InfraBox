FROM docker:1.12.6-dind

RUN apk add --no-cache \
    python \
    py-pip \
    py-requests \
    bash \
    openssh-client \
    pigz && \
    pip install docker-compose docker future PyJWT && \
    apk del py-pip

COPY src/job /job

COPY src/job/ecr_login.sh /usr/local/bin/
COPY src/job/get_compose_exit_code.sh /usr/local/bin/
COPY src/job/entrypoint.sh /usr/local/bin/

COPY src/pyinfrabox /pyinfrabox
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/utils:/
ENV PATH=/utils:$PATH

RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT /usr/local/bin/entrypoint.sh
