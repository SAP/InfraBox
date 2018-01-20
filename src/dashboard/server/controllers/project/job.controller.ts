import { Request, Response } from "express";
import { Router } from "express";
import { restart_build } from './restart_build';
import { db, handleDBError } from '../../db';
import { NotFound, BadRequest, OK } from "../../utils/status";
import { deleteCache } from "../../utils/gcs";
import { param_validation as pv } from "../../utils/validation";
import { auth, checkProjectAccess } from "../../utils/auth";

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/:job_id/restart", pv, auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const job_id = req.params['job_id'];

    db.tx((tx) => {
        const build = null;
        return tx.any(`
            SELECT state, type FROM job WHERE id = $1
        `, [job_id])
        .then((jobs: any[]) => {
            if (jobs.length !== 1) {
                throw new NotFound();
            }

            const state = jobs[0].state;
            const typ = jobs[0].type;

            if (typ !== 'run_project_container' && typ !== 'run_docker_compose') {
                throw new BadRequest('Job type cannot be restarted');
            }

            if (state !== 'error' && state !== 'failure' && state !== 'finished' && state !== 'killed') {
                throw new BadRequest(`Job in state '${state}' cannot be restarted`);
            }

            return tx.none(`
                UPDATE job SET state = 'queued' WHERE id = $1
            `, [job_id]);
        });
    })
    .then(() => {
        return OK(res, 'successfully restarted job');
    }).catch(handleDBError(next));
});

router.get("/:job_id/kill", pv, auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const job_id = req.params['job_id'];

    db.any('INSERT INTO abort (job_id) VALUES($1)', [job_id])
    .then(() => {
        return OK(res, "Killed job");
    }).catch(handleDBError(next));
});

router.get("/:build_id/cache/clear", pv, auth, checkProjectAccess, (req: Request, res: Response, next) => {
    const job_id = req.params['build_id'];
    const project_id = req.params['project_id'];

    db.any(`SELECT j.name, branch from job j
        INNER JOIN build b
            ON b.id = j.build_id
            AND j.id = $1
            AND j.project_id = $2
            AND b.project_id = $2
        LEFT OUTER JOIN "commit" c
            ON b.commit_id = c.id
            AND c.project_id = $2`, [job_id, project_id])
        .then((jobs: any[]) => {
            if (jobs.length !== 1) {
                throw new NotFound();
            }

            const j = jobs[0];
            const p = [];
            const key = 'project_' + req.params['project_id'] + '_branch_' + j['branch'] + '_job_' + j['name'] + '.tar.gz';
            return deleteCache(key);
        }).then(() => {
            return OK(res, "Cleared cache");
    }).catch(handleDBError(next));
});
