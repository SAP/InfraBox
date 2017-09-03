"use strict";

const crypto = require('crypto');
const bufferEq = require('buffer-equal-constant-time');

import Promise = require("bluebird");
import { config } from "../config/config";
import { Request, Response, Router } from "express";
import { db, pgp, handleDBError } from "../db";
import { OK, BadRequest } from "../utils/status";
import { logger } from "../utils/logger";
import { setStatus, getCommits } from "../utils/github";

const router = Router();

module.exports = router;

class User {
    public name: string;
    public email: string;
    public username: string;
}

class Commit {
    public id: string;
    public tree_id: string;
    public distinct: boolean;
    public message: string;
    public timestamp: string;
    public url: string;
    public author: User;
    public committer: User;
    public added: string[];
    public removed: string[];
    public modified: string[];
}

class Repository {
    public id: number;
    public name: string;
    public full_name: string;
    public owner: User;
    public private: boolean;
    public html_url: string;
    public fork: boolean;
    public url: string;
    public create_at: number;
    public update_at: string;
    public pushed_at: number;
    public clone_url: string;
    public default_branch: string;
    public master_branch: string;
}

class GithubUser {
    public login: string;
    public id: number;
    public avatar_url: string;
    public gravatar_url: string;
    public url: string;
    public html_url: string;
    public type: string;
}

class PushEvent {
    public ref: string;
    public before: string;
    public after: string;
    public created: boolean;
    public deleted: boolean;
    public forced: boolean;
    public base_ref: string;
    public compare: string;
    public commits: Commit[];
    public head_commit: Commit;
    public repository: Repository;
    public puser: User;
    public sender: GithubUser;
}

class PullRequestBase {
    public sha: string;
    public repo: Repository;
}

class PullRequestHead {
    public label: string;
    public ref: string;
    public sha: string;
    public user: GithubUser;
    public repo: Repository;
}

class PullRequest {
    public url: string;
    public id: number;
    public title: string;
    public user: GithubUser;
    public base: PullRequestBase;
    public head: PullRequestHead;
    public statuses_url: string;
    public commits_url: string;
    public html_url: string;
}

class PullRequestEvent {
    public action: string;
    public number: number;
    public pull_request: PullRequest;
    public repository: Repository;
}

