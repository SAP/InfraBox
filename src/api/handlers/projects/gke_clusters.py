"""GKE cluster provisioning API for external CI consumers (e.g. GitHub Actions).

Thin orchestration on top of the existing InfraBox GCP operator: creates and
manages `GKECluster` custom resources in the worker namespace.  The operator
(already deployed) performs the actual GKE cluster lifecycle.

v0 endpoints (all under /api/v1/projects/<project_id>/gke-clusters):
    POST   /                        Create a cluster (async, returns 202)
    GET    /<name>                  Get cluster status
    GET    /<name>/kubeconfig       Fetch kubeconfig (only when status=ready)
    DELETE /<name>                  Delete the cluster
"""

import base64
import os
import uuid

import requests
from flask import Response, abort, g, request
from flask_restx import Resource, fields

from pyinfraboxutils.ibrestplus import api


# --------------------------------------------------------------------------- #
# Namespace registration
# --------------------------------------------------------------------------- #

ns = api.namespace(
    'GKEClusters',
    path='/api/v1/projects/<project_id>/gke-clusters',
    description='Ephemeral GKE cluster provisioning for external CI consumers',
)


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

CR_GROUP = 'gcp.service.infrabox.net'
CR_VERSION = 'v1alpha1'
CR_PLURAL = 'gkeclusters'

# Same shape scheduler.py already uses to talk to the K8s API server.
K8S_TOKEN_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/token'
K8S_CA_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt'


# --------------------------------------------------------------------------- #
# Kubernetes helpers (thin wrapper on top of requests, same pattern as
# scheduler.py so we don't need to add the `kubernetes` python client dep)
# --------------------------------------------------------------------------- #

def _worker_namespace():
    """Namespace in which GKECluster CRs and their kubeconfig secrets live.

    Same env var that the scheduler reads (see scheduler.py:main).  It is
    injected into the API pod via the `env_general` Helm template.
    """
    return os.environ['INFRABOX_GENERAL_WORKER_NAMESPACE']


def _k8s_api_base():
    """In-cluster K8s API server URL."""
    host = os.environ.get('INFRABOX_KUBERNETES_MASTER_HOST', 'kubernetes.default')
    port = os.environ.get('INFRABOX_KUBERNETES_MASTER_PORT', '443')
    return 'https://{}:{}'.format(host, port)


def _k8s_headers():
    with open(K8S_TOKEN_PATH, 'r') as f:
        token = f.read().strip()
    return {
        'Authorization': 'Bearer {}'.format(token),
        'Content-Type': 'application/json',
    }


def _k8s_verify():
    """Path to the CA bundle used to verify the K8s API server certificate."""
    return K8S_CA_PATH if os.path.exists(K8S_CA_PATH) else True


def _cr_url(name=None):
    base = '{api}/apis/{group}/{version}/namespaces/{ns}/{plural}'.format(
        api=_k8s_api_base(),
        group=CR_GROUP,
        version=CR_VERSION,
        ns=_worker_namespace(),
        plural=CR_PLURAL,
    )
    return '{}/{}'.format(base, name) if name else base


def _secret_url(name):
    return '{api}/api/v1/namespaces/{ns}/secrets/{name}'.format(
        api=_k8s_api_base(),
        ns=_worker_namespace(),
        name=name,
    )


def _handle_k8s_status(resp, on_not_found_msg='not found'):
    """Translate a non-2xx K8s response into a Flask abort."""
    if resp.status_code == 404:
        abort(404, on_not_found_msg)
    if not resp.ok:
        abort(502, 'kubernetes api error: {} {}'.format(
            resp.status_code, resp.text[:200]))


# --------------------------------------------------------------------------- #
# Authorization helpers
# --------------------------------------------------------------------------- #

def _current_user_id():
    """Return current user id from the JWT.  Only user tokens are supported
    for v0 (OPA rules require token.type=user)."""
    token = getattr(g, 'token', None) or {}
    if token.get('type') != 'user':
        abort(403, 'user token required')
    user = token.get('user') or {}
    uid = user.get('id')
    if not uid:
        abort(403, 'user id missing in token')
    return uid


def _check_membership(project_id):
    """Ensure the current user is a collaborator on project_id."""
    user_id = _current_user_id()
    row = g.db.execute_one('''
        SELECT 1 FROM collaborator
        WHERE user_id = %s AND project_id = %s
    ''', [user_id, project_id])
    if not row:
        abort(403, 'not a project collaborator')


def _check_ownership(cr, project_id):
    """Ensure the CR belongs to the given project (label match).

    Guards against cross-project reads / deletes via crafted URLs.
    """
    labels = (cr.get('metadata') or {}).get('labels') or {}
    if labels.get('infrabox.net/project-id') != str(project_id):
        abort(403, 'cluster does not belong to this project')


# --------------------------------------------------------------------------- #
# Request / response models (Swagger docs only, not strict validation)
# --------------------------------------------------------------------------- #

create_model = api.model('GKEClusterCreate', {
    'zone':        fields.String(required=True, description='GCP zone, e.g. us-east1-b'),
    'numNodes':    fields.Integer(required=False, description='Node count', default=1),
    'machineType': fields.String(required=False, description='GCP machine type',
                                 default='n1-standard-1'),
    'preemptible': fields.Boolean(required=False, description='Use preemptible VMs',
                                  default=True),
    'diskSize':    fields.Integer(required=False, description='Node disk size in GB',
                                  default=100),
})

