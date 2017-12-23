FROM alpine:3.6

RUN apk add --no-cache py2-requests py2-bottle py2-pip git && \
    pip install boddle coverage mock xmlrunner
    # Don't delete pip, it's neccessary

COPY src/github/api/api.py /tests/api.py
COPY infrabox/test/github-api /tests

CMD /tests/entrypoint.sh
