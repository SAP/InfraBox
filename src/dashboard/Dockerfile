FROM node:8.4-alpine

ENV NPM_CONFIG_LOGLEVEL=warn
ENV NODE_ENV=production

RUN apk add --no-cache git python make g++

COPY src/dashboard /project
RUN mkdir /dashboard

CMD /project/entrypoint.sh
