"use strict";
const crypto = require('crypto');
const bufferEq = require('buffer-equal-constant-time');
const Promise = require("bluebird");
const config_1 = require("../config/config");
const express_1 = require("express");
const db_1 = require("../db");
const status_1 = require("../utils/status");
const github_1 = require("../utils/github");
const router = express_1.Router();
module.exports = router;
class User {
}
class Commit {
}
class Repository {
}
class GithubUser {
}
class PushEvent {
}
class PullRequestBase {
}
class PullRequestHead {
}
class PullRequest {
}
class PullRequestEvent {
}
function createJob(c, repository, branch, tag) {
    let repo = null;
    let commit = null;
    let build = null;
    return db_1.db.tx((tx) => {
        return tx.any(`
            SELECT id, name, project_id FROM repository WHERE github_id = $1;
        `, [repository.id]).then((repos) => {
            if (repos.length !== 1) {
                throw new status_1.BadRequest('Unknown repository');
            }
            repo = repos[0];
            return tx.any(`
                SELECT * FROM "commit" WHERE id = $1 AND project_id = $2;
                `, [c.id, repo.project_id]);
        }).then((commits) => {
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
            const stmt = db_1.pgp.helpers.insert(files, ['project_id', 'commit_id', 'modification', 'filename'], 'commit_file');
            return tx.any(stmt);
        });
    });
}
function getOwnerToken(repo_id) {
    // Get the owner token to set the status
    return db_1.db.one(`SELECT github_api_token FROM "user" u
        INNER JOIN collaborator co
            ON co.user_id = u.id
            AND co.owner = true
        INNER JOIN project p
            ON co.project_id = p.id
        INNER JOIN repository r
            ON r.github_id = $1
            AND r.project_id = p.id
        `, [repo_id]);
}
function handlePush(event, res, next) {
    let branch = null;
    let tag = null;
    let commits;
    if (event.base_ref) {
        branch = event.base_ref.split("/").pop();
    }
    if (event.ref.startsWith("refs/tags")) {
        tag = event.ref.split("/").pop();
        commits = [event.head_commit];
    }
    else {
        branch = event.ref.split("/").pop();
        commits = event.commits;
    }
    getOwnerToken(event.repository.id)
        .then((result) => {
        const token = result.github_api_token;
        if (token) {
            return Promise.map(commits, (c) => {
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
                    return github_1.setStatus(token, url, 'pending');
                }
            }).catch(() => {
                // failed to set status, but we ignore it
            });
        }
    }).then(() => {
        return Promise.mapSeries(commits, (c) => {
            if (c.distinct) {
                return createJob(c, event.repository, branch, tag);
            }
        });
    }).then(() => {
        return status_1.OK(res, "successfully handled push event");
    }).catch(db_1.handleDBError(next));
}
function handlePullRequest_open(pr) {
    let repo = null;
    let build = null;
    let commit = null;
    let hc = null;
    let pr_id = null;
    return db_1.db.tx((tx) => {
        return tx.any(`
                SELECT id, name, project_id FROM repository WHERE github_id = $1;
            `, [pr.repository.id]).then((repos) => {
            if (repos.length !== 1) {
                throw new status_1.BadRequest('Unknown repository');
            }
            repo = repos[0];
            return getOwnerToken(pr.repository.id);
        }).then((result) => {
            const token = result.github_api_token;
            const commits_url = pr.pull_request.commits_url;
            return github_1.getCommits(token, commits_url);
        }).then((commits) => {
            for (const c of commits) {
                if (c.sha === pr.pull_request.head.sha) {
                    hc = c;
                }
            }
            if (!hc) {
                throw new status_1.BadRequest("Commit not found");
            }
            return tx.any(`
                SELECT id FROM pull_request WHERE project_id = $1 and github_pull_request_id = $2;
            `, [repo.id, pr.pull_request.id]);
        }).then((result) => {
            if (result.length === 0) {
                return tx.none(`INSERT INTO pull_request (project_id, github_pull_request_id, title) VALUES ($1, $2, $3) RETURNING ID`, [repo.project_id, pr.pull_request.id, pr.pull_request.title]);
            }
        }).then((r) => {
            pr_id = r.id;
            return tx.any(`
                SELECT * FROM "commit" WHERE id = $1 AND project_id = $2;
                `, [hc.sha, repo.project_id]);
        }).then((commits) => {
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
        }).then((co) => {
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
function handlePullRequest(pr, res, next) {
    if (pr.action === "opened" || pr.action === "synchronize") {
        handlePullRequest_open(pr)
            .then(() => {
            return getOwnerToken(pr.repository.id);
        }).then((result) => {
            const token = result.github_api_token;
            return github_1.setStatus(token, pr.pull_request.statuses_url, 'pending');
        }).then(() => {
            return status_1.OK(res, "successfully handled pull_request event");
        }).catch(db_1.handleDBError(next));
    }
    else {
        return status_1.OK(res, "successfully handled pull_request event");
    }
}
function signBlob(key, blob) {
    const s = 'sha1=' + crypto.createHmac('sha1', key).update(blob).digest('hex');
    return s;
}
router.post("/", (req, res, next) => {
    // validate request
    const event = req.headers['x-github-event'];
    if (!event) {
        return next(new status_1.BadRequest("No x-github-event found"));
    }
    if (event === "ping") {
        return status_1.OK(res, "pong");
    }
    const sig = req.headers['x-hub-signature'];
    if (!sig) {
        return next(new status_1.BadRequest("No x-hub-signature found"));
    }
    const computedSig = new Buffer(signBlob(config_1.config.github.webhook_secret, JSON.stringify(req['body'])));
    if (!process.env.INFRABOX_TEST) {
        if (!bufferEq(new Buffer(sig), computedSig)) {
            return next(new status_1.BadRequest('X-Hub-Signature does not match blob signature'));
        }
    }
    if (event === "push") {
        const body = req['body'];
        handlePush(body, res, next);
    }
    else if (event === "pull_request") {
        const body = req['body'];
        handlePullRequest(body, res, next);
    }
    else {
        return status_1.OK(res, "event received");
    }
});
