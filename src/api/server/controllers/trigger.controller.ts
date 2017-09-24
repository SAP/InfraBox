import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../db";
import { BadRequest, OK, InternalError } from "../utils/status";
import { param_validation as pv } from "../utils/validation";
import { Validator } from 'jsonschema';
import * as request from 'request-promise';

const router = Router({ mergeParams: true });
module.exports = router;

const TriggerSchema = {
    id: "/TriggerSchema",
    type: "object",
    properties: {
        branch: { type: "string" },
        sha: { type: "string" },
    }
};

function insertCommit(tx, project_id: string, repo_id: string, branch: string, commit: any) {
    return tx.any(`
            SELECT * FROM "commit" WHERE id = $1 AND project_id = $2;
            `, [commit.sha, project_id]
    ).then((commits: any[]) => {
        if (commits.length !== 0) {
            return commits[0];
        }

        return tx.one(`
            INSERT INTO "commit" (
                id, message, repository_id, timestamp,
                author_name, author_email, author_username,
                committer_name, committer_email, committer_username, url, branch, project_id, tag)
            VALUES ($1, $2, $3,
                $4, $5, $6,
                $7, $8, $9,
                $10, $11, $12, $13, $14)
        `, [commit.sha, commit.message, repo_id, new Date(), commit.author.name,
            commit.author.email, '', '', '',
            '', commit.url, branch, project_id, null]);
    }).then(() => {
        return commit;
    });
}

function createGerritCommit(tx, project_id: string, repo_id: string, sha: string, branch: string) {
    return tx.one('SELECT github_owner, name FROM repository WHERE project_id = $1', [project_id])
    .then((project: any) => {
        const options = {
            method: 'POST',
            uri: 'http://localhost:8082/api/v1/commit',
            form: {
                sha: sha,
                branch: branch,
                project: project.name
            },
            json: true
        }

        return request(options).catch((e) => {
            throw new InternalError(e.error.message);
        });
    }).then((commit) => {
        return insertCommit(tx, project_id, repo_id, branch, commit);
    });
}

function createGithubCommit(tx, project_id: string, repo_id: string, sha: string, branch: string) {
    let project = null;

    return tx.one('SELECT github_owner, name FROM repository WHERE project_id = $1', [project_id])
    .then((p: any) => {
        project = p;
        return tx.one(`
            SELECT github_api_token FROM "user" u
            INNER JOIN collaborator co
                ON co.user_id = u.id
                AND co.owner = true
            INNER JOIN project p
                ON co.project_id = p.id
            INNER JOIN repository r
                ON r.id = $1
                AND r.project_id = p.id
        `, [repo_id]);
    }).then((user: any) => {
        const options = {
            method: 'POST',
            uri: 'http://localhost:8081/api/v1/commit',
            form: {
                sha: sha,
                branch: branch,
                owner: project.github_owner,
                repo: project.name,
                token: user.github_api_token
            },
            json: true
        }

        return request(options).catch((e) => {
            throw new InternalError(e.error.message);
        });
    }).then((commit) => {
        return insertCommit(tx, project_id, repo_id, branch, commit);
    });
}

function createCommit(tx, project_id: string, repo_id: string, sha: string, branch: string) {
    return tx.one('SELECT type FROM project WHERE id = $1', [project_id])
    .then((project: any) => {
        if (project.type === 'github') {
            return createGithubCommit(tx, project_id, repo_id, sha, branch);
        } else if (project.type === 'gerrit') {
            return createGerritCommit(tx, project_id, repo_id, sha, branch);
        } else {
            throw new BadRequest("unknown project type");
        }
    });
}

function createJob(branch: string, sha: string, project_id: string) {
    let repo = null;
    let commit = null;
    let build = null;

    return db.tx((tx) => {
        return tx.any(`
            SELECT id, name, clone_url FROM repository WHERE project_id = $1;
        `, [project_id]
        ).then((repos: any[]) => {
            if (repos.length !== 1) {
                throw new BadRequest('Unknown repository');
            }
            repo = repos[0];

            return createCommit(tx, project_id, repo.id, sha, branch);
        }).then((co) => {
            commit = co;
            console.log(co);

            return tx.one(`SELECT count(distinct build_number) + 1 AS build_no
                          FROM build AS b
                          WHERE b.project_id = $1`, [project_id]);
        }).then((r) => {
            const build_no = r.build_no;
            return tx.one(`
                INSERT INTO build (commit_id, build_number, project_id)
                VALUES ($1, $2, $3)
                RETURNING *
            `, [commit.sha, build_no, project_id]);
        }).then((b) => {
            build = b;
            const git_repo = {
                commit: commit.sha,
                clone_url: repo.clone_url
            };

            if (commit.clone_url) {
                git_repo.clone_url = commit.clone_url;
            }

            return tx.none(`
            INSERT INTO job (id, state, build_id, type, name, project_id, build_only, dockerfile, cpu, memory, repo)
            VALUES (gen_random_uuid(), 'queued', $1, 'create_job_matrix', 'Create Jobs', $2, false, '', 1, 1024, $3)
            `, [build.id, project_id, git_repo]);
        });
    });
}

router.post("/:project_id/trigger", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];

    const v = new Validator();
    const envResult = v.validate(req['body'], TriggerSchema);

    if (envResult.errors.length > 0) {
        return next(new BadRequest("Invalid values"));
    }

    let branch = req['body']['branch'];
    let sha = req['body']['sha'];

    // TODO(ib-steffen): disable push event
    // TODO(ib-steffen): Check scope
    // TODO(ib-steffen): check project allows trigger
    createJob(branch, sha, project_id)
    .then(() => {
        return OK(res, "Successfully triggered build");
    }).catch(handleDBError(next));
});