status_model = api.model('GKEClusterStatus', {
    'name':        fields.String(description='CR name (also the K8s Secret name)'),
    'status':      fields.String(description='pending | creating | ready | error | ...'),
    'message':     fields.String(description='Operator-provided status message'),
    'clusterName': fields.String(description='GKE cluster name once created'),
})


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@ns.route('')
class GKEClusterList(Resource):

    @api.expect(create_model)
    def post(self, project_id):
        """Create a new ephemeral GKE cluster.

        Returns 202 with the CR name; poll GET /<name> until status=ready.
        """
        _check_membership(project_id)

        body = request.get_json(force=True, silent=True) or {}
        zone = body.get('zone')
        if not zone:
            abort(400, 'zone is required')

        name = 'api-{}'.format(uuid.uuid4().hex[:12])

        cr = {
            'apiVersion': '{}/{}'.format(CR_GROUP, CR_VERSION),
            'kind': 'GKECluster',
            'metadata': {
                'name': name,
                'namespace': _worker_namespace(),
                'labels': {
                    # Operator uses this label to name the output Secret.
                    'service.infrabox.net/secret-name': name,
                    # Ownership + provenance labels for GC and audit.
                    'infrabox.net/created-by': 'api',
                    'infrabox.net/project-id': str(project_id),
                    'infrabox.net/created-by-user': _current_user_id(),
                },
            },
            'spec': {
                'zone': zone,
                'numNodes': int(body.get('numNodes', 1)),
                'machineType': body.get('machineType', 'n1-standard-1'),
                'preemptible': bool(body.get('preemptible', True)),
                'diskSize': int(body.get('diskSize', 100)),
            },
        }

        resp = requests.post(
            _cr_url(),
            headers=_k8s_headers(),
            verify=_k8s_verify(),
            json=cr,
            timeout=15,
        )
        if resp.status_code == 409:
            abort(409, 'cluster already exists')
        if not resp.ok:
            abort(502, 'kubernetes api error: {} {}'.format(
                resp.status_code, resp.text[:200]))

        return {'name': name, 'status': 'pending'}, 202


@ns.route('/<name>')
class GKEClusterItem(Resource):

    def get(self, project_id, name):
        """Get the current status of a GKE cluster."""
        _check_membership(project_id)

        resp = requests.get(
            _cr_url(name),
            headers=_k8s_headers(),
            verify=_k8s_verify(),
            timeout=15,
        )
        _handle_k8s_status(resp, 'cluster not found')

        cr = resp.json()
        _check_ownership(cr, project_id)

        st = cr.get('status') or {}
        return {
            'name': name,
            'status': st.get('status') or 'pending',
            'message': st.get('message'),
            'clusterName': st.get('clusterName'),
        }, 200

    def delete(self, project_id, name):
        """Delete the GKE cluster (async via operator finalizer)."""
        _check_membership(project_id)

        # First fetch the CR to enforce ownership, then delete.
        resp = requests.get(
            _cr_url(name),
            headers=_k8s_headers(),
            verify=_k8s_verify(),
            timeout=15,
        )
        _handle_k8s_status(resp, 'cluster not found')
        _check_ownership(resp.json(), project_id)

        del_resp = requests.delete(
            _cr_url(name),
            headers=_k8s_headers(),
            verify=_k8s_verify(),
            timeout=15,
        )
        _handle_k8s_status(del_resp, 'cluster not found')
        return {'name': name, 'status': 'deleting'}, 202


@ns.route('/<name>/kubeconfig')
class GKEClusterKubeconfig(Resource):

    def get(self, project_id, name):
        """Fetch the kubeconfig for a ready cluster.

        Returns 409 if the cluster is not yet ready.
        Returns the kubeconfig YAML directly (Content-Type: application/yaml).
        """
        _check_membership(project_id)

        # 1) Fetch CR, check ownership + readiness.
        cr_resp = requests.get(
            _cr_url(name),
            headers=_k8s_headers(),
            verify=_k8s_verify(),
            timeout=15,
        )
        _handle_k8s_status(cr_resp, 'cluster not found')

        cr = cr_resp.json()
        _check_ownership(cr, project_id)

        cr_status = ((cr.get('status') or {}).get('status')) or 'pending'
        if cr_status != 'ready':
            abort(409, 'cluster not ready (status={})'.format(cr_status))

        # 2) Fetch the Secret produced by the operator.  By convention the
        #    Secret is named after the CR (see the `secret-name` label above).
        sec_resp = requests.get(
            _secret_url(name),
            headers=_k8s_headers(),
            verify=_k8s_verify(),
            timeout=15,
        )
        _handle_k8s_status(sec_resp, 'kubeconfig secret not found')

        secret = sec_resp.json()
        data = secret.get('data') or {}
        kubeconfig_b64 = data.get('kubeconfig')
        if not kubeconfig_b64:
            abort(500, 'kubeconfig field missing in secret')

        try:
            kubeconfig_yaml = base64.b64decode(kubeconfig_b64).decode('utf-8')
        except Exception:  # pragma: no cover - defensive
            abort(500, 'failed to decode kubeconfig from secret')

        return Response(kubeconfig_yaml, mimetype='application/yaml')