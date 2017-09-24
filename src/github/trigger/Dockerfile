FROM alpine:3.6

RUN apk add --no-cache python py-requests py-psycopg2 py-bottle

ADD src/github/trigger/trigger.py /trigger.py

CMD python /trigger.py
