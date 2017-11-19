"use strict";

import { Request, Response } from "express";
import { Router } from "express";
import { db, handleDBError } from "../../db";
import { param_validation as pv } from "../../utils/validation";

const router = Router({ mergeParams: true });
module.exports = router;

router.get("/", pv, (req: Request, res: Response, next) => {
    const project_id = req.params['project_id'];

    db.one(`SELECT p.id, p.name, p.type FROM project p
            WHERE id = $1`, [project_id]).then((project: any) => {
            res.json(project);
        }).catch(handleDBError(next));
});
