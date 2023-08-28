FROM public.ecr.aws/docker/library/alpine

COPY script.sh /script.sh

RUN adduser -S tester
USER tester

CMD /script.sh
