FROM alpine:3.6

RUN apk add --no-cache py2-requests py2-bottle py2-pip git && \
    pip install boddle coverage mock xmlrunner && \
    apk del py2-pip

COPY src/github/api/api.py /tests/api.py
COPY infrabox/test/github-api /tests

CMD /tests/entrypoint.sh
