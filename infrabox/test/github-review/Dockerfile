FROM alpine:3.6

RUN apk add --no-cache python py-requests py-pip git py-psycopg2
RUN pip install coverage mock xmlrunner

COPY src/github/review/review.py /tests/review.py
COPY infrabox/test/github-review /tests
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD /tests/entrypoint.sh
