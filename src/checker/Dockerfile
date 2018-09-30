ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-base:build_$INFRABOX_BUILD_NUMBER

COPY src/checker checker
COPY src/pyinfraboxutils /pyinfraboxutils

ENV PYTHONPATH=/

ENTRYPOINT ["python", "checker/checker.py"]
