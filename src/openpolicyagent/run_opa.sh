SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

export PYTHONPATH=$PYTHONPATH:$SCRIPTPATH/..
echo $PYTHONPATH

export INFRABOX_OPA_HOST=wdfl33986622b.emea.global.corp.sap
export INFRABOX_OPA_PORT=8181

python opa.py

#docker build ./ -t infrabox/opa 

#docker run --rm -p 8181:8181 infrabox/opa run --server --log-level=debug