ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-test:build_$INFRABOX_BUILD_NUMBER

ENV PYTHONPATH=/infrabox/context/src:/infrabox/context/src/github/review

WORKDIR /infrabox/context/infrabox/test/github-review

CMD ../utils/python_tests.sh /infrabox/context/src/github/review
