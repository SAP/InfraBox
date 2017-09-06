"use strict";

import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { param_validation as pv } from "../../utils/validation";
import { OK, BadRequest, NotFound } from "../../utils/status";
import { Validator } from 'jsonschema';
import { deleteHook } from "../../utils/github";

const router = Router({ mergeParams: true });
module.exports = router;

router.delete("/", pv, (req: Request, res: Response, next) => {
    const user_id = req['user'].id;
    const project_id = req.params['project_id'];
    let project_type;

    db.tx((tx) => {
        return tx.one(`
            SELECT COUNT(*) as cnt
               FROM collaborator co
           INNER JOIN project p
               ON p.id = co.project_id
           WHERE co.user_id = $1
               AND co.project_id = $2
               AND co.owner = true`, [user_id, project_id]
        ).then((data: any) => {
            if (data.cnt === 0) {
                throw new NotFound();
            }

            return tx.one(`DELETE FROM project WHERE id = $1 RETURNING ID, type`, [project_id]);
        }).then((data: any) => {
            project_type = data.type;
            if (project_type == "github") {
                let repo_info = null;

                return tx.one(
                    `SELECT name, github_owner, github_hook_id
                     FROM repository
                     WHERE project_id = $1`, [project_id]
                ).then((data: any) => {
                    repo_info = data;
                    return tx.one(`SELECT github_api_token FROM "user"
                        WHERE id = $1`, [user_id]);
                }).then((data: any) => {
                    const d = repo_info;
                    // don't wait for the delete, it may fail
                    deleteHook(data.github_api_token, d.name, d.github_owner, d.github_hook_id);
                });
            }
        }).then(() => {
            if (project_type == "github" || project_type == "gerrit") {
                return tx.any(`DELETE FROM repository WHERE project_id = $1`, [project_id]);
            }
        }).then(() => {
            return tx.any(`DELETE FROM collaborator WHERE project_id = $1`, [project_id]);
        });
    })
    .then(() => {
        return OK(res, 'successfully deleted project');
    })
    .catch(handleDBError(next));
});
