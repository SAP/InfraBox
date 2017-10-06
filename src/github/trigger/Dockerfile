FROM alpine:3.6

RUN apk add --no-cache python py-requests py-psycopg2 py-bottle

COPY src/github/trigger/trigger.py /trigger.py
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python /trigger.py
