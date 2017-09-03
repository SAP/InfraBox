import { Request, Response } from "express";
import { Router } from "express";
import { restart_build } from './restart_build';
import { db, handleDBError } from '../../db';
import { BadRequest, OK } from "../../utils/status";
import { deleteCache } from "../../utils/gcs";
import { param_validation as pv } from "../../utils/validation";

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/:build_id/restart", pv, (req: Request, res: Response, next) => {
    restart_build(req, res, next);
});

router.get("/:build_id/kill", pv, (req: Request, res: Response, next) => {
    const build_id = req.params['build_id'];
    const project_id = req.params['project_id'];

    db.tx((tx) => {
        return tx.any('SELECT id FROM job WHERE build_id = $1 and project_id = $2', [build_id, project_id])
            .then((jobs: any[]) => {
                const stmts = [];

                for (const j of jobs) {
                    stmts.push(tx.none('INSERT INTO abort (job_id) VALUES($1)', [j.id]));
                }

                return tx.batch(stmts);
            });
    }).then(() => {
        return OK(res, "Killed all jobs");
    }).catch(handleDBError(next));
});

router.get("/:build_id/cache/clear", pv, (req: Request, res: Response, next) => {
    const build_id = req.params['build_id'];
    const project_id = req.params['project_id'];

    db.any(`SELECT j.name, branch from job j
        INNER JOIN build b
            ON b.id = j.build_id
            AND b.id = $1
            AND j.project_id = $2
            AND b.project_id = $2
        LEFT OUTER JOIN "commit" c
            ON b.commit_id = c.id
            AND c.project_id = $2`, [build_id, project_id])
        .then((jobs: any[]) => {
            const p = [];

            for (const j of jobs) {
                const key = 'project_' + req.params['project_id'] + '_branch_' + j['branch'] + '_job_' + j['name'] + '.tar.gz';
                p.push(deleteCache(key));
            }

            return Promise.all(p);
        }).then(() => {
            return OK(res, "Cleared cache");
    }).catch(handleDBError(next));
});
