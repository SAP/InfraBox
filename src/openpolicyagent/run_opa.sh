# docker run --rm -p 8181:8181 openpolicyagent/opa:0.9.1 run --server --log-level=debug
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

export PYTHONPATH=$PYTHONPATH:$SCRIPTPATH/..
echo $PYTHONPATH

export INFRABOX_OPA_HOST=http://localhost:8181

python opa.py