ARG INFRABOX_BUILD_NUMBER
FROM quay.io/infrabox/images-test:build_$INFRABOX_BUILD_NUMBER

COPY infrabox/test-registry/mock-registry/server.py /server.py
ENV FLASK_APP /server.py

CMD ["flask", "run", "--host=0.0.0.0", "--port", "5000"]
