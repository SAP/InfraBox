FROM stege/baseimage:1

COPY src/api-server/test/test.py test.py
COPY src/api-server/test/entrypoint.sh entrypoint.sh
COPY src/utils/wait-for-webserver.sh wait-for-webserver.sh

RUN adduser -S tester
USER tester

CMD ["entrypoint.sh"]
