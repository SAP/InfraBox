import { Request, Response } from "express";
import { db, handleDBError } from "../../db";
import { OK, NotFound } from '../../utils/status';

export function restart_build(req: Request, res: Response, next)  {
    let new_build_id = null;
    const user_id = req['user'].id;
    const project_id = req.params['project_id'];
    const build_id = req.params['build_id'];
    let restartCounter = null;

    db.tx((tx) => {
        let build = null;
        return tx.any(`
            SELECT b.*
            FROM build b
            INNER JOIN collaborator co
                ON b.id = $3
                AND b.project_id = co.project_id
                AND co.project_id = $2
                AND co.user_id = $1
        `, [user_id, project_id, build_id])
        .then((builds: any[]) => {
            if (builds.length !== 1) {
                throw new NotFound();
            }

            build = builds[0];
            return tx.one(`
                SELECT max(restart_counter) as restart_counter
                FROM build WHERE build_number = $1 and project_id = $2
            `, [build.build_number, build.project_id]);
        })
        .then((r: any) => {
            restartCounter = r.restart_counter + 1;
            return tx.one(`
                INSERT INTO build (commit_id, build_number,
                          project_id, restart_counter, source_upload_id)
                VALUES ($1, $2, $3, $4, $5) RETURNING ID
            `, [build.commit_id, build.build_number, build.project_id,
                restartCounter, build.source_upload_id]);
        })
        .then((b: any) => {
            new_build_id = b.id;
            return tx.one(`
               SELECT repo, env_var FROM job
               WHERE project_id = $1
               AND name = 'Create Jobs'
               AND build_id = $2
            `, [project_id, build_id]);
        })
        .then((job: any) => {
            return tx.none(`
                INSERT INTO job (id, state, build_id, type,
                           name, cpu, memory, project_id, build_only, dockerfile, repo, env_var, definition)
                VALUES (gen_random_uuid(), 'queued', $1, 'create_job_matrix',
                           'Create Jobs', 1, 1024, $2, false, '', $3, $4, $5);
            `, [new_build_id, build.project_id, job.repo, job.env_var, job.definition]);
        });
    })
    .then(() => {
        return OK(res, 'successfully restarted build', {build: {id: new_build_id, restartCounter: restartCounter}});
    }).catch(handleDBError(next));
}