function createJob(c: Commit, repository: Repository, branch: string, tag: string) {
    let repo = null;
    let commit = null;
    let build = null;
    return db.tx((tx) => {
        return tx.any(`
            SELECT id, name, project_id FROM repository WHERE github_id = $1;
        `, [repository.id]
        ).then((repos: any[]) => {
            if (repos.length !== 1) {
                throw new BadRequest('Unknown repository');
            }

            repo = repos[0];
            return tx.any(`
                SELECT * FROM "commit" WHERE id = $1 AND project_id = $2;
                `, [c.id, repo.project_id]);
        }).then((commits: any[]) => {
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
                RETURNING *
            `, [c.id, c.message, repo.id, new Date(c.timestamp), c.author.name,
                c.author.email, c.author.username, c.committer.name, c.committer.email,
                c.committer.username, c.url, branch, repo.project_id, tag]);
        }).then((co) => {
            commit = co;

            if (tag) {
                return tx.any(`
                    UPDATE "commit" SET tag = $1 WHERE id = $2 AND project_id = $3
                `, [tag, c.id, repo.project_id]);
            }
        }).then(() => {
            return tx.one(`SELECT count(distinct build_number) + 1 AS build_no
                          FROM build AS b
                          WHERE b.project_id = $1`, [repo.project_id]);
        }).then((r) => {
            const build_no = r.build_no;
            return tx.one(`
                INSERT INTO build (commit_id, build_number, project_id)
                VALUES ($1, $2, $3)
                RETURNING *
            `, [commit.id, build_no, repo.project_id]);
        }).then((b) => {
            build = b;
            const git_repo = {
                commit: c.id,
                clone_url: repository.clone_url
            };

            return tx.none(`
            INSERT INTO job (id, state, build_id, type, name, project_id, build_only, dockerfile, cpu, memory, repo)
            VALUES (gen_random_uuid(), 'queued', $1, 'create_job_matrix', 'Create Jobs', $2, false, '', 1, 1024, $3)
            `, [build.id, repo.project_id, git_repo]);
        })
        .then(() => {
            // Insert modified files
            const files = [];
            for (const m of c.modified) {
                files.push({ project_id: repo.project_id, commit_id: c.id, modification: 'modified', filename: m });
            }

            for (const a of c.added) {
                files.push({ project_id: repo.project_id, commit_id: c.id, modification: 'added', filename: a });
            }

            for (const r of c.removed) {
                files.push({ project_id: repo.project_id, commit_id: c.id, modification: 'removed', filename: r });
            }

            const stmt = pgp.helpers.insert(files, ['project_id', 'commit_id', 'modification', 'filename'], 'commit_file');

            return tx.any(stmt);
        });
    });
}

function getOwnerToken(repo_id: number) {
    // Get the owner token to set the status
    return db.one(`SELECT github_api_token FROM "user" u
        INNER JOIN collaborator co
            ON co.user_id = u.id
            AND co.owner = true
        INNER JOIN project p
            ON co.project_id = p.id
        INNER JOIN repository r
            ON r.github_id = $1
            AND r.project_id = p.id
        `, [repo_id]
    );
}

function handlePush(event: PushEvent, res: Response, next) {
    let branch = null;
    let tag = null;
    let commits: Commit[];

    if (event.base_ref) {
        branch = event.base_ref.split("/").pop();
    }

    if (event.ref.startsWith("refs/tags")) {
        tag = event.ref.split("/").pop();
        commits = [event.head_commit];
    } else {
        branch = event.ref.split("/").pop();
        commits = event.commits;
    }

    getOwnerToken(event.repository.id)
    .then((result) => {
        const token = result.github_api_token;

        if (token) {
            return Promise.map(commits, (c: Commit) => {
                if (c.distinct) {
                    const owner = event.repository.owner.name;
                    const repo = event.repository.name;
                    const sha = c.id;
                    const url = 'https://api.github.com/repos/'
                                + owner
                                + '/'
                                + repo
                                + '/statuses/'
                                + sha;
                    return setStatus(token, url, 'pending');
                }
            }).catch(() => {
                // failed to set status, but we ignore it
            });
        }
    }).then(() => {
        return Promise.mapSeries(commits, (c: Commit) => {
            if (c.distinct) {
                return createJob(c, event.repository, branch, tag);
            }
        });
    }).then(() => {
        return OK(res, "successfully handled push event");
    }).catch(handleDBError(next));
}

function handlePullRequest_open(pr: PullRequestEvent) {
    let repo = null;
    let build = null;
    let commit = null;
    let hc = null;
    let pr_id = null;

    return db.tx((tx) => {
        return tx.any(`
                SELECT id, name, project_id FROM repository WHERE github_id = $1;
            `, [pr.repository.id]
        ).then((repos: any[]) => {
            if (repos.length !== 1) {
                throw new BadRequest('Unknown repository');
            }

            repo = repos[0];
            return getOwnerToken(pr.repository.id);
        }).then((result: any) => {
            const token = result.github_api_token;
            const commits_url = pr.pull_request.commits_url;
            return getCommits(token, commits_url);
        }).then((commits: any[]) => {
            for (const c of commits) {
                if (c.sha === pr.pull_request.head.sha) {
                    hc = c;
                }
            }

            if (!hc) {
                throw new BadRequest("Commit not found");
            }

            return tx.any(`
                SELECT id FROM pull_request WHERE project_id = $1 and github_pull_request_id = $2;
            `, [repo.id, pr.pull_request.id]);
        }).then((result: any[]) => {
            if (result.length === 0) {
                return tx.one(`INSERT INTO pull_request (project_id, github_pull_request_id, title, url) VALUES ($1, $2, $3, $4) RETURNING ID`,
                               [repo.project_id, pr.pull_request.id, pr.pull_request.title, pr.pull_request.html_url]);
            }
        }).then((r: any) => {
            pr_id = r.id;

            return tx.any(`
                SELECT * FROM "commit" WHERE id = $1 AND project_id = $2;
                `, [hc.sha, repo.project_id]);
        }).then((commits: any[]) => {
            if (commits.length !== 0) {
                return commits[0];
            }

            return tx.one(`
                INSERT INTO "commit" (
                    id, message, repository_id, timestamp,
                    author_name, author_email, author_username,
                    committer_name, committer_email, committer_username, url, project_id, branch, pull_request_id)
                VALUES ($1, $2, $3,
                    $4, $5, $6,
                    $7, $8, $9,
                    $10, $11, $12, 'pull_request', $13)
                RETURNING *
            `, [hc.sha, hc.commit.message, repo.id, new Date(hc.commit.author.date), hc.commit.author.name,
                hc.commit.author.email, hc.author.login, hc.commit.committer.name, hc.commit.committer.email,
                hc.committer.login, hc.commit.url, repo.project_id, pr_id]);
        }).then((co: any) => {
            commit = co;
            return tx.one('SELECT count(distinct build_number) + 1 AS build_no FROM build AS b WHERE b.project_id = $1', [repo.project_id]);
        }).then((r) => {
            const build_no = r.build_no;
            return tx.one(`
                INSERT INTO build (commit_id, build_number, project_id)
                VALUES ($1, $2, $3)
                RETURNING *
            `, [commit.id, build_no, repo.project_id]);
        }).then((b) => {
            build = b;

            const pr_repo = {
                clone_url: pr.pull_request.head.repo.clone_url,
                commit: pr.pull_request.head.sha
            };

            return tx.none(`
            INSERT INTO job (id, state, build_id, type, name, project_id, build_only, dockerfile, cpu, memory, repo)
            VALUES (gen_random_uuid(), 'queued', $1, 'create_job_matrix', 'Create Jobs', $2, false, '', 1, 1024, $3)
            `, [build.id, repo.project_id, pr_repo]);
        });
    });
}

function handlePullRequest(pr: PullRequestEvent, res: Response, next) {
    if (pr.action === "opened" || pr.action === "synchronize") {
        handlePullRequest_open(pr)
        .then(() => {
            return getOwnerToken(pr.repository.id);
        }).then((result: any) => {
            const token = result.github_api_token;
            return setStatus(token, pr.pull_request.statuses_url, 'pending');
        }).then(() => {
            return OK(res, "successfully handled pull_request event");
        }).catch(handleDBError(next));
    } else {
        return OK(res, "successfully handled pull_request event");
    }
}

function signBlob(key, blob) {
    const s = 'sha1=' + crypto.createHmac('sha1', key).update(blob).digest('hex');
    return s;
}

router.post("/", (req: Request, res: Response, next) => {
    // validate request
    const event: String = req.headers['x-github-event'];

    if (!event) {
        return next(new BadRequest("No x-github-event found"));
    }

    if (event === "ping") {
        return OK(res, "pong");
    }

    const sig = req.headers['x-hub-signature'];

    if (!sig) {
        return next(new BadRequest("No x-hub-signature found"));
    }

    const computedSig = new Buffer(signBlob(config.github.webhook_secret, JSON.stringify(req['body'])));

    if (!process.env.INFRABOX_TEST) {
        if (!bufferEq(new Buffer(sig), computedSig)) {
            return next(new BadRequest('X-Hub-Signature does not match blob signature'));
        }
    }

    if (event === "push") {
        const body = req['body'] as PushEvent;
        handlePush(body, res, next);
    } else if (event === "pull_request") {
        const body = req['body'] as PullRequestEvent;
        handlePullRequest(body, res, next);
    } else {
        return OK(res, "event received");
    }
});
