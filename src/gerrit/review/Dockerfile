ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

COPY src/gerrit/review/review.py /review.py
COPY src/gerrit/review/entrypoint.sh /entrypoint.sh
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

CMD /entrypoint.sh
