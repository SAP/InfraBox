FROM alpine:3.4

COPY infrabox/test-malicious/script.sh /script.sh

RUN adduser -S tester
USER tester

CMD /script.sh
