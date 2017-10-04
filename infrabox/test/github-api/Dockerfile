FROM alpine:3.6

RUN apk add --no-cache python py-requests py-bottle py-pip git
RUN pip install boddle coverage mock xmlrunner

ADD src/github/api/api.py /tests/api.py
ADD infrabox/test/github-api /tests

CMD /tests/entrypoint.sh
