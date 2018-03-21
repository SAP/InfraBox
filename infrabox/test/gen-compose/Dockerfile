FROM alpine:3.6

RUN apk add --no-cache python openssh py2-yaml py2-yaml py2-crypto

RUN mkdir /generate
WORKDIR /generate

CMD /infrabox/context/infrabox/test/gen-compose/entrypoint.sh
