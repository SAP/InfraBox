import { Router, Request, Response } from "express";
import { db, handleDBError } from "../db";
import { NotFound, InternalError } from "../utils/status";
import { token_auth, checkProjectAccess } from "../utils/auth";
import { config } from "../config/config";
import { param_validation as pv } from "../utils/validation";
import { downloadOutput } from "../utils/gcs";

const badge = require('gh-badges');

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/:project_id", pv, token_auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];

    return db.any(`
        SELECT row_to_json(r) as project
        FROM (
            SELECT name, id, type, public, build_on_push, builds.builds
            FROM (
                select name, id, type, public, build_on_push
                from project
                where id = $1
            ) p LEFT JOIN LATERAL (
                SELECT array_to_json(array_agg(row_to_json(b))) as builds
                FROM (
                    SELECT id, restart_counter, build_number, jobs.jobs FROM build
                    LEFT JOIN LATERAL (
                        SELECT array_to_json(array_agg(row_to_json(jobs))) jobs
                        FROM (
                            SELECT id, state, start_date, end_date, name, build_only, keep, cpu, memory
                            FROM job
                            WHERE project_id = $1
                            AND build_id = build.id
                        ) jobs
                    ) jobs on true
                    WHERE build.project_id = $1
                ) as b
            ) builds on true
        ) r `, [project_id])
    .then((project: any) => {
        res.json(project[0]);
    }).catch(handleDBError(next));
});

router.get("/:project_id/build/:build_id/job", pv, token_auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const build_id = req.params['build_id'];

    return db.any(`
        SELECT j.name, j.start_date, j.end_date, j.cpu, j.memory, j.state, j.id
        FROM job j
        INNER JOIN build b
            ON j.build_id = b.id
            AND j.project_id = $1
            AND b.project_id = $1
            AND b.id = $2
    `, [project_id, build_id])
    .then((result: any[]) => {
        if (result.length === 0) {
            throw new NotFound();
        }

        res.json(result);
    }).catch(handleDBError(next));
});

router.get("/:project_id/job/:job_id/manifest", pv, token_auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];

    let m = null;

    return db.any(`
        SELECT j.name, j.start_date, j.end_date, j.cpu, memory, j.state, j.id, b.build_number
        FROM job j
        JOIN build b
            ON b.id = j.build_id
            AND b.project_id = $1
        WHERE j.id = $2
        AND j.project_id = $1
    `, [project_id, job_id])
    .then((result: any[]) => {
        if (result.length !== 1) {
            throw new NotFound();
        }

        m = result[0];
        m.image = config.docker_registry.url + '/' + project_id + '/' + m.name + ':build_' + m.build_number;
        m.image = m.image.replace("https://", "");
        m.image = m.image.replace("http://", "");
        m.image = m.image.replace("//", "/");

        m.output = {
            url: config.api.url + '/v1/project/' + project_id + '/job/' + job_id + '/output',
            format: 'tar.gz'
        };

        return db.any(`
             SELECT name, state, id FROM job
             WHERE id IN (SELECT (p->>'job-id')::uuid
                          FROM job, jsonb_array_elements(job.dependencies) as p
                          WHERE job.id = $1)
        `, [job_id]);
    })
    .then((deps: any[]) => {
        for (const d of deps) {
            d.output = {
                url: config.api.url + '/v1/project/' + project_id + '/job/' + d.id + '/output',
                format: 'tar.gz'
            };
        }

        m.dependencies = deps;
        res.json(m);
    })
    .catch(handleDBError(next));
});

router.get("/:project_id/job/:job_id/output", pv, token_auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];

    return db.any(`
        SELECT id, download FROM job WHERE id = $1 and project_id = $2
    `, [job_id, project_id])
    .then((result: any[]) => {
        if (result.length !== 1) {
            throw new NotFound();
        }

        if (!result[0].download) {
            throw new NotFound();
        }

        const file = result[0].download.Output[0].id;
        return downloadOutput(file);
    }).then((stream: any) => {
        if (!stream) {
            throw new NotFound();
        } else {
            stream.pipe(res);
        }
    }).catch(handleDBError(next));
});

