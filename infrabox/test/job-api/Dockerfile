FROM stege/baseimage:1

RUN apk add --no-cache py-crypto py-pip
RUN pip install PyJWT

COPY infrabox/test/job-api/test.py test.py
COPY infrabox/test/job-api/entrypoint.sh entrypoint.sh
COPY src/utils/wait-for-webserver.sh wait-for-webserver.sh

RUN adduser -S tester
USER tester

CMD ["entrypoint.sh"]
