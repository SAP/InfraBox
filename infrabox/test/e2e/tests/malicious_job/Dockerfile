FROM alpine:3.4

COPY script.sh /script.sh

RUN adduser -S tester
USER tester

CMD /script.sh
