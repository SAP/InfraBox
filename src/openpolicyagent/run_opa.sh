docker build ../../src/openpolicyagent -t infrabox/opa 

docker run --rm -p 8181:8181 infrabox/opa run --server --log-level=debug