"""
MCP projects endpoints.
GET /api/v1/mcp/projects
GET /api/v1/mcp/projects/<project_id>
"""
from flask import g, abort
from flask_restx import Resource

from pyinfraboxutils.ibrestplus import api
from api.handlers.mcp.auth import mcp_auth_required, check_project_access_mcp, get_mcp_user_id
from api.handlers.mcp.rate_limit import mcp_rate_limit
from api.handlers.mcp.audit import audit_mcp
from api.handlers.mcp.pagination import parse_pagination, page

ns = api.namespace('MCP Projects',
                   path='/api/v1/mcp',
                   description='MCP project operations')


@ns.route('/projects')
class MCPProjects(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_projects')
    def get(self):
        """List projects accessible to the current MCP token or session user.

        Paginated (default limit 50). Returns {items, total, limit, offset}.
        """
        audit_mcp('list_projects', outcome='attempt')
        try:
            user_id = get_mcp_user_id()
            enabled = getattr(g, 'mcp_enabled_projects', None)

            # Build a shared WHERE clause across the three access paths:
            #  - MCP token with an explicit project scope  -> filter by those ids
            #  - MCP token with empty scope, or session user -> all collaborations
            where = 'co.user_id = %s'
            params = [user_id]
            if enabled:
                where += ' AND p.id = ANY(%s::uuid[])'
                params.append(list(enabled.keys()))

            limit, offset = parse_pagination()
            total = g.db.execute_one_dict('''
                SELECT count(*) AS c
                FROM project p
                INNER JOIN collaborator co ON co.project_id = p.id AND ''' + where,
                params)['c']
            rows = g.db.execute_many_dict('''
                SELECT p.id, p.name, p.type, p.public
                FROM project p
                INNER JOIN collaborator co ON co.project_id = p.id AND ''' + where + '''
                ORDER BY p.name
                LIMIT %s OFFSET %s
            ''', params + [limit, offset])

            items = [{'id': r['id'], 'name': r['name'], 'type': r['type'], 'public': r['public']}
                     for r in rows]
            audit_mcp('list_projects', outcome='success',
                      details={'count': len(items), 'total': total})
            return page(items, total, limit, offset)
        except Exception as exc:
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
            audit_mcp('list_projects', outcome='failure', error=str(exc))
            raise


@ns.route('/projects/<project_id>')
class MCPProject(Resource):
    @mcp_auth_required
    @mcp_rate_limit('list_projects')
    def get(self, project_id):
        """Get a single project by ID."""
        audit_mcp('get_project', outcome='attempt', details={'project_id': project_id})
        if not check_project_access_mcp(project_id):
            audit_mcp('get_project', outcome='forbidden', details={'project_id': project_id})
            abort(403, 'access to this project is not permitted for the current MCP token')

        try:
            row = g.db.execute_one_dict('''
                SELECT p.id, p.name, p.type, p.public
                FROM project p
                WHERE p.id = %s
            ''', [project_id])
            if not row:
                abort(404)
            result = {'id': row['id'], 'name': row['name'], 'type': row['type'], 'public': row['public']}
            audit_mcp('get_project', outcome='success', details={'project_id': project_id})
            return result
        except Exception as exc:
            # Clear any aborted/pending transaction so the failure audit
            # (which shares g.db) can write, and no stray write is committed.
            try:
                g.db.rollback()
            except Exception:
                pass
            audit_mcp('get_project', outcome='failure',
                      details={'project_id': project_id}, error=str(exc))
            raise

