FROM alpine:3.6

RUN apk add --no-cache python py-requests py-psycopg2

COPY src/github/review/review.py /review.py
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python review.py
