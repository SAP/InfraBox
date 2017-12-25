FROM alpine:3.6

RUN apk add --no-cache py2-psycopg2 py2-pip py2-jwt py2-cryptography py2-requests git && \
    pip install xmlrunner

ENV PYTHONPATH=/infrabox/context/src

CMD /infrabox/context/infrabox/test/e2e-compose/entrypoint.sh
