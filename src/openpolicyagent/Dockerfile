FROM openpolicyagent/opa:0.10.5

ENV PYTHONPATH=/

COPY src/openpolicyagent/policies /policies
WORKDIR /policies

CMD ["run", "/policies", "--server", "--log-level=debug"]