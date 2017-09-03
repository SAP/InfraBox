FROM node:6.9.2-alpine

ENV NPM_CONFIG_LOGLEVEL=warn
ENV NODE_ENV=production

RUN apk add --no-cache git postgresql-client

COPY src/api /project
COPY src/utils/wait-for-postgres.sh /wait-for-postgres.sh
RUN mkdir /api

RUN adduser -S server
RUN chown -R server /project
RUN chown -R server /api

USER server

CMD /project/entrypoint.sh
