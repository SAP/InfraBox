FROM alpine:3.6

RUN apk add --no-cache python3

COPY infrabox/generator /generator

CMD python3 /generator/generator.py
