FROM alpine:3.6

RUN apk add --no-cache python py-requests py-bottle py-pip git
RUN pip install boddle coverage mock xmlrunner

COPY src/github/api/api.py /tests/api.py
COPY infrabox/test/github-api /tests

CMD /tests/entrypoint.sh
