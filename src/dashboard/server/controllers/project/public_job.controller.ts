import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { param_validation as pv } from "../../utils/validation";
import { NotFound, BadRequest } from "../../utils/status";
import { downloadOutput } from "../../utils/gcs";

const router = Router({ mergeParams: true});
module.exports = router;

router.get("/:job_id/testruns", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];

    db.any(`SELECT tr.state, t.name, t.suite, tr.duration, t.build_number, tr.message, tr.stack
            FROM test t
            INNER JOIN test_run tr
                ON t.id = tr.test_id
                AND t.project_id = $2
                AND tr.project_id = $2
                AND tr.job_id = $1
        `, [job_id, project_id])
        .then((repos: any[]) => {
            res.json(repos);
        }).catch(handleDBError(next));
});

router.get("/:job_id/tabs", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];

    db.any(`SELECT name, data, type FROM job_markup WHERE job_id = $1 and project_id = $2`,
           [job_id, project_id])
        .then((repos: any[]) => {
            res.json(repos);
        }).catch(handleDBError(next));
});

router.get("/:job_id/console", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];

    db.any(`SELECT console FROM job WHERE id = $1 and project_id = $2`,
           [job_id, project_id])
        .then((result: any[]) => {
            if (result.length != 1) {
                throw new NotFound();
            }

			const d = result[0].console;

			if (!d) {
                throw new NotFound();
			}

            res.set({"Content-Disposition":`attachment; filename="${job_id}-console-output.txt"`});
            res.send(d);
        }).catch(handleDBError(next));
});

router.get("/:job_id/output", pv, (req: Request, res: Response, next) => {
    const job_id = req.params['job_id'];
    const file_id = job_id + '.tar.gz'
    downloadOutput(file_id)
    .then((stream: any) => {
        if (!stream) {
            throw new NotFound();
        } else {
            res.set({"Content-Disposition": `attachment; filename="${file_id}"`});
            stream.pipe(res);
        }
    }).catch(handleDBError(next));
});

router.get("/:job_id/badges", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];

    db.any(`SELECT subject, status, color FROM job_badge WHERE job_id = $1 and project_id = $2`,
           [job_id, project_id])
        .then((repos: any[]) => {
            res.json(repos);
        }).catch(handleDBError(next));
});

router.get("/:job_id/stats", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];

    db.any(`SELECT stats FROM job WHERE id = $1 and project_id = $2`,
           [job_id, project_id])
        .then((stats: any[]) => {
            if (stats.length === 0) {
                throw new NotFound();
            }

            const s = stats[0].stats;
            if (!s) {
                return res.json({});
            } else {
                res.json(JSON.parse(s));
            }
        }).catch(handleDBError(next));
});

router.get("/:job_id/env", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];

    db.any(`SELECT env_var, env_var_ref FROM job WHERE id = $1 and project_id = $2`,
           [job_id, project_id])
        .then((result: any[]) => {
            if (result.length === 0) {
                throw new NotFound();
            }

            const env = [];
            const r = result[0];
            if (r.env_var) {
                for (const name in r.env_var) {
                    if (!r.env_var.hasOwnProperty(name)) {
                        continue;
                    }

                    env.push({
                        name: name,
                        value: r.env_var[name],
                        ref: false
                    });
                }
            }

            if (r.env_var_ref) {
                for (const name in r.env_var_ref) {
                    if (!r.env_var_ref.hasOwnProperty(name)) {
                        continue;
                    }

                    env.push({
                        name: name,
                        value: "<PRIVATE>",
                        ref: true
                    });
                }
            }

            return res.json(env);
        }).catch(handleDBError(next));
});

router.get("/:job_id/stats/history", pv,
    (req: Request, res: Response, next) => {

    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];

    db.any(`
        SELECT b.build_number, js.job_id, js.tests_added, js.tests_duration, js.tests_failed, js.tests_passed, js.tests_skipped, js.tests_error
        FROM job_stat js
        INNER JOIN job j
        ON j.id = js.job_id
            AND j.name = (SELECT name FROM job WHERE id = $1)
            AND j.project_id = $2
        INNER JOIN build b
        ON b.id = j.build_id
            AND b.build_number <= (SELECT build_number FROM build JOIN job ON job.build_id = build.id AND job.id = $1)
            AND b.project_id = $2
        ORDER BY b.build_number, b.restart_counter
        LIMIT 30`,
        [job_id, project_id])
    .then((repos: any[]) => {
        res.json(repos);
    })
    .catch(handleDBError(next));
});

router.get("/:job_id/test/history", pv, (req, res: Response, next) => {
    req.checkQuery('test', 'invalid test').notEmpty();
    req.checkQuery('suite', 'invalid suite').notEmpty();

    if (req.validationErrors()) {
        return next(new BadRequest("Invalid values"));
    }

    const project_id = req.params['project_id'];
    const job_id = req.params['job_id'];
    const user_id = req['user'].id;
    const test = req.query['test'];
    const suite = req.query['suite'];

    db.any(`
        SELECT
            b.build_number,
            tr.duration duration,
            tr.state state,
            m.name measurement_name,
            m.value measurement_value,
            m.unit measurement_unit
        FROM test t
        INNER JOIN test_run tr
            ON t.id = tr.test_id
            AND tr.project_id = $3
        INNER JOIN job j
            ON j.id = tr.job_id
            AND j.name = (SELECT name FROM job WHERE id = $1)
            AND j.project_id = $3
        INNER JOIN build b
            ON b.id = j.build_id
            AND b.project_id = $3
        INNER JOIN collaborator co
            ON co.project_id = $3
            AND co.user_id = $4
        LEFT OUTER JOIN measurement m
            ON tr.id = m.test_run_id
            AND m.project_id = $3
        WHERE t.name = $5
            AND t.suite = $6
            AND t.project_id = $3
        ORDER BY b.build_number, b.restart_counter
        LIMIT 30`,
        [job_id, null, project_id, user_id, test, suite])
        .then((results: any[]) => {
            let current_build = null;
            const result = [];

            for (const r of results) {
                if (current_build && current_build.build_number !== r.build_number) {
                    result.push(current_build);
                    current_build = null;
                }

                if (!current_build) {
                    current_build = {
                        build_number: r.build_number,
                        duration: r.duration,
                        state: r.state,
                        measurements: []
                    };
                }

                if (r.measurement_name) {
                    current_build.measurements.push({
                        name: r.measurement_name,
                        unit: r.measurement_unit,
                        value: r.measurement_value
                    });
                }
            }

            if (current_build) {
                result.push(current_build);
            }
            return result;
        })
        .then((repos: any[]) => {
            res.json(repos);
        }).catch(handleDBError(next));
});
