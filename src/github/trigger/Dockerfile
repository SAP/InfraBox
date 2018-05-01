FROM alpine:3.7

RUN apk add --no-cache python2 py2-requests py2-psycopg2 py2-bottle py2-urllib3

COPY src/github/trigger/trigger.py /trigger.py
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python /trigger.py
