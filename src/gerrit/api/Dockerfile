ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

COPY src/gerrit/api/api.py /api.py
COPY src/gerrit/api/entrypoint.sh /entrypoint.sh

CMD /entrypoint.sh
