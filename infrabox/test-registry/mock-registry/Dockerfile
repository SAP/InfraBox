FROM alpine:3.4

RUN apk add --no-cache python py-pip
RUN pip install flask

COPY infrabox/test-registry/mock-registry/server.py /server.py
ENV FLASK_APP /server.py

RUN adduser -S registry
USER registry

CMD ["flask", "run", "--host=0.0.0.0", "--port", "5000"]