router.get("/:project_id/build/state.svg", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    return db.any(`
        SELECT type FROM project WHERE id = $1
    `, [project_id])
    .then((result: any[]) => {
        if (result.length !== 1) {
            throw new NotFound();
        }

        const t = result[0].type

        if (req.query.branch && (t === 'github' || t === 'gerrit')) {
            return db.any(`
               SELECT state FROM job j
                WHERE j.project_id = $1
                    AND j.build_id = (
                        SELECT b.id
                        FROM build b
                        INNER JOIN job j
                        ON b.id = j.build_id
                            AND b.project_id = $1
                            AND j.project_id = $1
                        INNER JOIN "commit" c
                        ON c.id = b.commit_id
                            AND c.project_id = $1
                            AND c.branch = $2
                        ORDER BY j.created_at DESC
                        LIMIT 1
                )`, [project_id, req.query.branch]);
        } else {
            return db.any(`
                SELECT state FROM job j
                WHERE j.project_id = $1
                    AND j.build_id = (
                        SELECT b.id
                        FROM build b
                        INNER JOIN job j
                        ON b.id = j.build_id
                            AND b.project_id = $1
                            AND j.project_id = $1
                        ORDER BY j.created_at DESC
                        LIMIT 1
                )`, [project_id]);
        }
    }).then((rows: any[]) => {
        let status = 'finished';
        let color = 'brightgreen';

        for (const r of rows) {
            const state = r.state;
            if (state === 'finished') {
                continue;
            }

            if (state === 'failure' || state === 'error' || state === 'killed') {
                status = state;
                color = 'red';
                break;
            }

            if (state === 'skipped') {
                continue;
            }

            if (state !== 'failure') {
                status = 'running';
                color = 'grey';
                break;
            }
        }

        badge({ text: ["build", status], colorscheme: color, template: "flat" }, (svg, err) => {
            if (err) {
                throw new InternalError(err);
            } else {
                res.setHeader('Surrogate-Control', 'no-store');
                res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
                res.setHeader('Pragma', 'no-cache');
                res.setHeader('Expires', '0');
                res.setHeader('Content-Type', 'image/svg+xml');
                res.send(svg);
            }
        });
    }).catch(handleDBError(next));
});

router.get("/:project_id/build/tests.svg", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];

    db.any(`SELECT
                count(CASE WHEN tr.state = 'ok' THEN 1 END) success,
                count(CASE WHEN tr.state = 'failure' THEN 1 END) failure,
                count(CASE WHEN tr.state = 'error' THEN 1 END) error,
                count(CASE WHEN tr.state = 'skipped' THEN 1 END) skipped
            FROM test_run tr
            WHERE  tr.project_id = $1
                AND tr.job_id IN (
                    SELECT j.id
                    FROM job j
                    WHERE j.project_id = $1
                        AND j.build_id = (
                            SELECT b.id
                            FROM build b
                            INNER JOIN job j
                            ON b.id = j.build_id
                                AND b.project_id = $1
                                AND j.project_id = $1
                            ORDER BY j.created_at DESC
                            LIMIT 1
                        )
                )
        `, [project_id]).then((rows: any[]) => {

            const r = rows[0];
            const total = parseInt(r.success, 10) + parseInt(r.failure, 10) + parseInt(r.error, 10);
            const status = r.success + ' / ' + total;

            let color = "brightgreen";

            if (parseInt(r.success, 10) < total) {
                color = "red";
            }

            badge({ text: ["tests", status], colorscheme: color, template: "flat" }, (svg, err) => {
                if (err) {
                    throw new InternalError(err);
                } else {
                    res.setHeader('Surrogate-Control', 'no-store');
                    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
                    res.setHeader('Pragma', 'no-cache');
                    res.setHeader('Expires', '0');
                    res.setHeader('Content-Type', 'image/svg+xml');
                    res.send(svg);
                }
            });
        }).catch(handleDBError(next));
});

router.get("/:project_id/badge.svg", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const job_name = req.query['job_name'];
    const subject = req.query['subject'];

    db.any(`
       SELECT status, color
       FROM job_badge jb
       JOIN job j
            ON j.id = jb.job_id
            AND j.project_id = $1
            AND j.state = 'finished'
            AND j.name = $2
            AND jb.subject = $3
       JOIN build b
            ON j.build_id = b.id
            AND b.project_id = $1
       ORDER BY j.end_date desc
       LIMIT 1
       `, [project_id, job_name, subject])
    .then((rows: any[]) => {
        if (rows.length === 0) {
            throw new NotFound();
        }

        const r = rows[0];
        const color = r.color;
        const status = r.status;

        badge({ text: [subject, status], colorscheme: color, template: "flat" }, (svg, err) => {
            if (err) {
                throw new InternalError(err);
            } else {
                res.setHeader('Surrogate-Control', 'no-store');
                res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
                res.setHeader('Pragma', 'no-cache');
                res.setHeader('Expires', '0');
                res.setHeader('Content-Type', 'image/svg+xml');
                res.send(svg);
            }
        });

    }).catch(handleDBError(next));
});
