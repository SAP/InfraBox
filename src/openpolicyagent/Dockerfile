FROM openpolicyagent/opa:0.9.1

COPY src/pyinfraboxutils /pyinfraboxutils
COPY src/openpolicyagent/policies /policies
WORKDIR /policies

CMD ["run", "/policies", "--server", "--log-level=debug"]