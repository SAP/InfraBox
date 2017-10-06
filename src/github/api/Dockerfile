FROM alpine:3.6

RUN apk add --no-cache python py-requests py-bottle

COPY src/github/api/api.py /api.py

CMD python /api.py
