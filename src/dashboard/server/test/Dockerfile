FROM node:6.9.2-alpine

RUN apk add --no-cache git postgresql-client

COPY . /project

RUN adduser -S server
RUN chown -R server /project

USER server

CMD /project/src/dashboard/server/test/entrypoint.sh
