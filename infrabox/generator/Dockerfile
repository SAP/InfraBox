FROM alpine:3.6

RUN apk add --no-cache python2

COPY infrabox/generator /generator

CMD python /generator/generator.py
