FROM docker:17.12.1-ce-dind

RUN apk add --no-cache \
    python \
    py-pip \
    py-requests \
    bash \
    pigz && \
    pip install docker==2.0.1 awscli && \
    pip install docker-compose future PyJWT && \
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
CMD /usr/local/bin/entrypoint.sh
