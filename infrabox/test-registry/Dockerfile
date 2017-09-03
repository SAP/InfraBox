FROM stege/baseimage:1

COPY infrabox/test-registry/test.py test.py
COPY infrabox/test-registry/entrypoint.sh entrypoint.sh
COPY src/utils/wait-for-webserver.sh wait-for-webserver.sh

RUN adduser -S tester
USER tester

CMD ["entrypoint.sh"]
