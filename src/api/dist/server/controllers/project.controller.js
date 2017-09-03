"use strict";
const express_1 = require("express");
const db_1 = require("../db");
const status_1 = require("../utils/status");
const auth_1 = require("../utils/auth");
const config_1 = require("../config/config");
const validation_1 = require("../utils/validation");
const gcs_1 = require("../utils/gcs");
const badge = require('gh-badges');
const router = express_1.Router({ mergeParams: true });
module.exports = router;
router.get("/:project_id", validation_1.param_validation, auth_1.token_auth, auth_1.checkProjectAccess, (req, res, next) => {
    const project_id = req.params['project_id'];
    return db_1.db.any(`
        SELECT p.id, p.name, p.type
        FROM project p
        WHERE p.id = $1
    `, [project_id])
        .then((result) => {
        if (result.length !== 1) {
            throw new status_1.NotFound();
        }
        res.json(result[0]);
    }).catch(db_1.handleDBError(next));
});
router.get("/:project_id/build", validation_1.param_validation, auth_1.token_auth, auth_1.checkProjectAccess, (req, res, next) => {
    const project_id = req.params['project_id'];
    return db_1.db.any(`
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
        .then((result) => {
        res.json(result);
    }).catch(db_1.handleDBError(next));
});
router.get("/:project_id/build/:build_id/job", validation_1.param_validation, auth_1.token_auth, auth_1.checkProjectAccess, (req, res, next) => {
    const project_id = req.params['project_id'];
    const build_id = req.params['build_id'];
    return db_1.db.any(`
        SELECT j.name, j.start_date, j.end_date, j.cpu, j.memory, j.state, j.id
        FROM job j
        INNER JOIN build b
            ON j.build_id = b.id
            AND j.project_id = $1
            AND b.project_id = $1
            AND b.id = $2
    `, [project_id, build_id])
        .then((result) => {
        if (result.length === 0) {
            throw new status_1.NotFound();
        }
        res.json(result);
    }).catch(db_1.handleDBError(next));
});
router.get("/:project_id/job/:job_id/manifest", validation_1.param_validation, auth_1.token_auth, auth_1.checkProjectAccess, (req, res, next) => {
    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];
    let m = null;
    return db_1.db.any(`
        SELECT j.name, j.start_date, j.end_date, j.cpu, memory, j.state, j.id, b.build_number
        FROM job j
        JOIN build b
            ON b.id = j.build_id
            AND b.project_id = $1
        WHERE j.id = $2
        AND j.project_id = $1
    `, [project_id, job_id])
        .then((result) => {
        if (result.length !== 1) {
            throw new status_1.NotFound();
        }
        m = result[0];
        m.image = config_1.config.docker_registry.url + '/' + project_id + '/' + m.name + ':build_' + m.build_number;
        m.image = m.image.replace("https://", "");
        m.image = m.image.replace("http://", "");
        m.image = m.image.replace("//", "/");
        return db_1.db.any(`
             SELECT name, state, id FROM job
             WHERE id IN (SELECT unnest(dependencies) FROM job WHERE ID = $1)
        `, [job_id]);
    })
        .then((deps) => {
        for (const d of deps) {
            d.output = {
                url: config_1.config.api.url + '/v1/project/' + project_id + '/job/' + d.id + '/output',
                format: 'tar.gz'
            };
        }
        m.dependencies = deps;
        res.json(m);
    })
        .catch(db_1.handleDBError(next));
});
router.get("/:project_id/job/:job_id/output", validation_1.param_validation, auth_1.token_auth, auth_1.checkProjectAccess, (req, res, next) => {
    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];
    return db_1.db.any(`
        SELECT id FROM job WHERE id = $1 and project_id = $2
    `, [job_id, project_id])
        .then((result) => {
        if (result.length !== 1) {
            return next(new status_1.NotFound());
        }
        const file = job_id + '.tar.gz';
        return gcs_1.downloadOutput(file);
    }).then((stream) => {
        stream.pipe(res);
    }).catch(db_1.handleDBError(next));
});
router.get("/:project_id/build/state.svg", validation_1.param_validation, (req, res, next) => {
    const project_id = req.params['project_id'];
    db_1.db.any(`SELECT state FROM job j
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
        )`, [project_id]).then((rows) => {
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
                throw new status_1.InternalError(err);
            }
            else {
                res.set('Cache-Control', 'no-cache');
                res.send(svg);
            }
        });
    }).catch(db_1.handleDBError(next));
});
router.get("/:project_id/build/tests.svg", validation_1.param_validation, (req, res, next) => {
    const project_id = req.params['project_id'];
    db_1.db.any(`SELECT
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
        `, [project_id]).then((rows) => {
        const r = rows[0];
        const total = parseInt(r.success, 10) + parseInt(r.failure, 10) + parseInt(r.error, 10);
        const status = r.success + ' / ' + total;
        let color = "brightgreen";
        if (parseInt(r.success, 10) < total) {
            color = "red";
        }
        badge({ text: ["tests", status], colorscheme: color, template: "flat" }, (svg, err) => {
            if (err) {
                throw new status_1.InternalError(err);
            }
            else {
                res.set('Cache-Control', 'no-cache');
                res.send(svg);
            }
        });
    }).catch(db_1.handleDBError(next));
});
router.get("/:project_id/badge.svg", validation_1.param_validation, (req, res, next) => {
    const project_id = req.params['project_id'];
    const job_name = req.query['job_name'];
    const subject = req.query['subject'];
    db_1.db.any(`
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
        .then((rows) => {
        if (rows.length === 0) {
            throw new status_1.NotFound();
        }
        const r = rows[0];
        const color = r.color;
        const status = encodeURI(r.status);
        badge({ text: [subject, status], colorscheme: color, template: "flat" }, (svg, err) => {
            if (err) {
                throw new status_1.InternalError(err);
            }
            else {
                res.set('Cache-Control', 'no-cache');
                res.send(svg);
            }
        });
    }).catch(db_1.handleDBError(next));
});
