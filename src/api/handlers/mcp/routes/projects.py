"""
MCP projects endpoint: GET /api/v1/mcp/projects
Returns projects the MCP token has access to.
"""
from flask import g
from flask_restx import Resource

from pyinfraboxutils.ibrestplus import api
from api.handlers.mcp.auth import mcp_auth_required, get_mcp_user_id
from api.handlers.mcp.rate_limit import mcp_rate_limit
from api.handlers.mcp.audit import audit_mcp

ns = api.namespace('MCP Projects',
                   path='/api/v1/mcp',
                   description='MCP project operations')


@ns.route('/projects')
class MCPProjects(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_projects')
    def get(self):
        """List projects accessible to the current MCP token or session user."""
        audit_mcp('list_projects', outcome='attempt')
        try:
            user_id = get_mcp_user_id()
            enabled = getattr(g, 'mcp_enabled_projects', None)

            if enabled is not None:
                # MCP token path: return only scoped projects where the token owner
                # is still a collaborator — re-validate membership at query time so
                # a revoked collaborator cannot enumerate project metadata.
                if not enabled:
                    audit_mcp('list_projects', outcome='success', details={'count': 0})
                    return []

                project_ids = list(enabled.keys())
                rows = g.db.execute_many_dict('''
                    SELECT p.id, p.name, p.type, p.public
                    FROM project p
                    INNER JOIN collaborator co ON co.project_id = p.id AND co.user_id = %s
                    WHERE p.id = ANY(%s::uuid[])
                    ORDER BY p.name
                ''', [user_id, project_ids])
            else:
                # Session path: return all projects the user is a collaborator on
                rows = g.db.execute_many_dict('''
                    SELECT p.id, p.name, p.type, p.public
                    FROM project p
                    INNER JOIN collaborator co ON co.project_id = p.id AND co.user_id = %s
                    ORDER BY p.name
                ''', [user_id])

            result = [{'id': r['id'], 'name': r['name'], 'type': r['type'], 'public': r['public']}
                      for r in rows]
            audit_mcp('list_projects', outcome='success', details={'count': len(result)})
            return result
        except Exception as exc:
            audit_mcp('list_projects', outcome='failure', error=str(exc))
            raise
