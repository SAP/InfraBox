FROM alpine:3.6

RUN apk add --no-cache py2-pip py2-yaml py-nose git && \
    pip install coverage future && \
    apk del py2-pip

COPY src/pyinfrabox  /pyinfrabox
COPY infrabox/test-pyinfrabox/entrypoint.sh /pyinfrabox/entrypoint.sh

WORKDIR /pyinfrabox

RUN adduser -S tester
RUN chown -R tester /pyinfrabox

USER tester

CMD /pyinfrabox/entrypoint.sh
