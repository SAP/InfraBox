FROM stege/baseimage:1

RUN apk add --no-cache py-pip py-yaml git
RUN pip install coverage future

COPY src/pyinfrabox  /pyinfrabox
COPY infrabox/test-pyinfrabox/entrypoint.sh /pyinfrabox/entrypoint.sh

WORKDIR /pyinfrabox

RUN adduser -S tester
RUN chown -R tester /pyinfrabox

USER tester

CMD /pyinfrabox/entrypoint.sh
