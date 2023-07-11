FROM openpolicyagent/opa:0.10.7-debug

ENV PYTHONPATH=/

COPY src/openpolicyagent/policies /policies
WORKDIR /policies

CMD ["run", "/policies", "--server", "--log-level=debug"]
