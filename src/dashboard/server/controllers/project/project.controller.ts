"use strict";

import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { param_validation as pv } from "../../utils/validation";
import { OK, BadRequest, NotFound } from "../../utils/status";
import { Validator } from 'jsonschema';

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/", pv, (req: Request, res: Response, next) => {
    const user_id = req['user'].id;

    db.any(`SELECT p.id, p.name, p.type FROM project p
            INNER JOIN collaborator co
            ON co.project_id = p.id AND $1 = co.user_id
            ORDER BY p.name`, [user_id]).then((projects: any[]) => {
            res.json(projects);
        }).catch(handleDBError(next));
});

const AddProjectSchema = {
    id: "/EnvVarSchema",
    type: "object",
    properties: {
        name: { type: "string" },
        private: { type: "boolean" },
        type: ["upload", "gerrit"]
    },
    required: ["name", "private", "type"]
};

router.post("/", pv, (req: Request, res: Response, next) => {
    const v = new Validator();
    const envResult = v.validate(req['body'], AddProjectSchema);

    if (envResult.errors.length > 0) {
        return next(new BadRequest("Invalid values"));
    }

    const name = req['body']['name'];
    const typ = req['body']['type'];
    const priv = req['body']['private'] === 'true';

    const user_id = req['user'].id;
    let project_id = null;

    db.tx((tx) => {
        return tx.one(`SELECT COUNT(*) as cnt
                        FROM project p
                        INNER JOIN collaborator co
                        ON p.id = co.project_id
                        AND co.user_id = $1`, [user_id]
            ).then((data: any) => {
                if (data.cnt > 50) {
                    throw new BadRequest("too many projects");
                }

                return tx.one("INSERT INTO project (name, type, public) VALUES ($1, $2, $3) RETURNING id",
                    [name, typ, !priv]);
            })
            .then((result: any) => {
                project_id = result.id;
                return tx.none("INSERT INTO collaborator (user_id, project_id, owner) VALUES ($1, $2, true)",
                    [user_id, project_id]
                );
            });
    })
    .then(() => {
        return OK(res, 'successfully added new project', { project_id: project_id });
    })
    .catch(handleDBError(next));
});

router.delete("/", pv, (req: Request, res: Response, next) => {
    const user_id = req['user'].id;
    const project_id = req.params['project_id'];

    db.tx((tx) => {
        return tx.one(`SELECT COUNT(*) as cnt
                       FROM collaborator co
               INNER JOIN project p
                   ON p.id = co.project_id
                   AND p.type = 'upload'
                       WHERE co.user_id = $1
                   AND co.project_id = $2
                   AND co.owner = true`, [user_id, project_id]
            ).then((data: any) => {
                if (data.cnt === 0) {
                    throw new NotFound();
                }

                return tx.any(`DELETE FROM project WHERE id = $1
                    AND type = 'upload' RETURNING ID`, [project_id]);
            }).then((data: any) => {
                if (data.length === 0) {
                            throw new NotFound();
                }

                return tx.any(`DELETE FROM collaborator WHERE project_id = $1`, [project_id]);
        });
    })
    .then(() => {
        return OK(res, 'successfully deleted project');
    })
    .catch(handleDBError(next));
});
