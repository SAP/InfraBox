FROM stege/baseimage:1

COPY src/job-api/test/test.py test.py
COPY src/job-api/test/entrypoint.sh entrypoint.sh
COPY src/utils/wait-for-webserver.sh wait-for-webserver.sh

RUN adduser -S tester
USER tester

CMD ["entrypoint.sh"]
