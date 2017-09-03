import { Router } from "express";
import { Request, Response } from "express";
import { auth } from "../../utils/auth";
import { OK, BadRequest } from "../../utils/status";
import { db, handleDBError } from "../../db";
import { getRepos, getRepo, createDeployKey, createHook } from "../../utils/github";

const router = Router();
router.use(auth);

module.exports = router;

router.get("/repos", (req: Request, res: Response, next) => {
    const user_id = req['user'].id;

    let repos = null;

    db.one(`
        SELECT github_api_token FROM "user" WHERE id = $1
    `, [user_id])
    .then((user: any) => {
        return getRepos(user.github_api_token);
    }).then((r: any[]) => {
        repos = r;
        return db.task((t) => {
            const queries = [];
            for (const repo of repos) {
                const q = db.any("SELECT github_id FROM repository WHERE github_id = $1", [repo.id]);
                queries.push(q);
            }
            return t.batch(queries);
        });
    }).then((result: any[]) => {
        for (const match of result) {
            if (match.length > 0) {
                for (const repo of repos) {
                    if (repo.id === match[0].github_id) {
                        repo.connected = true;
                        break;
                    }
                }
            }
        }

        res.json(repos);
    }).catch(handleDBError(next));
});

router.post("/repo/:owner/:repo/connect", (req: Request, res: Response, next) => {
    let repo = null;
    const owner = req.params['owner'];
    const repo_name = req.params['repo'];
    const user_id = req['user'].id;
    let api_token = null;

    db.tx((tx) => {
        return tx.one(`
            SELECT github_api_token FROM "user" WHERE id = $1
        `, [user_id])
        .then((user: any) => {
            api_token = user.github_api_token;
            return getRepo(user.github_api_token, repo_name, owner);
        }).then((r: any) => {
            // check for admin permissions
            if (!r.permissions.admin) {
                throw new BadRequest("No permission");
            }

            repo = r;

            return tx.any('SELECT * FROM repository WHERE github_id = $1', [repo.id]);
        }).then((repos: any[]) => {
            if (repos.length > 0) {
                throw new BadRequest("Repository already connected");
            }

            return tx.one(`
                INSERT INTO project(name, type) VALUES ($1, 'github') RETURNING *;
            `, [repo.name]);
        }).then((project) => {
            return tx.none(`
                INSERT INTO collaborator (user_id, project_id, owner) VALUES ($1, $2, true);
                INSERT INTO repository (name, html_url, clone_url, github_id, private, project_id) VALUES ($3, $4, $5, $6, $7, $2);
            `, [req['user'].id, project.id, repo.name, repo.html_url, repo.clone_url, repo.id, repo.private]);
        }).then(() => {
            return createHook(api_token, repo_name, owner);
        }).then((hook: any) => {
            return tx.none('UPDATE repository SET github_hook_id = $1 WHERE github_id = $2', [hook.id, repo.id]);
        }).then(() => {
            return OK(res, "successfully connected repo");
        });
    }).catch(handleDBError(next));
});
