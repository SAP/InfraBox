FROM alpine:3.6

RUN apk add --no-cache python py-requests py-psycopg2

ADD src/github/review/review.py /review.py

CMD python review.py
