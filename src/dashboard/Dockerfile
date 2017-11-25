FROM node:8.9

ENV NPM_CONFIG_LOGLEVEL=warn
ENV NODE_ENV=production

RUN apt-get -y update && apt-get install -y git

COPY src/dashboard /project
RUN mkdir /dashboard

CMD /project/entrypoint.sh
