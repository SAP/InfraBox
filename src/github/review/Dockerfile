ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:$INFRABOX_BUILD_NUMBER

COPY src/github/review/review.py /review.py
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD python review.py
