FROM alpine:3.4

RUN apk update && apk add --no-cache python py-pip py-psycopg2 postgresql-client && \
    pip install flask && \
    apk del py-pip

COPY src/docker-registry/auth/server.py /server.py
COPY src/utils/wait-for-postgres.sh /wait-for-postgres.sh

ENV FLASK_APP /server.py

RUN adduser -S auth
USER auth

CMD ["flask", "run", "--host=0.0.0.0", "--port", "8080"]
