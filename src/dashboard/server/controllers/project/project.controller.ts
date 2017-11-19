"use strict";

import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { param_validation as pv } from "../../utils/validation";
import { OK, BadRequest, NotFound } from "../../utils/status";
import { Validator } from 'jsonschema';
import { getRepos, getRepo, createDeployKey, createHook } from "../../utils/github";
import { auth } from "../../utils/auth";

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/", pv, auth, (req: Request, res: Response, next) => {
    const user_id = req['user'].id;

    db.any(`SELECT p.id, p.name, p.type FROM project p
            INNER JOIN collaborator co
            ON co.project_id = p.id AND $1 = co.user_id
            ORDER BY p.name`, [user_id]).then((projects: any[]) => {
            res.json(projects);
        }).catch(handleDBError(next));
});

const AddProjectSchema = {
    id: "/EnvVarSchema",
    type: "object",
    properties: {
        name: { type: "string", pattern: "^[0-9a-zA-Z_-]+$", minLength: 2, maxLength: 20 },
        private: { type: "boolean" },
        type: ["upload", "gerrit"],
        github_repo_name: { type: "string" }
    },
    required: ["name", "private", "type"]
};

router.post("/", pv, auth, (req: Request, res: Response, next) => {
    const v = new Validator();
    const envResult = v.validate(req['body'], AddProjectSchema);

    if (envResult.errors.length > 0) {
        return next(new BadRequest(envResult.errors[0].message));
    }

    const name = req['body']['name'];
    const typ = req['body']['type'];
    const priv = req['body']['private'] === 'true';
    const github_repo_name = req['body']['github_repo_name'];

    const user_id = req['user'].id;
    let project_id = null;
    let api_token = null;
    let repo = null;

    db.tx((tx) => {
        return tx.one(`SELECT COUNT(*) as cnt
                        FROM project p
                        INNER JOIN collaborator co
                        ON p.id = co.project_id
                        AND co.user_id = $1`, [user_id]
        ).then((data: any) => {
            if (data.cnt > 50) {
                throw new BadRequest("too many projects");
            }

            return tx.one("SELECT count(*) as cnt FROM project WHERE name = $1", [name]);
        }).then((data: any) => {
            if (data.cnt > 0) {
                throw new BadRequest("A project with this name already exists");
            }

            if (typ === "github") {
                if (!github_repo_name) {
                    throw new BadRequest("github_repo_name not set");
                }

                const split = github_repo_name.split('/');
                const owner = split[0];
                const repo_name = split[1];

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
                });
            }
        }).then(() => {
            return tx.one("INSERT INTO project (name, type, public) VALUES ($1, $2, $3) RETURNING id",
                [name, typ, !priv]);
        }).then((result: any) => {
            project_id = result.id;
            return tx.none("INSERT INTO collaborator (user_id, project_id, owner) VALUES ($1, $2, true)",
                [user_id, project_id]
            );
        }).then(() => {
            if (typ === "github") {
                const split = github_repo_name.split('/');
                const owner = split[0];
                const repo_name = split[1];

                return tx.none(`
                    INSERT INTO repository (name, html_url, clone_url, github_id, private, project_id, github_owner)
                    VALUES ($1, $2, $3, $4, $5, $6, $7);
                `, [repo.name, repo.html_url,
                    repo.clone_url, repo.id, repo.private, project_id, repo.owner.login]
                ).then(() => {
                    return createHook(api_token, repo_name, owner);
                }).then((hook: any) => {
                    return tx.none(`UPDATE repository SET github_hook_id = $1
                                    WHERE github_id = $2`, [hook.id, repo.id]);

               });
            } else if (typ === "gerrit") {
                return tx.none(`
                    INSERT INTO repository (name, private, project_id)
                    VALUES ($1, false, $2);
                `, [name, project_id]);
            }
        });
    })
    .then(() => {
        return OK(res, 'successfully added new project', { project_id: project_id });
    })
    .catch(handleDBError(next));
});
