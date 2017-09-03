FROM node:6.10.0-alpine

RUN apk update && \
    apk add --no-cache \
        git \
        python \
        postgresql-client \
        py-requests

COPY . /project

RUN adduser -S -h /home/tester tester

RUN chown -R tester /project

USER tester

CMD /project/src/server/test/start_test.sh
