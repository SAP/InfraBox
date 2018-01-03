FROM alpine:3.6

RUN apk add --no-cache python py2-flask git openssh-client py2-pip py2-gevent bash && \
    pip install flask_restplus && \
    apk del py2-pip

ENV PYTHONPATH=/

COPY src/pyinfraboxutils /pyinfraboxutils
COPY src/job/git /git

CMD /git/entrypoint.sh
