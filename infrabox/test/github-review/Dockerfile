FROM alpine:3.6

RUN apk add --no-cache python py-requests py-pip git py-psycopg2
RUN pip install coverage mock xmlrunner codecov

ENV PYTHONPATH=/infrabox/context/src:/infrabox/context/src/github/review

WORKDIR /infrabox/context/infrabox/test/github-review

CMD ../utils/python_tests.sh /infrabox/context/src/github/review
