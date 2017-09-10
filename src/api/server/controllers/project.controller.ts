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
        SELECT p.id, p.name, p.type
        FROM project p
        WHERE p.id = $1
    `, [project_id])
    .then((result: any[]) => {
        if (result.length !== 1) {
            throw new NotFound();
        }

        res.json(result[0]);
    }).catch(handleDBError(next));
});

router.get("/:project_id/build", pv, token_auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];

    return db.any(`
        SELECT i.id, i.number, i.restart_counter,
            count(*)::int num_jobs,
            count(CASE WHEN j.state = 'queued' OR j.state = 'scheduled' OR j.state = 'running' THEN 1 END)::int num_active,
            count(CASE WHEN j.state = 'failure' THEN 1 END)::int num_failure,
            count(CASE WHEN j.state = 'error' THEN 1 END)::int num_error,
            count(CASE WHEN j.state = 'skipped' THEN 1 END)::int num_skipped,
            count(CASE WHEN j.state = 'finished' THEN 1 END)::int num_finished
        FROM (
            SELECT b.id, b.build_number as number, b.restart_counter
            FROM build b
            WHERE b.project_id = $1
            ORDER BY b.build_number DESC
            LIMIT 10
        ) i
        INNER JOIN job j
            ON j.build_id = i.id
            AND j.project_id = $1
        GROUP BY i.id, i.number, i.restart_counter
        ORDER BY i.number, i.restart_counter
    `, [project_id])
    .then((result: any[]) => {
        res.json(result);
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
             WHERE id IN (SELECT (p->>'job-id')::uuid FROM job, jsonb_elements_array(job.dependencies) WHERE job.id = $1)
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

    db.any(`SELECT state FROM job j
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
        )`, [project_id]).then((rows: any[]) => {
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
                    res.set('Cache-Control', 'no-cache');
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
                    res.set('Cache-Control', 'no-cache');
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
        const status = encodeURI(r.status);

        badge({ text: [subject, status], colorscheme: color, template: "flat" }, (svg, err) => {
            if (err) {
                throw new InternalError(err);
            } else {
                res.set('Cache-Control', 'no-cache');
                res.send(svg);
            }
        });

    }).catch(handleDBError(next));
});
